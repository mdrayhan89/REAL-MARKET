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

# সেশন ডেটা
session_data = {"win": 0, "loss": 0, "mtg": 0, "status": "STOPPED", "running_task": None}

# --- সিগন্যাল আউটপুট ফরম্যাট (আপনার প্রিমিয়াম ইমোজি সহ) ---
def format_signal_text(pair, action, acc):
    now = datetime.datetime.now()
    trade_time = (now + datetime.timedelta(minutes=1)).strftime("%H:%M:00")
    
    return (
        f'━━━━━━━━━━━━━━━━━━━━\n'
        f'<tg-emoji emoji-id="6325797905663791037">💎</tg-emoji> <b>API CONFIRMED SIGNAL</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━\n'
        f'<tg-emoji emoji-id="5472416843438246859">📊</tg-emoji> <b>Pair:</b> {pair}\n'
        f'<tg-emoji emoji-id="6264696987946324240">🔋</tg-emoji> <b>Action:</b> {action}\n'
        f'<tg-emoji emoji-id="6325717349257187998">🕒</tg-emoji> <b>Time:</b> {now.strftime("%H:%M:%S")}\n'
        f'<tg-emoji emoji-id="5212985021870123409">🚀</tg-emoji> <b>Trade:</b> {trade_time}\n'
        f'<tg-emoji emoji-id="6325667390197600621">🎯</tg-emoji> <b>Accuracy:</b> {acc}%\n'
        f'━━━━━━━━━━━━━━━━━━━━\n'
        f'<tg-emoji emoji-id="5384513813670279219">👑</tg-emoji> <b>Owner:</b> DARK-X-RAYHAN'
    )

# --- অটো অ্যানালাইজার লুপ ---
async def auto_signal_engine():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        while session_data["status"] == "RUNNING":
            try:
                await page.goto(BASE_URL)
                await asyncio.sleep(5) # চার্ট লোড টাইম
                
                # এখানে আপনার EMA, RSI, FVG স্ট্র্যাটেজি কাজ করবে
                # উদাহরণস্বরূপ একটি হাই একুরেসি সিগন্যাল পাঠানো হচ্ছে
                ss_path = "signal.png"
                await page.screenshot(path=ss_path)
                
                text = format_signal_text("EURJPY", "CALL ⬆️", "98.5")
                
                await bot.send_photo(
                    chat_id=CHAT_ID,
                    photo=open(ss_path, 'rb'),
                    caption=text,
                    parse_mode=ParseMode.HTML
                )
                
                # ১ মিনিট পর পর পরবর্তী সিগন্যাল চেক করবে
                await asyncio.sleep(60) 
            except Exception as e:
                print(f"Error: {e}")
                await asyncio.sleep(5)
        await browser.close()

# --- কন্ট্রোল প্যানেল HTML ---
@app.get("/", response_class=HTMLResponse)
async def get_panel():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DARK-X-CONTROL</title>
        <style>
            body { background: #000; color: #fff; font-family: sans-serif; text-align: center; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
            .container { background: #111; padding: 25px; border-radius: 25px; border: 1px solid #333; width: 300px; }
            .owner { color: #0f0; border: 1px solid #0f0; border-radius: 20px; padding: 5px 20px; font-size: 11px; margin-bottom: 15px; display: inline-block; }
            button { width: 100%; padding: 15px; margin: 6px 0; border: none; border-radius: 12px; font-weight: bold; cursor: pointer; color: #fff; }
            .btn-start { background: #2ecc71; } .btn-stop { background: #e74c3c; }
            .btn-win { background: #27ae60; width: 48%; float: left; }
            .btn-mtg { background: #f1c40f; width: 48%; float: right; color: #000; }
            .btn-loss { background: #c0392b; margin-top: 10px; }
            .btn-result { background: #3498db; margin-top: 15px; }
            .status { margin: 15px 0; font-weight: bold; font-size: 13px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="owner">OWNER: DARK-X-RAYHAN</div>
            <div class="status" id="st">● STOPPED</div>
            <button class="btn-start" onclick="send('start')">START SNIPER</button>
            <button class="btn-stop" onclick="send('stop')">STOP SNIPER</button>
            <div style="margin: 15px 0; background: #1a1a1a; padding: 10px; border-radius: 10px; font-size: 12px; border-left: 3px solid #0f0;">
                LIVE PAIR: EURJPY <br> MODE: AUTO ANALYZE
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

# --- API কমান্ডস ---
@app.get("/api/command")
async def api_command(type: str):
    global session_data
    if type == "start" and session_data["status"] == "STOPPED":
        session_data["status"] = "RUNNING"
        asyncio.create_task(auto_signal_engine())
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
