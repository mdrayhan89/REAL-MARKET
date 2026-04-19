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

# ট্রেডিং স্ট্যাটাস ও হিস্ট্রি
stats = {"win": 0, "loss": 0, "mtg": 0}

# --- ১ সেকেন্ডে সিগন্যাল ও এসএস পাঠানোর ইঞ্জিন ---
async def capture_and_send(pair, action):
    # আপনার দেওয়া রেন্ডার লিঙ্ক
    ss_url = f"https://dark-live-ss.onrender.com/?Pair={pair.lower()}"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        try:
            # আল্ট্রা ফাস্ট লোডিং লজিক
            await page.goto(ss_url, wait_until="networkidle")
            ss_bytes = await page.screenshot(type='png')
            
            now = datetime.datetime.now()
            trade_time = (now + datetime.timedelta(minutes=1)).strftime("%H:%M")
            
            # আপনার ৩ নম্বর ছবির মতো প্রিমিয়াম টেক্সট ফরম্যাট
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
            await bot.send_photo(
                chat_id=config["chat_id"], 
                photo=ss_bytes, 
                caption=caption, 
                parse_mode=ParseMode.HTML
            )
        finally:
            await browser.close()

# --- সম্পূর্ণ প্যানেল UI (লগইন + হোম + সেটিংস) ---
@app.get("/", response_class=HTMLResponse)
async def main_interface():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DARK-X-PRO | TRADING PANEL</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body { background: #0b0e14; color: #fff; font-family: 'Inter', sans-serif; overflow-x: hidden; }
            .glass { background: rgba(30, 41, 59, 0.6); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.05); }
            .glow-yellow { border: 1.5px solid #eab308; box-shadow: 0 0 15px rgba(234, 179, 8, 0.15); }
            .nav-active { color: #3b82f6; border-top: 2px solid #3b82f6; }
            .btn-action { transition: transform 0.1s; }
            .btn-action:active { transform: scale(0.95); }
        </style>
    </head>
    <body class="pb-20">

        <div id="auth-screen" class="fixed inset-0 z-50 bg-[#0b0e14] flex items-center justify-center p-6">
            <div class="w-full max-w-sm text-center">
                <h1 class="text-3xl font-black mb-10 text-blue-500 tracking-tighter">DARK-X-PRO</h1>
                
                <button onclick="login('free')" class="w-full p-4 bg-slate-800 hover:bg-slate-700 rounded-2xl font-bold mb-4 border border-slate-700 transition">
                    <i class="fas fa-unlock mr-2"></i> FREE ACCESS
                </button>

                <div class="flex items-center my-6">
                    <div class="flex-1 border-t border-slate-800"></div>
                    <span class="px-4 text-xs text-slate-500 font-bold uppercase">Premium Login</span>
                    <div class="flex-1 border-t border-slate-800"></div>
                </div>

                <input id="key-input" type="password" placeholder="Enter Premium Key" class="w-full p-4 bg-slate-900 rounded-2xl mb-4 text-center border border-slate-800 focus:border-blue-500 outline-none">
                <button onclick="login('premium')" class="w-full p-4 bg-blue-600 hover:bg-blue-500 rounded-2xl font-bold shadow-lg shadow-blue-900/40">
                    <i class="fas fa-crown mr-2 text-yellow-400"></i> UNLOCK PANEL
                </button>
            </div>
        </div>

        <div id="panel-content" class="hidden max-w-lg mx-auto p-4">
            
            <div id="home-tab" class="tab-page">
                <div class="glass p-5 rounded-3xl mb-5 glow-yellow">
                    <div class="flex justify-between items-center mb-4">
                        <span class="text-[10px] font-bold text-yellow-500 uppercase tracking-widest">Signal Generator</span>
                        <span id="user-badge" class="text-[9px] bg-blue-600 px-2 py-0.5 rounded-full uppercase">Premium</span>
                    </div>
                    <select id="pair-select" class="w-full p-4 bg-slate-900 rounded-xl mb-4 border border-slate-800 text-sm font-bold">
                        <option value="XAUUSD">XAUUSD (GOLD)</option>
                        <option value="EURJPY">EURJPY</option>
                        <option value="NZDUSD">NZDUSD</option>
                        <option value="AUTO">AUTO (EMA STRATEGY)</option>
                    </select>
                    <button id="gen-btn" onclick="generateSignal()" class="w-full p-4 bg-yellow-500 text-black font-black rounded-xl uppercase tracking-wider btn-action">
                        <i class="fas fa-bolt mr-2"></i> Generate & Send SS
                    </button>
                    <div id="timer-box" class="hidden mt-4 text-center text-red-500 font-bold text-sm">Next Signal: <span id="timer">120</span>s</div>
                </div>

                <div class="glass p-5 rounded-3xl mb-5 glow-yellow">
                    <h3 class="text-blue-400 text-[10px] font-bold uppercase mb-4 tracking-widest"><i class="fas fa-chart-line mr-2"></i> Result Recording</h3>
                    <div class="grid grid-cols-2 gap-3 mb-4">
                        <button onclick="record('win')" class="p-4 bg-blue-600 rounded-xl font-bold text-xs btn-action">✓ WIN</button>
                        <button onclick="record('loss')" class="p-4 bg-blue-600 rounded-xl font-bold text-xs btn-action">✕ LOSS</button>
                        <button onclick="record('mtg')" class="p-4 bg-blue-600 rounded-xl font-bold text-xs btn-action">⇄ MTG</button>
                        <button onclick="record('refund')" class="p-4 bg-blue-600 rounded-xl font-bold text-xs btn-action">↺ REFUND</button>
                    </div>
                </div>

                <div class="glass p-5 rounded-3xl glow-yellow text-center">
                    <h3 class="text-blue-400 text-[10px] font-bold uppercase mb-4 tracking-widest"><i class="fas fa-file-invoice mr-2"></i> Session Report</h3>
                    <button onclick="sendFinalReport()" class="w-full p-4 bg-blue-600 rounded-xl font-bold uppercase text-xs mb-3 btn-action">
                        <i class="fas fa-paper-plane mr-2"></i> Show Final Result
                    </button>
                    <button class="w-full p-4 bg-yellow-500 text-black rounded-xl font-black uppercase text-[10px] btn-action">Export History (PDF)</button>
                </div>
            </div>

            <div id="settings-tab" class="tab-page hidden">
                <div class="glass p-6 rounded-3xl glow-yellow">
                    <h3 class="text-blue-500 font-bold mb-6 text-sm uppercase tracking-widest">Telegram Bot Config</h3>
                    <div class="space-y-5">
                        <div class="group">
                            <label class="text-[9px] text-slate-500 font-bold ml-1">BOT TOKEN</label>
                            <input type="text" value="8354111202:AAEqFL..." class="w-full p-3 bg-slate-900 rounded-lg border border-slate-800 text-xs mt-1" readonly>
                        </div>
                        <div class="group">
                            <label class="text-[9px] text-slate-500 font-bold ml-1">CHAT ID</label>
                            <input type="text" value="-100386285..." class="w-full p-3 bg-slate-900 rounded-lg border border-slate-800 text-xs mt-1" readonly>
                        </div>
                        <div class="flex justify-between items-center p-3 bg-slate-900 rounded-xl">
                            <span class="text-xs font-bold">Send Photo with Signal</span>
                            <div class="w-10 h-5 bg-blue-600 rounded-full flex items-center px-1"><div class="w-3.5 h-3.5 bg-white rounded-full ml-auto shadow"></div></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <nav id="navbar" class="hidden fixed bottom-0 left-0 right-0 glass flex justify-around p-3 border-t border-slate-800">
            <button onclick="switchTab('home')" class="nav-item nav-active flex flex-col items-center"><i class="fas fa-home text-sm"></i><span class="text-[8px] mt-1 font-bold uppercase">Home</span></button>
            <button onclick="switchTab('history')" class="nav-item flex flex-col items-center text-slate-500"><i class="fas fa-history text-sm"></i><span class="text-[8px] mt-1 font-bold uppercase">History</span></button>
            <button onclick="switchTab('settings')" class="nav-item flex flex-col items-center text-slate-500"><i class="fas fa-cog text-sm"></i><span class="text-[8px] mt-1 font-bold uppercase">Settings</span></button>
            <button onclick="switchTab('profile')" class="nav-item flex flex-col items-center text-slate-500"><i class="fas fa-user text-sm"></i><span class="text-[8px] mt-1 font-bold uppercase">Profile</span></button>
        </nav>

        <script>
            let userType = 'free';
            let freeSignalCount = 0;

            function login(mode) {
                if(mode === 'premium') {
                    const key = document.getElementById('key-input').value;
                    if(key === 'DARK-X-RAYHAN') {
                        userType = 'premium';
                        document.getElementById('user-badge').innerText = 'Premium';
                        document.getElementById('user-badge').classList.replace('bg-blue-600', 'bg-yellow-500');
                    } else { alert('Invalid Premium Key!'); return; }
                } else {
                    userType = 'free';
                    document.getElementById('user-badge').innerText = 'Free (Limit: 5)';
                    document.getElementById('user-badge').classList.add('bg-slate-600');
                }
                document.getElementById('auth-screen').classList.add('hidden');
                document.getElementById('panel-content').classList.remove('hidden');
                document.getElementById('navbar').classList.remove('hidden');
            }

            function switchTab(tab) {
                document.querySelectorAll('.tab-page').forEach(t => t.classList.add('hidden'));
                const target = document.getElementById(tab + '-tab');
                if(target) target.classList.remove('hidden');
                document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('nav-active', 'text-blue-500'));
                event.currentTarget.classList.add('nav-active');
            }

            async function generateSignal() {
                if(userType === 'free' && freeSignalCount >= 5) {
                    alert('Free Limit Reached! Buy Premium.'); return;
                }
                const pair = document.getElementById('pair-select').value;
                document.getElementById('gen-btn').disabled = true;
                await fetch(`/api/signal?pair=${pair}`);
                if(userType === 'free') freeSignalCount++;
                if(pair !== 'AUTO') startTimer();
            }

            function startTimer() {
                document.getElementById('timer-box').classList.remove('hidden');
                let s = 120;
                const i = setInterval(() => {
                    s--; document.getElementById('timer').innerText = s;
                    if(s<=0) { clearInterval(i); document.getElementById('gen-btn').disabled = false; document.getElementById('timer-box').classList.add('hidden'); }
                }, 1000);
            }

            async function record(res) { await fetch(`/api/record?res=${res}`); }
            async function sendFinalReport() { await fetch('/api/report'); alert('Report Sent to Telegram!'); }
        </script>
    </body>
    </html>
    """

# --- API এন্ডপয়েন্টস ---
@app.get("/api/signal")
async def api_signal(pair: str):
    asyncio.create_task(capture_and_send(pair, "CALL ⬆️"))
    return {"status": "sent"}

@app.get("/api/record")
async def api_record(res: str):
    global stats
    if res in stats: stats[res] += 1
    return {"status": "recorded"}

@app.get("/api/report")
async def api_report():
    report = (
        f"📊 <b>FINAL SESSION REPORT</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Wins: {stats['win']}\n"
        f"❌ Loss: {stats['loss']}\n"
        f"🔄 MTG: {stats['mtg']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>Owner:</b> DARK-X-RAYHAN"
    )
    bot = Bot(token=config["bot_token"])
    await bot.send_message(config["chat_id"], report, parse_mode=ParseMode.HTML)
    return {"status": "sent"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
