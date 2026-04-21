import asyncio
import datetime
import uvicorn
import base64
import random
import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from telegram import Bot
from telegram.constants import ParseMode
from playwright.async_api import async_playwright

app = FastAPI()

ALL_PAIRS = ["XAUUSD", "EURJPY", "NZDUSD", "EURUSD", "GBPUSD", "AUDUSD", "USDCAD", "USDJPY", "EURGBP", "AUDJPY", "CADJPY"]

state = {
    "telegram_enabled": True,
    "auto_scan_active": False,
    "bot_token": "8354111202:AAEqFLMoJ7W7AlwpfHibZbpusiWbnOcl5Xc",
    "chat_id": "-1003862859969",
    "premium_key": "DARK-X-RAYHAN",
    "stats": {"win": 0, "loss": 0, "mtg": 0, "refund": 0},
    "current_ss": "",
    "history": [],
    "user_role": "FREE USER"
}

def get_signal_logic(pair):
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=6)
    signal_time = (now + datetime.timedelta(minutes=1)).strftime("%H:%M")
    # No Randomness: Fixed logic based on pair and minute
    direction = "PUT" if (now.minute + len(pair)) % 2 == 0 else "CALL"
    accuracy = "99%"
    return direction, accuracy, signal_time

async def send_signal_task(pair):
    direction, accuracy, signal_time = get_signal_logic(pair)
    ss_url = f"https://dark-live-ss.onrender.com/?Pair={pair.lower()}"
    
    state["history"].insert(0, {"pair": pair, "time": signal_time, "dir": direction, "acc": accuracy})
    
    async with async_playwright() as p:
        browser = None
        try:
            # Stable Browser Launch for Render/Linux
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'])
            context = await browser.new_context(viewport={'width': 1000, 'height': 600})
            page = await context.new_page()
            
            # টাইমআউট ৯০০০০ (৯০ সেকেন্ড) করা হয়েছে যাতে স্লো নেটেও চার্ট আসে
            await page.goto(ss_url, timeout=90000, wait_until="networkidle")
            await asyncio.sleep(12) # ওয়েট টাইম বাড়ানো হয়েছে স্ক্রিনশট ক্লিয়ার আসার জন্য
            
            ss_bytes = await page.screenshot(type='png')
            state["current_ss"] = base64.b64encode(ss_bytes).decode('utf-8')
            
            if state["telegram_enabled"] and state["bot_token"]:
                bot = Bot(token=state["bot_token"])
                caption = (
                    f"╔═━━━━━ ◥◣◆◢◤ ━━━━━═╗\n"
                    f"              PAIR         ➜ {pair}\n"
                    f"              TIME         ➜ {signal_time}\n"
                    f"              EXPIRE     ➜  M1\n"
                    f"              DIRECTION ➜ {direction}\n"
                    f"              PRICE        ➜ $N/A\n"
                    f"╚═━━━━━ ◢◤◆◥◣ ━━━━━═╝\n\n"
                    f" CONTRACT HERE : @mdrayhan85\n"
                    f" SIGNAL SEND SUCCESSFULLY"
                )
                # ২০ সেকেন্ডের মধ্যে টেলিগ্রামে না পাঠাতে পারলে স্কিপ করবে যাতে সিস্টেম হ্যাং না হয়
                await asyncio.wait_for(bot.send_photo(chat_id=state["chat_id"], photo=ss_bytes, caption=caption, parse_mode=ParseMode.HTML), timeout=20)
        except Exception as e:
            print(f"Signal Process Error: {e}")
        finally:
            if browser: await browser.close()

async def auto_scan_loop():
    while True:
        if state["auto_scan_active"]:
            pair = random.choice(ALL_PAIRS)
            await send_signal_task(pair)
            await asyncio.sleep(120)
        await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(auto_scan_loop())

@app.get("/", response_class=HTMLResponse)
async def main_ui():
    pair_options = "".join([f'<option value="{p}">{p}</option>' for p in ALL_PAIRS])
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DARK-X-PRO V10</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body {{ background: #0b0e14; color: #fff; font-family: sans-serif; }}
            .glow-card {{ background: #151a21; border: 1px solid #2d3748; border-radius: 12px; padding: 15px; margin-bottom: 15px; }}
            .btn-action {{ background: #2563eb; color: white; font-weight: bold; padding: 12px; border-radius: 8px; width: 100%; font-size: 11px; }}
            .hidden {{ display: none; }}
        </style>
    </head>
    <body class="pb-24 p-4">
        <div id="auth-screen" class="fixed inset-0 z-[100] bg-[#0b0e14] flex flex-col items-center justify-center p-6 text-center">
            <h1 class="text-3xl font-black mb-10 text-blue-500 italic">DARK-X-PRO</h1>
            <button onclick="doLogin('FREE USER')" class="w-full max-w-xs p-4 bg-slate-800 rounded-xl font-bold mb-4">👤 FREE USER</button>
            <button onclick="doLogin('PREMIUM')" class="w-full max-w-xs p-4 bg-blue-600 rounded-xl font-bold">💎 PREMIUM</button>
        </div>

        <div id="main-content" class="hidden">
            <div id="home-tab" class="tab-page">
                <div class="glow-card">
                    <div class="flex gap-2 mb-2">
                        <button id="auto-btn" onclick="toggleAuto()" class="flex-1 p-4 bg-slate-800 rounded-xl font-bold text-[10px] uppercase">🚀 AUTO: OFF</button>
                        <select id="pair-select" class="flex-1 p-4 bg-slate-900 rounded-xl font-bold text-[10px] border border-slate-700 outline-none uppercase">{pair_options}</select>
                    </div>
                    <button id="gen-btn" onclick="manualGenerate()" class="w-full p-4 bg-yellow-500 text-black font-bold text-[12px] rounded-xl uppercase">Generate Signal</button>
                </div>
                <div class="glow-card">
                    <div id="chart-box" class="w-full aspect-video bg-black rounded-lg flex items-center justify-center border border-slate-800 text-[10px] text-slate-700 italic">Live Preview Area</div>
                </div>
                <div class="glow-card grid grid-cols-2 gap-3 mb-3">
                    <button onclick="record('win')" class="btn-action">✓ WIN</button>
                    <button onclick="record('loss')" class="btn-action">✗ LOSS</button>
                </div>
            </div>
            <div id="settings-tab" class="tab-page hidden">
                <div class="glow-card">
                    <h3 class="mb-4">Telegram Config</h3>
                    <input id="bot-token" type="text" class="w-full p-4 bg-slate-900 border border-slate-800 rounded-xl mb-4 text-xs" value="{state['bot_token']}">
                    <input id="chat-id" type="text" class="w-full p-4 bg-slate-900 border border-slate-800 rounded-xl text-xs" value="{state['chat_id']}">
                </div>
            </div>
        </div>

        <nav class="fixed bottom-0 left-0 right-0 bg-[#151a21] border-t border-slate-800 flex justify-around p-3 z-[100]">
            <button onclick="switchTab('home')" class="flex flex-col items-center text-[9px] uppercase"><i class="fas fa-home text-lg"></i>HOME</button>
            <button onclick="switchTab('settings')" class="flex flex-col items-center text-[9px] uppercase"><i class="fas fa-cog text-lg"></i>SETTING</button>
        </nav>

        <script>
            async function doLogin(role) {{
                document.getElementById('auth-screen').classList.add('hidden');
                document.getElementById('main-content').classList.remove('hidden');
            }}
            function switchTab(t) {{
                document.querySelectorAll('.tab-page').forEach(p => p.classList.add('hidden'));
                document.getElementById(t + '-tab').classList.remove('hidden');
            }}
            async function toggleAuto() {{
                const res = await fetch('/api/toggle_auto');
                const d = await res.json();
                const b = document.getElementById('auto-btn');
                const genBtn = document.getElementById('gen-btn');
                
                if(d.active) {{
                    b.innerText = "🚀 AUTO: ON";
                    b.style.background = "#16a34a";
                    genBtn.innerText = "AUTO STARTING...";
                    genBtn.disabled = true;
                    genBtn.style.background = "#334155";
                }} else {{
                    b.innerText = "🚀 AUTO: OFF";
                    b.style.background = "#1e293b";
                    genBtn.innerText = "Generate Signal";
                    genBtn.disabled = false;
                    genBtn.style.background = "#eab308";
                }}
            }}
            async function manualGenerate() {{
                const p = document.getElementById('pair-select').value;
                document.getElementById('gen-btn').innerText = "GENERATING...";
                await fetch(`/api/manual?pair=${{p}}`);
            }}
            async function updateStats() {{
                const r = await fetch('/api/get_state');
                const d = await r.json();
                if(d.current_ss) document.getElementById('chart-box').innerHTML = `<img src="data:image/png;base64,${{d.current_ss}}" class="w-full rounded-lg">`;
            }}
            setInterval(updateStats, 5000);
        </script>
    </body>
    </html>
    """

@app.get("/api/toggle_auto")
async def toggle_auto():
    state["auto_scan_active"] = not state["auto_scan_active"]
    return {"active": state["auto_scan_active"]}

@app.get("/api/manual")
async def manual_signal(pair: str):
    asyncio.create_task(send_signal_task(pair.upper()))
    return {"ok": True}

@app.get("/api/get_state")
async def get_state(): return state

@app.get("/api/record")
async def record_stat(type: str):
    if type in state["stats"]: state["stats"][type] += 1
    return {"ok": True}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
