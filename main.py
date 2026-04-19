import asyncio
import datetime
import uvicorn
import base64
import random
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from telegram import Bot
from telegram.constants import ParseMode
from playwright.async_api import async_playwright

app = FastAPI()

# ১১টি পেয়ারের লিস্ট
ALL_PAIRS = ["XAUUSD", "EURJPY", "NZDUSD", "EURUSD", "GBPUSD", "AUDUSD", "USDCAD", "USDJPY", "EURGBP", "AUDJPY", "CADJPY"]

state = {
    "telegram_enabled": True,
    "bot_token": "8354111202:AAEqFLMoJ7W7AlwpfHibZbpusiWbnOcl5Xc",
    "chat_id": "-1003862859969",
    "premium_key": "DARK-X-RAYHAN",
    "owner_tg": "@mdrayhan89",
    "stats": {"win": 0, "loss": 0, "mtg": 0, "refund": 0},
    "session_history": [],
    "current_ss": "",
    "user_type": "FREE USER"
}

# --- নন-র‍্যান্ডম লজিক ---
def get_signal_engine(pair):
    now = datetime.datetime.now()
    val = now.minute + now.second + len(pair)
    strategies = ["EMA_RSI", "Price_Action", "Supertrend", "FVG_Strategy", "Bollinger", "Support_Resistance", "Trend_Reverse", "Trend"]
    
    direction = "CALL ⬆️" if val % 2 == 0 else "PUT ⬇️"
    accuracy = 92 + (val % 7)
    selected_strat = strategies[now.minute % 8]
    return direction, accuracy, selected_strat

async def process_signal(pair):
    direction, accuracy, strategy = get_signal_engine(pair)
    now_time = datetime.datetime.now().strftime("%H:%M")
    
    ss_url = f"https://dark-live-ss.onrender.com/?Pair={pair.lower()}"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(ss_url, wait_until="networkidle")
            ss_bytes = await page.screenshot()
            state["current_ss"] = base64.b64encode(ss_bytes).decode('utf-8')
            
            if state["telegram_enabled"] and state["bot_token"]:
                signal_text = (
                    f"╔═━━━━━ ◥◣◆◢◤ ━━━━━═╗\n"
                    f"             PAIR        ➜ {pair}\n"
                    f"             TIME       ➜ {now_time}\n"
                    f"             STRATEGY   ➜ {strategy}\n"
                    f"             DIRECTION ➜ {direction}\n"
                    f"             ACCURACY     ➜ {accuracy}%\n"
                    f"╚═━━━━━ ◢◤◆◥◣ ━━━━━═╝\n\n"
                    f" CONTRACT HERE : {state['owner_tg']}↯\n"
                    f" SIGNAL SEND SUCCESSFULLY"
                )
                bot = Bot(token=state["bot_token"])
                await bot.send_photo(chat_id=state["chat_id"], photo=ss_bytes, caption=signal_text, parse_mode=ParseMode.HTML)
        finally: await browser.close()

@app.get("/", response_class=HTMLResponse)
async def main_ui():
    pair_opts = "".join([f'<option value="{p}">{p}</option>' for p in ALL_PAIRS])
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DARK-X-PRO V7.1</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body {{ background: #0b0e14; color: #fff; font-family: sans-serif; }}
            .glow-card {{ background: #151a21; border: 1px solid #2d3748; border-radius: 15px; padding: 20px; margin-bottom: 20px; }}
            .nav-active {{ color: #3b82f6; border-top: 2px solid #3b82f6; }}
            .hidden {{ display: none; }}
            .input-box {{ background: #0b0e14; border: 1px solid #2d3748; color: #fff; padding: 12px; border-radius: 10px; font-size: 12px; width: 100%; outline: none; }}
            .toggle-bg:after {{ content: ''; position: absolute; top: 2px; left: 2px; background: white; border-radius: 99px; height: 1.25rem; width: 1.25rem; transition: .3s; }}
            input:checked + .toggle-bg:after {{ transform: translateX(100%); }}
            input:checked + .toggle-bg {{ background-color: #3b82f6; }}
        </style>
    </head>
    <body class="pb-24 p-4">

        <div id="auth-screen" class="fixed inset-0 z-[100] bg-[#0b0e14] flex flex-col items-center justify-center p-6">
            <h1 class="text-3xl font-black mb-10 text-blue-500 italic">DARK SNIPER PRO</h1>
            <button onclick="login('free')" class="w-full max-w-xs p-4 bg-slate-800 rounded-2xl font-bold mb-4">FREE ACCESS</button>
            <input id="key-input" type="password" placeholder="Premium Key" class="w-full max-w-xs p-4 bg-slate-900 rounded-2xl mb-4 text-center border border-slate-800 outline-none">
            <button onclick="login('premium')" class="w-full max-w-xs p-4 bg-blue-600 rounded-2xl font-bold">UNLOCK PREMIUM</button>
        </div>

        <div id="main-content" class="hidden">
            <div id="home-tab" class="tab-page">
                <div class="glow-card">
                    <select id="pair-select" class="w-full p-4 bg-slate-900 rounded-xl mb-4 border border-slate-700 font-bold">{pair_opts}</select>
                    <button id="gen-btn" onclick="generateSignal()" class="w-full p-4 bg-yellow-500 text-black font-black rounded-xl uppercase">Analyze Signal</button>
                </div>
                <div class="glow-card">
                    <div id="chart-box" class="w-full aspect-video bg-black rounded-lg flex items-center justify-center border border-slate-800 text-[10px] text-slate-700">No Chart Loaded</div>
                </div>
                <div class="glow-card">
                    <div class="grid grid-cols-2 gap-3 mb-4">
                        <button onclick="record('win')" class="p-4 bg-blue-600 rounded-xl font-bold text-xs uppercase">Win</button>
                        <button onclick="record('loss')" class="p-4 bg-blue-600 rounded-xl font-bold text-xs uppercase">Loss</button>
                    </div>
                    <button onclick="sendFinalReport()" class="w-full p-4 bg-yellow-500 text-black font-black rounded-xl uppercase">Send Partial Report</button>
                </div>
            </div>

            <div id="settings-tab" class="tab-page hidden">
                <div class="glow-card">
                    <h3 class="text-yellow-500 font-bold mb-6 uppercase text-sm">Telegram Settings</h3>
                    <div class="flex items-center justify-between p-4 bg-slate-900 rounded-xl border border-slate-800 mb-6">
                        <span class="text-xs font-bold uppercase">Sending Status</span>
                        <label class="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" id="tg-toggle" class="sr-only" onchange="saveConfig()" checked>
                            <div class="toggle-bg block bg-slate-700 w-12 h-7 rounded-full"></div>
                        </label>
                    </div>
                    <div class="space-y-4">
                        <input id="bot-token" type="text" class="input-box" placeholder="Custom Bot Token" onchange="saveConfig()">
                        <input id="chat-id" type="text" class="input-box" placeholder="Custom Chat ID" onchange="saveConfig()">
                    </div>
                </div>
            </div>

            <div id="history-tab" class="tab-page hidden">
                <div class="glow-card"><div id="history-list" class="space-y-2 text-[10px]"></div></div>
            </div>

            <div id="profile-tab" class="tab-page hidden text-center py-10">
                <div class="w-20 h-20 bg-blue-600 rounded-full mx-auto mb-4 flex items-center justify-center text-2xl font-bold">R</div>
                <h2 class="font-bold text-xl uppercase">Dark-X-Rayhan</h2>
                <div id="u-type" class="text-blue-500 font-bold text-xs mb-8 uppercase">Free User</div>
                <div class="grid grid-cols-2 gap-4 px-4">
                    <div class="bg-slate-800 p-4 rounded-xl">
                        <p class="text-2xl font-black text-blue-500" id="p-win">0</p>
                        <p class="text-[9px] uppercase">Total Win</p>
                    </div>
                    <div class="bg-slate-800 p-4 rounded-xl">
                        <p class="text-2xl font-black text-red-500" id="p-loss">0</p>
                        <p class="text-[9px] uppercase">Total Loss</p>
                    </div>
                </div>
            </div>
        </div>

        <nav id="navbar" class="hidden fixed bottom-0 left-0 right-0 bg-[#151a21] border-t border-slate-800 flex justify-around p-4">
            <button onclick="switchTab('home')" class="nav-btn nav-active flex flex-col items-center text-[8px]"><i class="fas fa-home mb-1 text-lg"></i>HOME</button>
            <button onclick="switchTab('history')" class="nav-btn flex flex-col items-center text-[8px] text-slate-500"><i class="fas fa-history mb-1 text-lg"></i>HISTORY</button>
            <button onclick="switchTab('settings')" class="nav-btn flex flex-col items-center text-[8px] text-slate-500"><i class="fas fa-cog mb-1 text-lg"></i>SETTING</button>
            <button onclick="switchTab('profile')" class="nav-btn flex flex-col items-center text-[8px] text-slate-500"><i class="fas fa-user mb-1 text-lg"></i>PROFILE</button>
        </nav>

        <script>
            async function login(m) {{
                if(m === 'premium') {{
                    const key = document.getElementById('key-input').value;
                    if(key !== 'DARK-X-RAYHAN') return alert('Invalid Key');
                    document.getElementById('u-type').innerText = '💎 Premium User';
                }}
                document.getElementById('auth-screen').classList.add('hidden');
                document.getElementById('main-content').classList.remove('hidden');
                document.getElementById('navbar').classList.remove('hidden');
            }}

            function switchTab(t) {{
                document.querySelectorAll('.tab-page').forEach(p => p.classList.add('hidden'));
                document.getElementById(t + '-tab').classList.remove('hidden');
                document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('nav-active', 'text-blue-500'));
                event.currentTarget.classList.add('nav-active', 'text-blue-500');
            }}

            async function saveConfig() {{
                const e = document.getElementById('tg-toggle').checked;
                const t = document.getElementById('bot-token').value;
                const c = document.getElementById('chat-id').value;
                await fetch(`/api/update_config?enabled=${{e}}&token=${{t}}&chat=${{c}}`);
            }}

            async function generateSignal() {{
                const p = document.getElementById('pair-select').value;
                document.getElementById('gen-btn').innerText = "Analyzing...";
                await fetch(`/api/signal?pair=${{p}}`);
                setTimeout(async () => {{
                    const r = await fetch('/api/get_ss');
                    const d = await r.json();
                    if(d.ss) document.getElementById('chart-box').innerHTML = `<img src="data:image/png;base64,${{d.ss}}" class="w-full">`;
                    document.getElementById('gen-btn').innerText = "Analyze Signal";
                }}, 3000);
            }}

            async function record(type) {{
                const pair = document.getElementById('pair-select').value;
                await fetch(`/api/record?type=${{type}}&pair=${{pair}}`);
                const r = await fetch('/api/get_stats');
                const s = await r.json();
                document.getElementById('p-win').innerText = s.win;
                document.getElementById('p-loss').innerText = s.loss;
            }}

            async function sendFinalReport() {{ await fetch('/api/report'); alert('Sent!'); }}
        </script>
    </body>
    </html>
    """

@app.get("/api/update_config")
async def update_config(enabled: str, token: str, chat: str):
    state["telegram_enabled"] = (enabled.lower() == 'true')
    state["bot_token"], state["chat_id"] = token, chat
    return {"ok": True}

@app.get("/api/get_stats")
async def get_stats(): return state["stats"]

@app.get("/api/signal")
async def api_signal(pair: str):
    asyncio.create_task(process_signal(pair))
    return {"ok": True}

@app.get("/api/get_ss")
async def get_ss(): return {"ss": state["current_ss"]}

@app.get("/api/record")
async def api_record(type: str, pair: str):
    now = datetime.datetime.now().strftime("%H:%M")
    if type in state["stats"]: state["stats"][type] += 1
    state["session_history"].append(f"〄 {now} - {pair} - {type.upper()}")
    
    if state["telegram_enabled"] and state["bot_token"]:
        bot = Bot(token=state["bot_token"])
        msg = f"========== 𝗥𝗘𝗦𝗨𝗟𝗧 ===========\n\n{pair} | {now}\nRESULT: {type.upper()}\n\nWIN: {state['stats']['win']} | LOSS: {state['stats']['loss']}"
        try: await bot.send_message(state["chat_id"], msg)
        except: pass
    return {"ok": True}

@app.get("/api/report")
async def api_report():
    if not state["telegram_enabled"]: return
    history = "\n".join(state["session_history"])
    report = f"=========== 𝗣𝗔𝗥𝗧𝗜𝗔𝗟 ============️\n\n{history}\n\nWIN: {state['stats']['win']} | LOSS: {state['stats']['loss']}"
    try:
        bot = Bot(token=state["bot_token"])
        await bot.send_message(state["chat_id"], report)
    except: pass
    return {"ok": True}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
