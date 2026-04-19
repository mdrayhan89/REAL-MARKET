import asyncio
import datetime
import io
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
    "telegram_enabled": True  # সেটিংস থেকে এটি কন্ট্রোল হবে
}

user_sessions = {} 
signal_history = []

# --- ১ সেকেন্ডে সিগন্যাল ও এসএস পাঠানোর ইঞ্জিন ---
async def send_ultra_fast_signal(pair, action):
    # ডাইনামিক লিঙ্ক জেনারেশন
    ss_url = f"https://dark-live-ss.onrender.com/?Pair={pair.lower()}"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1000, 'height': 600})
        page = await context.new_page()
        
        try:
            # পেজ লোড এবং স্ক্রিনশট (Zero Delay logic)
            await page.goto(ss_url, wait_until="networkidle")
            ss_bytes = await page.screenshot(type='png')
            
            now = datetime.datetime.now()
            trade_time = (now + datetime.timedelta(minutes=1)).strftime("%H:%M")
            
            # প্রিমিয়াম আউটপুট ফরম্যাট
            caption = (
                f"✿° ━━━━━━━━━━━━━ ✿°\n"
                f"👑 <b>DARK-X-SNIPER V3.0</b> 👑\n"
                f"— — — — — — — — — — — —\n"
                f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
                f" <tg-emoji emoji-id='5472416843438246859'>📊</tg-emoji> <b>Pair:—</b> {pair}\n"
                f" <tg-emoji emoji-id='6325717349257187998'>⌛</tg-emoji> <b>TimeFrame:—</b> M1\n"
                f" <tg-emoji emoji-id='5212985021870123409'>🚀</tg-emoji> <b>TradeTime:—</b> {trade_time}\n"
                f" <tg-emoji emoji-id='6264696987946324240'>🔋</tg-emoji> <b>Direction:—</b> {action}\n"
                f"┗━━━━━━━━━━━━━━━━━━━━┛\n"
                f" • ────── ✾ ────── •\n"
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

# --- মডার্ন ইউআই কন্ট্রোল প্যানেল ---
@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DARK-X-PRO PANEL</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body { background: #0b0e14; color: #fff; font-family: sans-serif; }
            .glass { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }
            .nav-active { color: #3b82f6; border-top: 2px solid #3b82f6; }
        </style>
    </head>
    <body class="pb-24">
        <div id="auth" class="fixed inset-0 z-50 bg-[#0b0e14] flex flex-col items-center justify-center p-6">
            <h2 class="text-xl font-bold mb-6">ACCESS KEY REQUIRED</h2>
            <input id="key" type="password" placeholder="Enter Key" class="w-full max-w-xs p-4 glass rounded-xl mb-4 text-center">
            <button onclick="login()" class="w-full max-w-xs p-4 bg-blue-600 rounded-xl font-bold">UNLOCKED PANEL</button>
        </div>

        <div id="panel" class="hidden p-4">
            <div id="home" class="tab-content">
                <div class="glass p-6 rounded-2xl mb-4">
                    <label class="text-xs text-blue-400 font-bold uppercase">Market Selection</label>
                    <select id="pair" class="w-full p-4 glass rounded-xl mt-2 mb-4">
                        <option value="EURJPY">EURJPY</option>
                        <option value="XAUUSD">XAUUSD (GOLD)</option>
                        <option value="NZDUSD">NZDUSD</option>
                        <option value="AUTO">AUTO MODE (2 MIN)</option>
                    </select>
                    <button id="genBtn" onclick="generate()" class="w-full p-5 bg-yellow-500 text-black font-black rounded-2xl">GENERATE & SEND SS</button>
                    <div id="cool" class="hidden mt-4 text-center text-red-500 font-bold">Next Signal In: <span id="sec">120</span>s</div>
                </div>
                <div class="glass rounded-2xl p-4 h-48 flex items-center justify-center border-dashed border-2 border-slate-700">
                    <p class="text-slate-500">Live API Chart Preview</p>
                </div>
            </div>

            <div id="settings" class="tab-content hidden">
                <div class="glass p-6 rounded-2xl">
                    <h3 class="font-bold mb-4">Telegram Bot Settings</h3>
                    <div class="flex justify-between items-center glass p-4 rounded-xl">
                        <span>Send Photo with Signal</span>
                        <input type="checkbox" checked class="w-6 h-6">
                    </div>
                </div>
            </div>

            <div id="profile" class="tab-content hidden text-center p-10">
                <div class="w-24 h-24 bg-blue-600 rounded-full mx-auto mb-4 flex items-center justify-center text-3xl font-bold">R</div>
                <h2 class="text-2xl font-bold">DARK-X-RAYHAN</h2>
                <p class="text-blue-400">@mdrayhan89</p>
            </div>
        </div>

        <nav class="fixed bottom-0 left-0 right-0 glass flex justify-around p-3 border-t border-slate-800">
            <button onclick="tab('home')" class="nav-btn nav-active"><i class="fas fa-home"></i></button>
            <button onclick="tab('settings')" class="nav-btn"><i class="fas fa-cog"></i></button>
            <button onclick="tab('profile')" class="nav-btn"><i class="fas fa-user"></i></button>
        </nav>

        <script>
            function login() {
                if(document.getElementById('key').value === 'DARK-X-RAYHAN') {
                    document.getElementById('auth').classList.add('hidden');
                    document.getElementById('panel').classList.remove('hidden');
                } else { alert('Invalid Key'); }
            }
            function tab(t) {
                document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
                document.getElementById(t).classList.remove('hidden');
            }
            async function generate() {
                const p = document.getElementById('pair').value;
                document.getElementById('genBtn').disabled = true;
                const res = await fetch(`/api/send?pair=${p}`);
                if(p !== 'AUTO') startTimer();
            }
            function startTimer() {
                document.getElementById('cool').classList.remove('hidden');
                let s = 120;
                const i = setInterval(() => {
                    s--; document.getElementById('sec').innerText = s;
                    if(s<=0) { clearInterval(i); document.getElementById('genBtn').disabled = false; document.getElementById('cool').classList.add('hidden'); }
                }, 1000);
            }
        </script>
    </body>
    </html>
    """

@app.get("/api/send")
async def api_send(pair: str):
    # ব্যাকগ্রাউন্ডে সুপার ফাস্ট সিগন্যাল পাঠানো হবে
    asyncio.create_task(send_ultra_fast_signal(pair, "CALL ⬆️"))
    return {"status": "processing"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
