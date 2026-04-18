import asyncio
import datetime
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from telegram import Bot
from telegram.constants import ParseMode
from playwright.async_api import async_playwright

# --- কনফিগারেশন ---
TOKEN = '8354111202:AAEqFLMoJ7W7AlwpfHibZbpusiWbnOcl5Xc'
CHAT_ID = '-1003862859969'
BASE_URL = "https://dark-live-ss.onrender.com/?Pair=eurjpy"

bot = Bot(token=TOKEN)
app = FastAPI()

session_data = {"win": 0, "loss": 0, "mtg": 0, "status": "STOPPED", "pair": "EURJPY"}

# --- প্রিমিয়াম স্টাইল সিগন্যাল আউটপুট (আপনার দেওয়া স্ক্রিনশটের মতো) ---
def get_premium_caption(action, acc):
    now = datetime.datetime.now()
    trade_time = (now + datetime.timedelta(minutes=1)).strftime("%H:%M")
    
    return (
        f"✿° ━━━━━━━━━━━━━ ✿°\n"
        f"👑 <b>DARK-X-SNIPER V3.0</b> 👑\n"
        f"— — — — — — — — — — — —\n"
        f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
        f" <tg-emoji emoji-id='5472416843438246859'>📊</tg-emoji> <b>Pair:—</b> {session_data['pair']}\n"
        f" <tg-emoji emoji-id='6325717349257187998'>⌛</tg-emoji> <b>TimeFrame:—</b> M1\n"
        f" <tg-emoji emoji-id='5212985021870123409'>🚀</tg-emoji> <b>TradeTime:—</b> {trade_time}\n"
        f" <tg-emoji emoji-id='6264696987946324240'>🔋</tg-emoji> <b>Direction:—</b> {action}\n"
        f"┗━━━━━━━━━━━━━━━━━━━━┛\n"
        f"💎 <b>Payout:—</b> 87% 📈 <b>Trend:—</b> Bullish\n"
        f" • ────── ✾ ────── •\n"
        f"😈 <b>DARK-X-RAYHAN QUOTEX TRADING</b>"
    )

# --- সুপার ফাস্ট অটো ইঞ্জিন ---
async def auto_engine():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # ল্যাটেন্সি কমানোর জন্য অপ্টিমাইজড ব্রাউজার কন্টেক্সট
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        
        while session_data["status"] == "RUNNING":
            try:
                # পেজ লোড হওয়া পর্যন্ত অপেক্ষা
                await page.goto(BASE_URL, wait_until="networkidle")
                
                # স্ক্রিনশট এবং ক্যাপশন প্রসেসিং একসাথে (Zero Delay)
                ss_bytes = await page.screenshot(type='png')
                caption_text = get_premium_caption("CALL ⬆️", "98.5")
                
                # ফটো এবং টেক্সট ১টি রিকোয়েস্টে পাঠানো (এতে দেরি হয় না)
                await bot.send_photo(
                    chat_id=CHAT_ID,
                    photo=ss_bytes,
                    caption=caption_text,
                    parse_mode=ParseMode.HTML
                )
                
                await asyncio.sleep(60) # ক্যান্ডেল ক্লোজিং টাইম
            except Exception as e:
                print(f"Error: {e}")
                await asyncio.sleep(5)
        await browser.close()

# --- ওয়েব কন্ট্রোল প্যানেল ---
@app.get("/", response_class=HTMLResponse)
async def get_panel():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { background: #000; color: #fff; font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
            .container { background: #111; padding: 25px; border-radius: 25px; border: 1px solid #333; width: 300px; text-align: center; }
            .owner { color: #0f0; border: 1px solid #0f0; border-radius: 20px; padding: 5px 20px; font-size: 11px; margin-bottom: 15px; display: inline-block; }
            button { width: 100%; padding: 15px; margin: 6px 0; border: none; border-radius: 12px; font-weight: bold; cursor: pointer; color: #fff; }
            .btn-start { background: #2ecc71; } .btn-stop { background: #e74c3c; }
            .btn-win { background: #27ae60; width: 48%; float: left; }
            .btn-mtg { background: #f1c40f; width: 48%; float: right; color: #000; }
            .btn-loss { background: #c0392b; margin-top: 10px; }
            .btn-result { background: #3498db; margin-top: 15px; }
            .status { margin: 15px 0; font-weight: bold; color: red; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="owner">OWNER: DARK-X-RAYHAN</div>
            <div class="status" id="st">● STOPPED</div>
            <button class="btn-start" onclick="send('start')">START SNIPER</button>
            <button class="btn-stop" onclick="send('stop')">STOP SNIPER</button>
            <div style="margin: 15px 0; background: #1a1a1a; padding: 10px; border-radius: 10px; font-size: 12px; border-left: 3px solid #0f0;">
                PAIR: EURJPY | MODE: FAST AUTO
            </div>
            <div style="overflow: hidden;">
                <button class="btn-win" onclick="send('win')">WIN</button>
                <button class="btn-mtg" onclick="send('mtg')">MTG</button>
            </div>
            <button class="btn-loss" onclick="send('loss')">LOSS</button>
            <button class="btn-result" onclick="send('show_results')">🔥 SHOW FINAL RESULTS 🔥</button>
        </div>
        <script>
            async function send(cmd) {
                const s = document.getElementById('st');
                if(cmd === 'start') { s.style.color = '#0f0'; s.innerText = '● RUNNING'; }
                if(cmd === 'stop') { s.style.color = 'red'; s.innerText = '● STOPPED'; }
                await fetch(`/api/command?type=${cmd}`);
            }
        </script>
    </body>
    </html>
    """

@app.get("/api/command")
async def api_command(type: str):
    global session_data
    if type == "start" and session_data["status"] == "STOPPED":
        session_data["status"] = "RUNNING"
        asyncio.create_task(auto_engine())
    elif type == "stop":
        session_data["status"] = "STOPPED"
    elif type in ["win", "loss", "mtg"]:
        session_data[type] += 1
    elif type == "show_results":
        report = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 <b>FINAL SESSION REPORT</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ Wins: {session_data['win']}\n"
            f"❌ Loss: {session_data['loss']}\n"
            f"🔄 MTG: {session_data['mtg']}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👑 <b>Owner:</b> DARK-X-RAYHAN"
        )
        await bot.send_message(CHAT_ID, report, parse_mode=ParseMode.HTML)
        session_data.update({"win": 0, "loss": 0, "mtg": 0})
    return {"ok": True}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
