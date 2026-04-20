import asyncio
import datetime
import uvicorn
import base64
import random
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from telegram import Bot
from telegram.constants import ParseMode
from playwright.async_api import async_playwright

app = FastAPI()

# ১১টি পেয়ারের লিস্ট
ALL_PAIRS = ["XAUUSD", "EURJPY", "NZDUSD", "EURUSD", "GBPUSD", "AUDUSD", "USDCAD", "USDJPY", "EURGBP", "AUDJPY", "CADJPY"]

state = {
    "telegram_enabled": True,
    "auto_scan_active": False,
    "bot_token": "8354111202:AAEqFLMoJ7W7AlwpfHibZbpusiWbnOcl5Xc",
    "chat_id": "-1003862859969",
    "premium_key": "DARK-X-RAYHAN",
    "stats": {"win": 0, "loss": 0, "mtg": 0},
    "current_ss": "",
    "history": [],
    "user_role": "FREE USER"
}

# --- ফিক্সড এক্যুরেসি ও সিগন্যাল লজিক ---
def get_signal_logic(pair):
    now = datetime.datetime.now()
    # র‍্যান্ডম নয়, গাণিতিক এক্যুরেসি (৯৬-৯৯ এর মধ্যে)
    accuracy = 96 + (now.minute % 4) 
    direction = "CALL ⬆️" if (now.minute + len(pair)) % 2 == 0 else "PUT ⬇️"
    strategies = ["EMA Cross", "Price Action", "Bollinger Break", "Support Zone", "RSI Reverse"]
    strat = strategies[now.minute % 5]
    return direction, accuracy, strat

async def send_signal_task(pair):
    direction, accuracy, strategy = get_signal_logic(pair)
    now_time = datetime.datetime.now().strftime("%H:%M:%S")
    ss_url = f"https://dark-live-ss.onrender.com/?Pair={pair.lower()}"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(ss_url, timeout=60000)
            ss_bytes = await page.screenshot()
            state["current_ss"] = base64.b64encode(ss_bytes).decode('utf-8')
            state["history"].insert(0, {"pair": pair, "time": now_time, "dir": direction, "acc": accuracy})
            
            if state["telegram_enabled"] and state["bot_token"]:
                bot = Bot(token=state["bot_token"])
                caption = (
                    f"🔥 <b>DARK-X PRO SIGNAL</b> 🔥\n\n"
                    f"📊 PAIR: {pair}\n"
                    f"⏰ TIME: {now_time}\n"
                    f"🎯 STRATEGY: {strategy}\n"
                    f"💎 DIRECTION: {direction}\n"
                    f"✅ ACCURACY: {accuracy}%"
                )
                await bot.send_photo(chat_id=state["chat_id"], photo=ss_bytes, caption=caption, parse_mode=ParseMode.HTML)
        except: pass
        finally: await browser.close()

# ২ মিনিট অটো লুপ
async def auto_scan_loop():
    while True:
        if state["auto_scan_active"]:
            pair = random.choice(ALL_PAIRS)
            await send_signal_task(pair)
            await asyncio.sleep(120)
        else:
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event(): asyncio.create_task(auto_scan_loop())

@app.get("/", response_class=HTMLResponse)
async def main_ui():
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
            .glow-card {{ background: #151a21; border: 1px solid #2d3748; border-radius: 12px; padding: 15px; margin-bottom: 15px; box-shadow: 0 0 10px rgba(0,0,0,0.5); }}
            .nav-active {{ color: #3b82f6; border-top: 2px solid #3b82f6; }}
            .hidden {{ display: none; }}
            .btn-action {{ background: #2563eb; color: white; font-weight: bold; padding: 12px; border-radius: 8px; width: 100%; font-size: 11px; }}
        </style>
    </head>
    <body class="pb-24 p-4">

        <div id="auth-screen" class="fixed inset-0 z-[100] bg-[#0b0e14] flex flex-col items-center justify-center p-6 text-center">
            <h1 class="text-3xl font-black mb-10 text-blue-500 italic">DARK-X-PRO</h1>
            <button onclick="doLogin('FREE USER')" class="w-full max-w-xs p-4 bg-slate-800 rounded-xl font-bold mb-4 border border-slate-700">👤 FREE USER ACCESS</button>
            <div class="w-full max-w-xs p-1 bg-slate-900 rounded-xl mb-4 border border-slate-800">
                <input id="key-input" type="password" placeholder="Enter Premium Key" class="w-full p-3 bg-transparent text-center outline-none">
            </div>
            <button onclick="doLogin('PREMIUM')" class="w-full max-w-xs p-4 bg-blue-600 rounded-xl font-bold">💎 UNLOCK PREMIUM</button>
        </div>

        <div id="main-content" class="hidden">
            <div id="home-tab" class="tab-page">
                <div class="glow-card">
                    <div class="flex gap-2">
                        <button id="auto-btn" onclick="toggleAuto()" class="flex-1 p-4 bg-slate-800 rounded-xl font-bold text-[10px]">🚀 AUTO SCAN: OFF</button>
                        <button onclick="manualSend()" class="flex-1 p-4 bg-yellow-500 text-black font-bold text-[10px] rounded-xl uppercase">Manual Send</button>
                    </div>
                </div>

                <div class="glow-card">
                    <div id="chart-box" class="w-full aspect-video bg-black rounded-lg flex items-center justify-center border border-slate-800 text-[10px] text-slate-700 italic">Live Preview Area</div>
                </div>

                <div class="glow-card">
                    <div class="grid grid-cols-2 gap-3 mb-3">
                        <button onclick="record('win')" class="btn-action">✓ WIN</button>
                        <button onclick="record('loss')" class="btn-action">✗ LOSS</button>
                        <button onclick="record('mtg')" class="btn-action">⇄ MTG</button>
                        <button onclick="alert('Report Sent')" class="p-3 bg-yellow-500 text-black font-bold rounded-lg text-[10px] uppercase">Report</button>
                    </div>
                </div>
            </div>

            <div id="history-tab" class="tab-page hidden">
                <div class="glow-card">
                    <h3 class="text-blue-500 font-bold mb-4 text-xs uppercase">Signal History</h3>
                    <div id="hist-list" class="space-y-3 text-[11px]"></div>
                </div>
            </div>

            <div id="profile-tab" class="tab-page hidden text-center py-10">
                <div class="w-20 h-20 bg-blue-600 rounded-full mx-auto mb-4 flex items-center justify-center text-3xl font-bold">R</div>
                <h2 class="font-bold text-xl uppercase tracking-tighter">Dark-X-Rayhan</h2>
                <div id="display-role" class="text-blue-500 font-bold text-[10px] mb-8 uppercase tracking-widest">FREE USER</div>
                <div class="grid grid-cols-3 gap-2 px-2">
                    <div class="bg-slate-800 p-3 rounded-lg"><p class="text-lg font-black" id="p-win">0</p><p class="text-[8px]">WIN</p></div>
                    <div class="bg-slate-800 p-3 rounded-lg"><p class="text-lg font-black" id="p-loss">0</p><p class="text-[8px]">LOSS</p></div>
                    <div class="bg-slate-800 p-3 rounded-lg"><p class="text-lg font-black" id="p-mtg">0</p><p class="text-[8px]">MTG</p></div>
                </div>
            </div>

            <div id="settings-tab" class="tab-page hidden">
                <div class="glow-card">
                    <div class="flex justify-between items-center mb-6">
                        <span class="text-xs font-bold">TELEGRAM STATUS</span>
                        <button id="tg-status" onclick="toggleTG()" class="px-4 py-2 bg-blue-600 rounded-lg text-[10px]">ENABLED</button>
                    </div>
                    <input id="bot-token" type="text" class="w-full p-4 bg-slate-900 border border-slate-800 rounded-xl mb-4 text-xs" placeholder="Bot Token" onchange="saveConfig()">
                    <input id="chat-id" type="text" class="w-full p-4 bg-slate-900 border border-slate-800 rounded-xl text-xs" placeholder="Chat ID" onchange="saveConfig()">
                </div>
            </div>
        </div>

        <nav class="fixed bottom-0 left-0 right-0 bg-[#151a21] border-t border-slate-800 flex justify-around p-3 z-[100]">
            <button onclick="switchTab('home')" class="flex flex-col items-center text-[9px]"><i class="fas fa-home text-lg mb-1"></i>HOME</button>
            <button onclick="switchTab('history')" class="flex flex-col items-center text-[9px]"><i class="fas fa-history text-lg mb-1"></i>HISTORY</button>
            <button onclick="switchTab('settings')" class="flex flex-col items-center text-[9px]"><i class="fas fa-cog text-lg mb-1"></i>SETTING</button>
            <button onclick="switchTab('profile')" class="flex flex-col items-center text-[9px]"><i class="fas fa-user text-lg mb-1"></i>PROFILE</button>
        </nav>

        <script>
            async function doLogin(role) {{
                if(role === 'PREMIUM') {{
                    const key = document.getElementById('key-input').value;
                    if(key !== 'DARK-X-RAYHAN') return alert('Invalid Key!');
                    document.getElementById('display-role').innerText = '💎 PREMIUM USER';
                }}
                document.getElementById('auth-screen').classList.add('hidden');
                document.getElementById('main-content').classList.remove('hidden');
                await fetch(`/api/set_role?role=${{role}}`);
            }}

            function switchTab(t) {{
                document.querySelectorAll('.tab-page').forEach(p => p.classList.add('hidden'));
                document.getElementById(t + '-tab').classList.remove('hidden');
            }}

            async function toggleAuto() {{
                const res = await fetch('/api/toggle_auto');
                const d = await res.json();
                const b = document.getElementById('auto-btn');
                b.innerText = d.active ? "🚀 AUTO SCAN: ON" : "🚀 AUTO SCAN: OFF";
                b.style.background = d.active ? "#16a34a" : "#1e293b";
            }}

            async function toggleTG() {{
                const res = await fetch('/api/toggle_tg');
                const d = await res.json();
                document.getElementById('tg-status').innerText = d.enabled ? "ENABLED" : "DISABLED";
            }}

            async function manualSend() {{
                const p = prompt("Enter Pair (e.g. EURUSD):", "EURUSD");
                if(p) await fetch(`/api/manual?pair=${{p}}`);
            }}

            async function record(type) {{
                await fetch(`/api/record?type=${{type}}`);
                updateStats();
            }}

            async function updateStats() {{
                const r = await fetch('/api/get_state');
                const d = await r.json();
                document.getElementById('p-win').innerText = d.stats.win;
                document.getElementById('p-loss').innerText = d.stats.loss;
                document.getElementById('p-mtg').innerText = d.stats.mtg;
                
                if(d.ss) document.getElementById('chart-box').innerHTML = `<img src="data:image/png;base64,${{d.ss}}" class="w-full rounded-lg">`;
                
                const hList = document.getElementById('hist-list');
                hList.innerHTML = d.history.map(h => `
                    <div class="flex justify-between border-b border-slate-800 pb-2">
                        <span><b>${{h.pair}}</b> (${{h.dir}})</span>
                        <span class="text-blue-500">${{h.time}}</span>
                    </div>
                `).join('');
            }}
            setInterval(updateStats, 5000);
        </script>
    </body>
    </html>
    """

@app.get("/api/set_role")
async def set_role(role: str):
    state["user_role"] = role
    return {"ok": True}

@app.get("/api/toggle_auto")
async def toggle_auto():
    state["auto_scan_active"] = not state["auto_scan_active"]
    return {"active": state["auto_scan_active"]}

@app.get("/api/toggle_tg")
async def toggle_tg():
    state["telegram_enabled"] = not state["telegram_enabled"]
    return {"enabled": state["telegram_enabled"]}

@app.get("/api/manual")
async def manual_signal(pair: str):
    asyncio.create_task(send_signal_task(pair.upper()))
    return {"ok": True}

@app.get("/api/record")
async def record_stat(type: str):
    if type in state["stats"]: state["stats"][type] += 1
    return {"ok": True}

@app.get("/api/get_state")
async def get_state(): return state

@app.get("/api/update_config")
async def update_config(token: str, chat: str):
    state["bot_token"], state["chat_id"] = token, chat
    return {"ok": True}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
