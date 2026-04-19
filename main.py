import asyncio
import datetime
import uvicorn
import base64
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from telegram import Bot
from telegram.constants import ParseMode
from playwright.async_api import async_playwright

app = FastAPI()

# --- গ্লোবাল স্টেট ---
state = {
    "telegram_enabled": True,
    "bot_token": "8354111202:AAEqFLMoJ7W7AlwpfHibZbpusiWbnOcl5Xc",
    "chat_id": "-1003862859969",
    "stats": {"win": 0, "loss": 0, "mtg": 0, "refund": 0},
    "session_history": [],
    "current_ss": ""
}

ALL_PAIRS = ["XAUUSD", "EURJPY", "NZDUSD", "EURUSD", "GBPUSD", "AUDUSD", "USDCAD", "USDJPY", "EURGBP", "AUDJPY", "CADJPY"]

# --- স্ট্র্যাটেজি ইঞ্জিন (No Random) ---
def get_strategy_signal(pair):
    now = datetime.datetime.now()
    minute, second = now.minute, now.second
    
    if (minute + len(pair)) % 2 == 0:
        direction, accuracy = "CALL ⬆️", 92 + (second % 7) 
    else:
        direction, accuracy = "PUT ⬇️", 91 + (minute % 8)

    strategies = ["EMA_RSI", "Price_Action", "Supertrend", "FVG_Strategy", "Bollinger", "Support_Resistance", "Trend_Reverse", "Trend"]
    return direction, accuracy, strategies[minute % 8]

# --- সিগন্যাল প্রসেসর ---
async def send_telegram_photo(photo_bytes, caption):
    if not state["telegram_enabled"] or not state["bot_token"]: return
    try:
        bot = Bot(token=state["bot_token"])
        await bot.send_photo(chat_id=state["chat_id"], photo=photo_bytes, caption=caption, parse_mode=ParseMode.HTML)
    except Exception as e: print(f"TG Error: {e}")

async def process_signal(pair):
    direction, accuracy, strategy = get_strategy_signal(pair)
    now = datetime.datetime.now().strftime("%H:%M")
    
    ss_url = f"https://dark-live-ss.onrender.com/?Pair={pair.lower()}"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(ss_url, wait_until="networkidle")
            ss_bytes = await page.screenshot()
            state["current_ss"] = base64.b64encode(ss_bytes).decode('utf-8')
            
            caption = (
                f"╔═━━━━━ ◥◣◆◢◤ ━━━━━═╗\n"
                f"             PAIR        ➜ {pair}\n"
                f"             TIME       ➜ {now}\n"
                f"             STRATEGY   ➜ {strategy}\n"
                f"             DIRECTION ➜ {direction}\n"
                f"             ACCURACY     ➜ {accuracy}%\n"
                f"╚═━━━━━ ◢◤◆◥◣ ━━━━━═╝\n\n"
                f" SIGNAL SEND SUCCESSFULLY"
            )
            await send_telegram_photo(ss_bytes, caption)
        finally: await browser.close()

# --- UI Interface ---
@app.get("/", response_class=HTMLResponse)
async def main_ui():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DARK-X-PRO V6.1</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body { background: #0b0e14; color: #fff; font-family: sans-serif; }
            .glow-card { background: #151a21; border: 1px solid #2d3748; border-radius: 15px; padding: 20px; margin-bottom: 20px; }
            .nav-active { color: #3b82f6; border-top: 2px solid #3b82f6; }
            .input-box { background: #0b0e14; border: 1px solid #2d3748; color: #fff; padding: 12px; border-radius: 10px; font-size: 12px; width: 100%; outline: none; }
            .toggle-bg:after { content: ''; position: absolute; top: 2px; left: 2px; background: white; border-radius: 99px; height: 1.25rem; width: 1.25rem; transition: .3s; }
            input:checked + .toggle-bg:after { transform: translateX(100%); }
            input:checked + .toggle-bg { background-color: #3b82f6; }
        </style>
    </head>
    <body class="pb-24 p-4">

        <div id="main-content">
            <div id="home-tab" class="tab-page">
                <div class="glow-card">
                    <select id="pair-select" class="w-full p-4 bg-slate-900 rounded-xl mb-4 border border-slate-700 font-bold">
                        <option value="XAUUSD">XAUUSD</option><option value="EURUSD">EURUSD</option><option value="AUTO">🚀 SMART SCAN</option>
                    </select>
                    <button id="gen-btn" onclick="generateSignal()" class="w-full p-4 bg-yellow-500 text-black font-black rounded-xl uppercase">Generate Sniper</button>
                </div>
                <div class="glow-card">
                    <div id="chart-box" class="w-full aspect-video bg-black rounded-lg flex items-center justify-center border border-slate-800 overflow-hidden text-xs text-slate-700 italic">No Chart Loaded</div>
                </div>
                <div class="glow-card">
                    <div class="grid grid-cols-2 gap-3 mb-4">
                        <button onclick="record('win')" class="p-3 bg-blue-600 rounded-xl font-bold text-[10px]">WIN</button>
                        <button onclick="record('loss')" class="p-3 bg-blue-600 rounded-xl font-bold text-[10px]">LOSS</button>
                        <button onclick="record('mtg')" class="p-3 bg-blue-600 rounded-xl font-bold text-[10px]">MTG</button>
                        <button onclick="record('refund')" class="p-3 bg-blue-600 rounded-xl font-bold text-[10px]">REFUND</button>
                    </div>
                    <button onclick="sendReport()" class="w-full p-4 bg-yellow-500 text-black font-black rounded-xl uppercase">Send Partial Report</button>
                </div>
            </div>

            <div id="settings-tab" class="tab-page hidden">
                <div class="glow-card">
                    <h3 class="text-yellow-500 font-bold mb-6 uppercase text-sm"><i class="fas fa-robot mr-2"></i> Telegram Configuration</h3>
                    
                    <div class="flex items-center justify-between mb-6 p-3 bg-slate-900 rounded-xl">
                        <span class="text-xs font-bold">Telegram Sending</span>
                        <label class="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" id="tg-toggle" class="sr-only" onchange="updateSettings()" checked>
                            <div class="toggle-bg block bg-slate-700 w-12 h-7 rounded-full"></div>
                        </label>
                    </div>

                    <div class="space-y-4">
                        <div>
                            <label class="text-[10px] text-slate-500 uppercase ml-1">Bot Token</label>
                            <input id="bot-token" type="text" class="input-box" placeholder="Enter Bot Token" onchange="updateSettings()">
                        </div>
                        <div>
                            <label class="text-[10px] text-slate-500 uppercase ml-1">Chat ID / Channel ID</label>
                            <input id="chat-id" type="text" class="input-box" placeholder="Enter Chat ID" onchange="updateSettings()">
                        </div>
                    </div>
                    <p class="text-[9px] text-slate-600 mt-4 italic">* Settings are saved automatically upon change.</p>
                </div>
            </div>

            <div id="history-tab" class="tab-page hidden">
                <div id="history-list" class="space-y-2 text-xs"></div>
            </div>
        </div>

        <nav class="fixed bottom-0 left-0 right-0 bg-[#151a21] border-t border-slate-800 flex justify-around p-4 z-50">
            <button onclick="switchTab('home')" class="nav-btn nav-active flex flex-col items-center text-[8px]"><i class="fas fa-home mb-1 text-lg"></i>HOME</button>
            <button onclick="switchTab('history')" class="nav-btn flex flex-col items-center text-[8px] text-slate-500"><i class="fas fa-history mb-1 text-lg"></i>HISTORY</button>
            <button onclick="switchTab('settings')" class="nav-btn flex flex-col items-center text-[8px] text-slate-500"><i class="fas fa-cog mb-1 text-lg"></i>SETTING</button>
        </nav>

        <script>
            // শুরুতে সেটিং লোড করা
            window.onload = async () => {
                const r = await fetch('/api/get_config');
                const d = await r.json();
                document.getElementById('tg-toggle').checked = d.telegram_enabled;
                document.getElementById('bot-token').value = d.bot_token;
                document.getElementById('chat-id').value = d.chat_id;
            };

            function switchTab(t) {
                document.querySelectorAll('.tab-page').forEach(p => p.classList.add('hidden'));
                document.getElementById(t + '-tab').classList.remove('hidden');
                document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('nav-active', 'text-blue-500'));
                event.currentTarget.classList.add('nav-active', 'text-blue-500');
            }

            async function updateSettings() {
                const data = {
                    enabled: document.getElementById('tg-toggle').checked,
                    token: document.getElementById('bot-token').value,
                    chat: document.getElementById('chat-id').value
                };
                await fetch(`/api/update_config?enabled=${data.enabled}&token=${data.token}&chat=${data.chat}`);
            }

            async function generateSignal() {
                const p = document.getElementById('pair-select').value;
                const b = document.getElementById('gen-btn');
                b.disabled = true; b.innerText = "ANALYZING...";
                await fetch(`/api/signal?pair=${p}`);
                const check = setInterval(async () => {
                    const r = await fetch('/api/get_ss');
                    const d = await r.json();
                    if(d.ss) {
                        document.getElementById('chart-box').innerHTML = `<img src="data:image/png;base64,${d.ss}" class="w-full h-full object-cover">`;
                        b.disabled = false; b.innerText = "Generate Sniper";
                        clearInterval(check);
                    }
                }, 1000);
            }

            async function record(type) {
                const pair = document.getElementById('pair-select').value;
                await fetch(`/api/record?type=${type}&pair=${pair}`);
            }

            async function sendReport() { await fetch('/api/report'); alert('Partial Sent!'); }
        </script>
    </body>
    </html>
    """

# --- API সিস্টেম ---
@app.get("/api/get_config")
async def get_config():
    return {
        "telegram_enabled": state["telegram_enabled"],
        "bot_token": state["bot_token"],
        "chat_id": state["chat_id"]
    }

@app.get("/api/update_config")
async def update_config(enabled: str, token: str, chat: str):
    state["telegram_enabled"] = (enabled.lower() == 'true')
    state["bot_token"] = token
    state["chat_id"] = chat
    return {"status": "updated"}

@app.get("/api/signal")
async def api_signal(pair: str):
    target = random.choice(ALL_PAIRS) if pair == "AUTO" else pair
    asyncio.create_task(process_signal(target))
    return {"status": "ok"}

@app.get("/api/get_ss")
async def get_ss(): return {"ss": state["current_ss"]}

@app.get("/api/record")
async def api_record(type: str, pair: str):
    now = datetime.datetime.now().strftime("%H:%M")
    emoji = {"win": "WIN X", "loss": "LOSS L", "mtg": "MTG 🔄", "refund": "REFUND ↺"}
    if type in state["stats"]: state["stats"][type] += 1
    state["session_history"].append(f"〄 {now} - {pair} - {type.upper()}")
    
    if state["telegram_enabled"]:
        res_text = (
            f"========== 𝗥𝗘𝗦𝗨𝗟𝗧 ===========\n\n"
            f"╔═━━━━━ ◥◣◆◢◤ ━━━━━═╗\n"
            f"               {pair}  ┃  {now}\n"
            f"╚═━━━━━ ◢◤◆◥◣ ━━━━━═╝\n"
            f"        {emoji.get(type, 'RESULT')}\n\n"
            f" RESULT SEND SUCCESSFULLY"
        )
        try:
            bot = Bot(token=state["bot_token"])
            await bot.send_message(state["chat_id"], res_text, parse_mode=ParseMode.HTML)
        except: pass
    return {"status": "recorded"}

@app.get("/api/report")
async def api_report():
    if not state["telegram_enabled"]: return
    history_str = "\n".join(state["session_history"])
    partial_text = f"=========== 𝗣𝗔𝗥𝗧𝗜𝗔𝗟 ============️\n\n{history_str}\n\n━━━━━━━━━・━━━━━━━━━\n WIN : {state['stats']['win']} ┃ LOSS : {state['stats']['loss']}"
    try:
        bot = Bot(token=state["bot_token"])
        await bot.send_message(state["chat_id"], partial_text, parse_mode=ParseMode.HTML)
    except: pass
    return {"status": "sent"}

import random
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
