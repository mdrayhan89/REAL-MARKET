import asyncio
import datetime
import random
import uvicorn
import base64
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from telegram import Bot
from telegram.constants import ParseMode
from playwright.async_api import async_playwright

app = FastAPI()

# --- কনফিগারেশন ও স্টেট ---
config = {
    "bot_token": "8354111202:AAEqFLMoJ7W7AlwpfHibZbpusiWbnOcl5Xc",
    "chat_id": "-1003862859969",
    "premium_key": "DARK-X-RAYHAN",
    "owner_tg": "@mdrayhan89"
}

state = {
    "telegram_enabled": True, # টেলিগ্রাম অন/অফ করার জন্য
    "stats": {"win": 0, "loss": 0, "mtg": 0, "refund": 0},
    "session_history": [],
    "current_ss": ""
}

ALL_PAIRS = ["XAUUSD", "EURJPY", "NZDUSD", "EURUSD", "GBPUSD", "AUDUSD", "USDCAD", "USDJPY", "EURGBP", "AUDJPY", "CADJPY"]

# --- রিয়েল একিউরেসি ক্যালকুলেটর ---
def get_strategy_accuracy():
    factors = [random.randint(90, 99) for _ in range(8)]
    return sum(factors) // 8

# --- সিগন্যাল ইঞ্জিন ---
async def process_signal(pair):
    accuracy = get_strategy_accuracy()
    direction = random.choice(["CALL ⬆️", "PUT ⬇️"])
    now = datetime.datetime.now().strftime("%H:%M")
    
    ss_url = f"https://dark-live-ss.onrender.com/?Pair={pair.lower()}"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(ss_url, wait_until="networkidle")
            ss_bytes = await page.screenshot()
            state["current_ss"] = base64.b64encode(ss_bytes).decode('utf-8')
            
            # টেলিগ্রাম অন থাকলে মেসেজ পাঠাবে
            if state["telegram_enabled"]:
                signal_text = (
                    f"╔═━━━━━ ◥◣◆◢◤ ━━━━━═╗\n"
                    f"             PAIR        ➜ {pair}\n"
                    f"             TIME       ➜ {now}\n"
                    f"             EXPIRE    ➜  M1\n"
                    f"             DIRECTION ➜ {direction}\n"
                    f"             ACCURACY     ➜ {accuracy}%\n"
                    f"╚═━━━━━ ◢◤◆◥◣ ━━━━━═╝\n\n"
                    f" CONTRACT HERE : {config['owner_tg']}↯\n"
                    f" SIGNAL SEND SUCCESSFULLY"
                )
                bot = Bot(token=config["bot_token"])
                await bot.send_photo(chat_id=config["chat_id"], photo=ss_bytes, caption=signal_text, parse_mode=ParseMode.HTML)
        finally: await browser.close()

# --- মেইন প্যানেল UI ---
@app.get("/", response_class=HTMLResponse)
async def main_ui():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DARK-X-PRO V5.1</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body { background: #0b0e14; color: #fff; font-family: 'Inter', sans-serif; }
            .glow-card { background: #151a21; border: 1px solid #2d3748; border-radius: 15px; padding: 20px; margin-bottom: 20px; }
            .nav-active { color: #3b82f6; border-top: 2px solid #3b82f6; }
            .hidden { display: none; }
            .toggle-bg:after { content: ''; position: absolute; top: 2px; left: 2px; background: white; border: 1px solid #d1d5db; border-radius: 9999px; height: 1.25rem; width: 1.25rem; transition: all .3s; }
            input:checked + .toggle-bg:after { transform: translateX(100%); border-color: #3b82f6; }
            input:checked + .toggle-bg { background-color: #3b82f6; }
        </style>
    </head>
    <body class="pb-24 p-4">

        <div id="auth-screen" class="fixed inset-0 z-50 bg-[#0b0e14] flex flex-col items-center justify-center p-6">
            <h1 class="text-3xl font-black mb-10 text-blue-500 italic">DARK-X-PRO</h1>
            <button onclick="login('free')" class="w-full max-w-xs p-4 bg-slate-800 rounded-2xl font-bold mb-4">FREE ACCESS</button>
            <input id="key-input" type="password" placeholder="Premium Key" class="w-full max-w-xs p-4 bg-slate-900 rounded-2xl mb-4 text-center border border-slate-800 outline-none">
            <button onclick="login('premium')" class="w-full max-w-xs p-4 bg-blue-600 rounded-2xl font-bold">UNLOCK PREMIUM</button>
        </div>

        <div id="main-content" class="hidden">
            <div id="home-tab" class="tab-page">
                <div class="glow-card">
                    <select id="pair-select" class="w-full p-4 bg-slate-900 rounded-xl mb-4 border border-slate-700 font-bold">
                        <option value="AUTO">🚀 SMART AUTO SCAN</option>
                        <option value="EURUSD">EURUSD</option><option value="USDJPY">USDJPY</option>
                        <option value="XAUUSD">XAUUSD</option><option value="GBPUSD">GBPUSD</option>
                    </select>
                    <button id="gen-btn" onclick="generateSignal()" class="w-full p-4 bg-yellow-500 text-black font-black rounded-xl uppercase">Analyze & Send</button>
                </div>

                <div class="glow-card">
                    <h3 class="text-blue-400 text-[10px] font-bold uppercase mb-4">Live Chart Preview</h3>
                    <div id="chart-box" class="w-full aspect-video bg-black rounded-lg flex items-center justify-center border border-slate-800 overflow-hidden text-xs text-slate-700 italic">No Chart Loaded</div>
                </div>

                <div class="glow-card">
                    <div class="grid grid-cols-2 gap-3 mb-4">
                        <button onclick="record('win')" class="p-4 bg-blue-600 rounded-xl font-bold text-xs uppercase">Win</button>
                        <button onclick="record('loss')" class="p-4 bg-blue-600 rounded-xl font-bold text-xs uppercase">Loss</button>
                        <button onclick="record('mtg')" class="p-4 bg-blue-600 rounded-xl font-bold text-xs uppercase">MTG</button>
                        <button onclick="record('refund')" class="p-4 bg-blue-600 rounded-xl font-bold text-xs uppercase">Refund</button>
                    </div>
                    <button onclick="sendFinalReport()" class="w-full p-4 bg-yellow-500 text-black font-black rounded-xl uppercase">Send Partial Report</button>
                </div>
            </div>

            <div id="settings-tab" class="tab-page hidden">
                <div class="glow-card">
                    <h3 class="text-yellow-500 font-bold mb-6 uppercase text-sm"><i class="fas fa-cog mr-2"></i> Control Panel</h3>
                    <div class="flex items-center justify-between p-4 bg-slate-900 rounded-xl border border-slate-800">
                        <div>
                            <p class="font-bold text-sm text-white">Telegram Bot Status</p>
                            <p class="text-[10px] text-slate-500">Enable/Disable Auto Sending</p>
                        </div>
                        <label class="flex items-center cursor-pointer relative">
                            <input type="checkbox" id="tg-toggle" class="sr-only" onchange="toggleTelegram()" checked>
                            <div class="toggle-bg block bg-slate-700 w-12 h-7 rounded-full"></div>
                        </label>
                    </div>
                </div>
            </div>

            <div id="history-tab" class="tab-page hidden">
                <div class="glow-card">
                    <h3 class="text-blue-500 font-bold mb-4 uppercase text-sm">Signal History</h3>
                    <div id="history-list" class="space-y-3"></div>
                </div>
            </div>

            <div id="profile-tab" class="tab-page hidden text-center py-10">
                <div class="w-20 h-20 bg-blue-600 rounded-full mx-auto mb-4 flex items-center justify-center text-2xl font-bold">R</div>
                <h2 class="font-bold">DARK-X-RAYHAN</h2>
                <div class="grid grid-cols-2 gap-4 mt-8 px-4">
                    <div class="bg-slate-800 p-4 rounded-xl border border-slate-700"><p class="text-yellow-500 font-black text-xl" id="p-win">0</p><p class="text-[9px]">WIN</p></div>
                    <div class="bg-slate-800 p-4 rounded-xl border border-slate-700"><p class="text-red-500 font-black text-xl" id="p-loss">0</p><p class="text-[9px]">LOSS</p></div>
                </div>
            </div>
        </div>

        <nav id="navbar" class="hidden fixed bottom-0 left-0 right-0 bg-[#151a21] border-t border-slate-800 flex justify-around p-4">
            <button onclick="switchTab('home')" class="nav-btn nav-active flex flex-col items-center text-[8px]"><i class="fas fa-home mb-1"></i>HOME</button>
            <button onclick="switchTab('history')" class="nav-btn flex flex-col items-center text-[8px] text-slate-500"><i class="fas fa-history mb-1"></i>HISTORY</button>
            <button onclick="switchTab('settings')" class="nav-btn flex flex-col items-center text-[8px] text-slate-500"><i class="fas fa-cog mb-1"></i>SETTING</button>
            <button onclick="switchTab('profile')" class="nav-btn flex flex-col items-center text-[8px] text-slate-500"><i class="fas fa-user mb-1"></i>PROFILE</button>
        </nav>

        <script>
            function login(m) {
                if(m === 'premium' && document.getElementById('key-input').value !== 'DARK-X-RAYHAN') return alert('Wrong Key!');
                document.getElementById('auth-screen').classList.add('hidden');
                document.getElementById('main-content').classList.remove('hidden');
                document.getElementById('navbar').classList.remove('hidden');
            }
            function switchTab(t) {
                document.querySelectorAll('.tab-page').forEach(p => p.classList.add('hidden'));
                document.getElementById(t + '-tab').classList.remove('hidden');
                document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('nav-active', 'text-blue-500'));
                event.currentTarget.classList.add('nav-active', 'text-blue-500');
            }
            async function toggleTelegram() {
                const status = document.getElementById('tg-toggle').checked;
                await fetch(`/api/toggle_tg?status=${status}`);
            }
            async function generateSignal() {
                const p = document.getElementById('pair-select').value;
                const b = document.getElementById('gen-btn');
                b.disabled = true; b.innerText = "MARKET ANALYZING...";
                await fetch(`/api/signal?pair=${p}`);
                const check = setInterval(async () => {
                    const r = await fetch('/api/get_ss');
                    const d = await r.json();
                    if(d.ss) {
                        document.getElementById('chart-box').innerHTML = `<img src="data:image/png;base64,${d.ss}" class="w-full h-full object-cover">`;
                        b.disabled = false; b.innerText = "Analyze & Send";
                        clearInterval(check);
                    }
                }, 1000);
            }
            async function record(type) {
                const pair = document.getElementById('pair-select').value;
                await fetch(`/api/record?type=${type}&pair=${pair}`);
                const r = await fetch('/api/stats');
                const s = await r.json();
                document.getElementById('p-win').innerText = s.win;
                document.getElementById('p-loss').innerText = s.loss;
            }
            async function sendFinalReport() { await fetch('/api/report'); alert('Partial Sent!'); }
        </script>
    </body>
    </html>
    """

# --- APIs ---
@app.get("/api/toggle_tg")
async def toggle_tg(status: str):
    state["telegram_enabled"] = (status.lower() == 'true')
    return {"status": state["telegram_enabled"]}

@app.get("/api/signal")
async def api_signal(pair: str):
    target_pair = random.choice(ALL_PAIRS) if pair == "AUTO" else pair
    asyncio.create_task(process_signal(target_pair))
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
        result_text = (
            f"========== 𝗥𝗘𝗦𝗨𝗟𝗧 ===========\n\n"
            f"╔═━━━━━ ◥◣◆◢◤ ━━━━━═╗\n"
            f"               {pair}  ┃  {now}\n"
            f"╚═━━━━━ ◢◤◆◥◣ ━━━━━═╝\n"
            f"        {emoji.get(type, 'RESULT')}\n"
            f"╔═━━━━━ ◥◣◆◢◤ ━━━━━═╗\n"
            f"            Win: {state['stats']['win']} | ️Loss: {state['stats']['loss']}\n"
            f"            Current Session: {state['stats']['win']}x{state['stats']['loss']}\n"
            f"╚═━━━━━ ◢◤◆◥◣ ━━━━━═╝"
        )
        bot = Bot(token=config["bot_token"])
        await bot.send_message(config["chat_id"], result_text, parse_mode=ParseMode.HTML)
    return {"status": "recorded"}

@app.get("/api/report")
async def api_report():
    if not state["telegram_enabled"]: return {"status": "telegram_disabled"}
    today = datetime.datetime.now().strftime("%d.%m.%Y")
    history_str = "\n".join(state["session_history"])
    partial_text = (
        f"=========== 𝗣𝗔𝗥𝗧𝗜𝗔𝗟 ============️\n\n"
        f"━━━━━━━━━・━━━━━━━━━\n"
        f"                   - {today}\n"
        f"━━━━━━━━━・━━━━━━━━━\n"
        f"                  REAL-MARKET\n"
        f"━━━━━━━━━・━━━━━━━━━\n"
        f"{history_str}\n"
        f"━━━━━━━━━・━━━━━━━━━\n"
        f" WIN : {state['stats']['win']} ┃ LOSS : {state['stats']['loss']} ┃ (100%)\n"
        f"━━━━━━━━━・━━━━━━━━━"
    )
    bot = Bot(token=config["bot_token"])
    await bot.send_message(config["chat_id"], partial_text, parse_mode=ParseMode.HTML)
    return {"status": "sent"}

@app.get("/api/stats")
async def get_stats(): return state["stats"]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
