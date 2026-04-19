import asyncio
import datetime
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from telegram import Bot
from telegram.constants import ParseMode
from playwright.async_api import async_playwright

app = FastAPI()

# --- গ্লোবাল কনফিগারেশন ---
config = {
    "bot_token": "8354111202:AAEqFLMoJ7W7AlwpfHibZbpusiWbnOcl5Xc",
    "chat_id": "-1003862859969",
    "premium_key": "DARK-X-RAYHAN",
    "owner_tg": "@mdrayhan89"
}

session_stats = {"win": 0, "loss": 0, "mtg": 0}
signal_history = []

# --- ১ সেকেন্ডে সিগন্যাল ও এসএস পাঠানোর ইঞ্জিন ---
async def capture_and_send(pair, action):
    ss_url = f"https://dark-live-ss.onrender.com/?Pair={pair.lower()}"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        try:
            await page.goto(ss_url, wait_until="networkidle")
            ss_bytes = await page.screenshot(type='png')
            
            now = datetime.datetime.now()
            trade_time = (now + datetime.timedelta(minutes=1)).strftime("%H:%M")
            
            caption = (
                f"✿° ━━━━━━━━━━━━━ ✿°\n"
                f"👑 <b>DARK-X-SNIPER V3.0</b> 👑\n"
                f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
                f" <tg-emoji emoji-id='5472416843438246859'>📊</tg-emoji> <b>Pair:—</b> {pair}\n"
                f" <tg-emoji emoji-id='5212985021870123409'>🚀</tg-emoji> <b>TradeTime:—</b> {trade_time}\n"
                f" <tg-emoji emoji-id='6264696987946324240'>🔋</tg-emoji> <b>Direction:—</b> {action}\n"
                f"┗━━━━━━━━━━━━━━━━━━━━┛\n"
                f"😈 <b>DARK-X-RAYHAN QUOTEX</b>"
            )
            bot = Bot(token=config["bot_token"])
            await bot.send_photo(chat_id=config["chat_id"], photo=ss_bytes, caption=caption, parse_mode=ParseMode.HTML)
        finally:
            await browser.close()

# --- মডার্ন ইউআই কন্ট্রোল প্যানেল (আপনার স্ক্রিনশট অনুযায়ী) ---
@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ADVANCED SIGNAL GENERATOR PRO</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body { background: #0f172a; color: #fff; font-family: 'Inter', sans-serif; }
            .section-card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; margin-bottom: 20px; padding: 20px; box-shadow: 0 0 20px rgba(0,0,0,0.3); }
            .glow-yellow { border: 1px solid #eab308; box-shadow: 0 0 10px rgba(234, 179, 8, 0.2); }
            .nav-item { color: #94a3b8; transition: 0.3s; }
            .nav-active { color: #3b82f6; }
            .btn-blue { background: #2563eb; transition: 0.2s; }
            .btn-blue:hover { background: #1d4ed8; }
        </style>
    </head>
    <body class="pb-24">
        <div id="auth" class="fixed inset-0 z-50 bg-[#0b0e14] flex flex-col items-center justify-center p-6">
            <h1 class="text-2xl font-bold mb-8 text-blue-500">DARK-X-PRO LOGIN</h1>
            <input id="key" type="password" placeholder="Premium Access Key" class="w-full max-w-xs p-4 bg-slate-800 rounded-xl mb-4 text-center focus:outline-none border border-slate-700">
            <button onclick="login()" class="w-full max-w-xs p-4 bg-blue-600 rounded-xl font-bold uppercase tracking-widest">Unlock Panel</button>
        </div>

        <div id="panel" class="hidden max-w-4xl mx-auto p-4">
            <div id="home-tab" class="tab-content">
                <div class="section-card glow-yellow">
                    <select id="pair" class="w-full p-4 bg-slate-900 rounded-lg mb-4 border border-slate-700">
                        <option value="AUTO">Auto (EMA Strategy)</option>
                        <option value="EURJPY">EURJPY</option>
                        <option value="XAUUSD">XAUUSD</option>
                    </select>
                    <button id="genBtn" onclick="generate()" class="w-full p-4 bg-yellow-500 text-black font-black rounded-lg uppercase"><i class="fas fa-paper-plane mr-2"></i> Generate & Send</button>
                    <div id="cooldown" class="hidden mt-4 text-center text-red-500 font-bold">Wait: <span id="timer">120</span>s</div>
                </div>

                <div class="section-card glow-yellow">
                    <h3 class="text-blue-400 text-xs font-bold uppercase mb-4"><i class="fas fa-trophy mr-2"></i> Record Result <span class="bg-yellow-500 text-black px-2 py-0.5 rounded text-[10px] ml-2">PRO</span></h3>
                    <div class="grid grid-cols-2 gap-4 mb-4">
                        <button onclick="record('win')" class="p-3 btn-blue rounded-lg font-bold text-sm">✓ WIN</button>
                        <button onclick="record('loss')" class="p-3 btn-blue rounded-lg font-bold text-sm">✕ LOSS</button>
                        <button onclick="record('mtg')" class="p-3 btn-blue rounded-lg font-bold text-sm">⇄ MTG</button>
                        <button class="p-3 btn-blue rounded-lg font-bold text-sm">↺ REFUND</button>
                    </div>
                </div>

                <div class="section-card glow-yellow">
                    <h3 class="text-blue-400 text-xs font-bold uppercase mb-4"><i class="fas fa-file-alt mr-2"></i> Full Trading Report <span class="bg-yellow-500 text-black px-2 py-0.5 rounded text-[10px] ml-2">PRO</span></h3>
                    <button onclick="sendReport()" class="w-full p-4 btn-blue rounded-lg font-bold uppercase mb-3">Send Report</button>
                    <button class="w-full p-4 bg-yellow-500 text-black rounded-lg font-bold uppercase">Export as PDF</button>
                </div>
            </div>

            <div id="settings-tab" class="tab-content hidden">
                <div class="section-card glow-yellow">
                    <h3 class="text-blue-400 text-xs font-bold uppercase mb-6"><i class="fas fa-robot mr-2"></i> Telegram API <span class="bg-yellow-500 text-black px-2 py-0.5 rounded text-[10px] ml-2">PRO</span></h3>
                    <div class="space-y-4">
                        <div>
                            <label class="text-[10px] text-slate-400 ml-1">Bot Token</label>
                            <input type="text" value="8354111202:AAEqFL..." class="w-full p-3 bg-slate-900 rounded-lg border border-slate-700 mt-1" readonly>
                        </div>
                        <div>
                            <label class="text-[10px] text-slate-400 ml-1">Chat ID</label>
                            <input type="text" value="-100386285..." class="w-full p-3 bg-slate-900 rounded-lg border border-slate-700 mt-1" readonly>
                        </div>
                        <div class="flex justify-between items-center p-3 bg-slate-900 rounded-lg">
                            <span class="text-sm">Send Photo With Signal</span>
                            <div class="w-12 h-6 bg-blue-600 rounded-full flex items-center px-1"><div class="w-4 h-4 bg-white rounded-full ml-auto"></div></div>
                        </div>
                    </div>
                </div>
            </div>

            <div id="profile-tab" class="tab-content hidden text-center py-12">
                <div class="w-24 h-24 bg-blue-600 rounded-full mx-auto mb-4 flex items-center justify-center text-4xl font-bold shadow-lg">R</div>
                <h2 class="text-2xl font-bold">DARK-X-RAYHAN</h2>
                <p class="text-blue-400 font-medium">@mdrayhan89</p>
            </div>
        </div>

        <nav class="fixed bottom-0 left-0 right-0 bg-[#1e293b] flex justify-around p-4 border-t border-slate-800 shadow-2xl">
            <button onclick="showTab('home')" class="nav-item nav-active flex flex-col items-center"><i class="fas fa-home"></i><span class="text-[10px] mt-1">Home</span></button>
            <button onclick="showTab('history')" class="nav-item flex flex-col items-center"><i class="fas fa-history"></i><span class="text-[10px] mt-1">History</span></button>
            <button onclick="showTab('settings')" class="nav-item flex flex-col items-center"><i class="fas fa-cog"></i><span class="text-[10px] mt-1">Settings</span></button>
            <button onclick="showTab('profile')" class="nav-item flex flex-col items-center"><i class="fas fa-user"></i><span class="text-[10px] mt-1">Profile</span></button>
        </nav>

        <script>
            function login() {
                if(document.getElementById('key').value === 'DARK-X-RAYHAN') {
                    document.getElementById('auth').style.display = 'none';
                    document.getElementById('panel').style.display = 'block';
                } else { alert('Access Denied!'); }
            }
            function showTab(tab) {
                document.querySelectorAll('.tab-content').forEach(t => t.classList.add('hidden'));
                document.getElementById(tab + '-tab').classList.remove('hidden');
                document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('nav-active'));
                event.currentTarget.classList.add('nav-active');
            }
            async function generate() {
                const pair = document.getElementById('pair').value;
                document.getElementById('genBtn').disabled = true;
                await fetch(`/api/signal?pair=${pair}`);
                if(pair !== 'AUTO') startTimer();
            }
            function startTimer() {
                document.getElementById('cooldown').classList.remove('hidden');
                let s = 120;
                const i = setInterval(() => {
                    s--; document.getElementById('timer').innerText = s;
                    if(s<=0) { clearInterval(i); document.getElementById('genBtn').disabled = false; document.getElementById('cooldown').classList.add('hidden'); }
                }, 1000);
            }
            async function record(type) { await fetch(`/api/record?type=${type}`); alert(type.toUpperCase() + ' recorded!'); }
            async function sendReport() { await fetch('/api/report'); alert('Report Sent to Telegram!'); }
        </script>
    </body>
    </html>
    """

@app.get("/api/signal")
async def api_signal(pair: str):
    asyncio.create_task(capture_and_send(pair, "CALL ⬆️"))
    return {"status": "ok"}

@app.get("/api/record")
async def api_record(type: str):
    global session_stats
    if type in session_stats: session_stats[type] += 1
    return {"status": "ok"}

@app.get("/api/report")
async def api_report():
    report = (
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>FINAL SESSION REPORT</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Wins: {session_stats['win']}\n"
        f"❌ Loss: {session_stats['loss']}\n"
        f"🔄 MTG: {session_stats['mtg']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>Owner:</b> DARK-X-RAYHAN"
    )
    bot = Bot(token=config["bot_token"])
    await bot.send_message(config["chat_id"], report, parse_mode=ParseMode.HTML)
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
