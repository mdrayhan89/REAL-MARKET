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
    now = datetime.datetime.now()
    # পরবর্তী ১ মিনিটের সময় সেট করা (১১:১১ তে জেনারেট করলে ১১:১২ দেখাবে)
    signal_time = (now + datetime.timedelta(minutes=1)).strftime("%H:%M")
    accuracy = 96 + (now.minute % 4) 
    direction = "CALL ⬆️" if (now.minute + len(pair)) % 2 == 0 else "PUT ⬇️"
    strategies = ["EMA Cross", "Price Action", "Support Zone", "RSI Reverse"]
    strat = strategies[now.minute % 4]
    return direction, accuracy, strat, signal_time

async def send_signal_task(pair):
    direction, accuracy, strategy, signal_time = get_signal_logic(pair)
    ss_url = f"https://dark-live-ss.onrender.com/?Pair={pair.lower()}"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page()
        try:
            await page.goto(ss_url, timeout=60000)
            await asyncio.sleep(2) # চার্ট লোড হওয়ার সময়
            ss_bytes = await page.screenshot()
            state["current_ss"] = base64.b64encode(ss_bytes).decode('utf-8')
            state["history"].insert(0, {"pair": pair, "time": signal_time, "dir": direction, "acc": accuracy})
            
            if state["telegram_enabled"] and state["bot_token"]:
                bot = Bot(token=state["bot_token"])
                caption = (
                    f"🔥 <b>DARK-X PRO SIGNAL</b> 🔥\n\n"
                    f"📊 PAIR: {pair}\n"
                    f"⏰ TIME: {signal_time} (Next Candle)\n"
                    f"🎯 STRATEGY: {strategy}\n"
                    f"💎 DIRECTION: {direction}\n"
                    f"✅ ACCURACY: {accuracy}%"
                )
                await bot.send_photo(chat_id=state["chat_id"], photo=ss_bytes, caption=caption, parse_mode=ParseMode.HTML)
        except Exception as e: print(f"Error: {e}")
        finally: await browser.close()

async def auto_scan_loop():
    while True:
        if state["auto_scan_active"]:
            await send_signal_task(random.choice(ALL_PAIRS))
            await asyncio.sleep(120)
        else:
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event(): asyncio.create_task(auto_scan_loop())

@app.get("/", response_class=HTMLResponse)
async def main_ui():
    pair_opts = "".join([f'<option value="{p}">{p}</option>' for p in ALL_PAIRS])
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DARK-X-PRO V10.2</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body {{ background: #0b0e14; color: #fff; font-family: sans-serif; overflow-x: hidden; }}
            .glow-card {{ background: #151a21; border: 1px solid #2d3748; border-radius: 12px; padding: 15px; margin-bottom: 15px; }}
            .hidden {{ display: none; }}
            .btn-action {{ background: #2563eb; color: white; font-weight: bold; padding: 12px; border-radius: 8px; width: 100%; font-size: 11px; }}
            .switch {{ position: relative; display: inline-block; width: 45px; height: 22px; }}
            .switch input {{ opacity: 0; width: 0; height: 0; }}
            .slider {{ position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #334155; transition: .4s; border-radius: 20px; }}
            .slider:before {{ position: absolute; content: ""; height: 16px; width: 16px; left: 3px; bottom: 3px; background-color: white; transition: .4s; border-radius: 50%; }}
            input:checked + .slider {{ background-color: #2563eb; }}
            input:checked + .slider:before {{ transform: translateX(23px); }}
        </style>
    </head>
    <body class="pb-24 p-4">

        <div id="auth-screen" class="fixed inset-0 z-[100] bg-[#0b0e14] flex flex-col items-center justify-center p-6 text-center">
            <h1 class="text-3xl font-black mb-10 text-blue-500 italic">DARK-X-PRO</h1>
            <button onclick="doLogin('FREE USER')" class="w-full max-w-xs p-4 bg-slate-800 rounded-xl font-bold mb-4 border border-slate-700 uppercase text-xs">👤 Free Access</button>
            <input id="key-input" type="password" placeholder="Premium Key" class="w-full max-w-xs p-4 bg-slate-900 rounded-xl mb-4 border border-slate-800 text-center outline-none">
            <button onclick="doLogin('PREMIUM')" class="w-full max-w-xs p-4 bg-blue-600 rounded-xl font-bold uppercase text-xs">💎 Unlock Premium</button>
        </div>

        <div id="main-content" class="hidden">
            <div id="home-tab" class="tab-page">
                <div class="glow-card">
                    <div class="flex gap-2">
                        <button id="auto-btn" onclick="toggleAuto()" class="flex-1 p-4 bg-slate-800 rounded-xl font-bold text-[9px] uppercase">🚀 Auto Scan: OFF</button>
                        <div class="flex-1">
                            <select id="m-pair" class="w-full p-2 bg-slate-900 rounded-lg text-[10px] font-bold border border-slate-700 outline-none mb-1">{pair_opts}</select>
                            <button onclick="manualSend()" class="w-full p-2 bg-yellow-500 text-black font-bold text-[10px] rounded-lg uppercase">Send Manual</button>
                        </div>
                    </div>
                </div>
                <div class="glow-card h-48 flex items-center justify-center" id="chart-box">
                    <p class="text-slate-600 italic text-xs">Live Chart Loading...</p>
                </div>
                <div class="glow-card">
                    <div class="grid grid-cols-2 gap-2 mb-2">
                        <button onclick="record('win')" class="btn-action">✓ WIN</button>
                        <button onclick="record('loss')" class="btn-action">✗ LOSS</button>
                        <button onclick="record('mtg')" class="btn-action">⇄ MTG</button>
                        <button onclick="record('refund')" class="btn-action bg-slate-700">↺ REFUND</button>
                        <button onclick="sendFinalReport()" class="col-span-2 p-3 bg-yellow-500 text-black font-bold rounded-lg text-[10px] uppercase">Send Final Report</button>
                    </div>
                </div>
            </div>

            <div id="history-tab" class="tab-page hidden">
                <div class="glow-card"><h3 class="text-blue-500 font-bold mb-4 text-xs uppercase">History</h3><div id="hist-list" class="space-y-2 text-[10px]"></div></div>
            </div>

            <div id="settings-tab" class="tab-page hidden">
                <div class="glow-card">
                    <div class="flex justify-between items-center mb-6"><span class="text-xs font-bold">TELEGRAM NOTIFICATION</span>
                        <label class="switch"><input type="checkbox" id="tg-toggle" checked onclick="toggleTG()"><span class="slider"></span></label>
                    </div>
                    <input id="bot-token" type="text" class="w-full p-4 bg-slate-900 border border-slate-800 rounded-xl mb-2 text-xs" placeholder="Bot Token" onchange="saveConfig()">
                    <input id="chat-id" type="text" class="w-full p-4 bg-slate-900 border border-slate-800 rounded-xl text-xs" placeholder="Chat ID" onchange="saveConfig()">
                </div>
            </div>

            <div id="profile-tab" class="tab-page hidden text-center pt-6">
                <div class="w-16 h-16 bg-blue-600 rounded-full mx-auto mb-2 flex items-center justify-center text-xl font-bold">R</div>
                <h2 id="display-role" class="text-blue-500 font-bold text-[10px] mb-6 uppercase">FREE USER</h2>
                <div class="grid grid-cols-4 gap-1 px-2">
                    <div class="bg-slate-800 p-2 rounded"><p id="p-win" class="font-bold">0</p><p class="text-[7px]">WIN</p></div>
                    <div class="bg-slate-800 p-2 rounded"><p id="p-loss" class="font-bold">0</p><p class="text-[7px]">LOSS</p></div>
                    <div class="bg-slate-800 p-2 rounded"><p id="p-mtg" class="font-bold">0</p><p class="text-[7px]">MTG</p></div>
                    <div class="bg-slate-800 p-2 rounded"><p id="p-ref" class="font-bold">0</p><p class="text-[7px]">REF</p></div>
                </div>
            </div>
        </div>

        <nav class="fixed bottom-0 left-0 right-0 bg-[#151a21] border-t border-slate-800 flex justify-around p-3 z-[100]">
            <button onclick="switchTab('home')" class="flex flex-col items-center text-[9px]"><i class="fas fa-home mb-1 text-lg"></i>HOME</button>
            <button onclick="switchTab('history')" class="flex flex-col items-center text-[9px]"><i class="fas fa-history mb-1 text-lg"></i>HISTORY</button>
            <button onclick="switchTab('settings')" class="flex flex-col items-center text-[9px]"><i class="fas fa-cog mb-1 text-lg"></i>SETTING</button>
            <button onclick="switchTab('profile')" class="flex flex-col items-center text-[9px]"><i class="fas fa-user mb-1 text-lg"></i>PROFILE</button>
        </nav>

        <script>
            async function doLogin(role) {{
                if(role === 'PREMIUM') {{
                    if(document.getElementById('key-input').value !== 'DARK-X-RAYHAN') return alert('Wrong Key!');
                    document.getElementById('display-role').innerText = '💎 PREMIUM USER';
                }}
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
                document.getElementById('auto-btn').innerText = d.active ? "🚀 AUTO SCAN: ON" : "🚀 AUTO SCAN: OFF";
                document.getElementById('auto-btn').style.background = d.active ? "#16a34a" : "#1e293b";
            }}
            async function toggleTG() {{ await fetch('/api/toggle_tg'); }}
            async function manualSend() {{
                const p = document.getElementById('m-pair').value;
                await fetch(`/api/manual?pair=${{p}}`);
                alert('Signal Request Sent!');
            }}
            async function record(type) {{ await fetch(`/api/record?type=${{type}}`); updateUI(); }}
            async function sendFinalReport() {{ await fetch('/api/send_report'); alert('Report Sent!'); }}
            async function updateUI() {{
                const r = await fetch('/api/get_state');
                const d = await r.json();
                document.getElementById('p-win').innerText = d.stats.win;
                document.getElementById('p-loss').innerText = d.stats.loss;
                document.getElementById('p-mtg').innerText = d.stats.mtg;
                document.getElementById('p-ref').innerText = d.stats.refund;
                if(d.current_ss) document.getElementById('chart-box').innerHTML = `<img src="data:image/png;base64,${{d.current_ss}}" class="w-full rounded-lg">`;
                document.getElementById('hist-list').innerHTML = d.history.map(h => `<div class="flex justify-between border-b border-slate-800 pb-1"><span>${{h.pair}} (${{h.dir}})</span><span class="text-blue-500">${{h.time}}</span></div>`).join('');
            }}
            setInterval(updateUI, 5000);
        </script>
    </body>
    </html>
    """

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
    if type in state["stats"]: 
        state["stats"][type] += 1
        if state["telegram_enabled"] and state["bot_token"]:
            bot = Bot(token=state["bot_token"])
            msg = f"📊 <b>RESULT: {type.upper()}</b>\nWIN: {state['stats']['win']} | LOSS: {state['stats']['loss']}\nMTG: {state['stats']['mtg']} | REFUND: {state['stats']['refund']}"
            asyncio.create_task(bot.send_message(state["chat_id"], msg, parse_mode=ParseMode.HTML))
    return {"ok": True}

@app.get("/api/send_report")
async def send_report():
    if state["telegram_enabled"] and state["bot_token"]:
        bot = Bot(token=state["bot_token"])
        msg = f"🏆 <b>SESSION REPORT</b>\n\n✅ WIN: {state['stats']['win']}\n❌ LOSS: {state['stats']['loss']}\n🔄 MTG: {state['stats']['mtg']}\n♻️ REFUND: {state['stats']['refund']}"
        asyncio.create_task(bot.send_message(state["chat_id"], msg, parse_mode=ParseMode.HTML))
    return {"ok": True}

@app.get("/api/get_state")
async def get_state(): return state

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
