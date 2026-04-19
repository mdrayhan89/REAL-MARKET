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

# --- কনফিগারেশন ---
config = {
    "bot_token": "8354111202:AAEqFLMoJ7W7AlwpfHibZbpusiWbnOcl5Xc",
    "chat_id": "-1003862859969",
    "owner_tg": "@mdrayhan89"
}

ALL_PAIRS = ["XAUUSD", "EURJPY", "NZDUSD", "EURUSD", "GBPUSD", "AUDUSD", "USDCAD", "USDJPY", "EURGBP", "AUDJPY", "CADJPY"]
stats = {"win": 0, "loss": 0, "mtg": 0, "refund": 0}
report_list = [] # একটার পর একটা রেজাল্ট সেভ করার জন্য
current_screenshot = "" # লাইভ চার্ট প্রিভিউয়ের জন্য

async def capture_signal_ss(pair):
    global current_screenshot
    ss_url = f"https://dark-live-ss.onrender.com/?Pair={pair.lower()}"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(ss_url, wait_until="networkidle")
            ss_bytes = await page.screenshot()
            # বেস-৬৪ এ কনভার্ট করে প্যানেলে দেখানোর জন্য
            current_screenshot = base64.b64encode(ss_bytes).decode('utf-8')
            return ss_bytes
        finally: await browser.close()

async def process_signal(pair):
    now = datetime.datetime.now().strftime("%H:%M")
    direction = random.choice(["CALL ⬆️", "PUT ⬇️"])
    
    # ১ সেকেন্ডও দেরি না করে স্ক্রিনশট নেওয়া
    ss_data = await capture_signal_ss(pair)
    
    caption = f"👑 <b>DARK-X-PRO</b>\n━━━━━━━━━━━━\n📊 <b>Pair:</b> {pair}\n🔋 <b>Direction:</b> {direction}\n🎯 <b>Time:</b> {now}"
    bot = Bot(token=config["bot_token"])
    await bot.send_photo(chat_id=config["chat_id"], photo=ss_data, caption=caption, parse_mode=ParseMode.HTML)

@app.get("/", response_class=HTMLResponse)
async def main_ui():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DARK-X-PRO | ADVANCED SNIPER</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body { background: #0b0e14; color: #fff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            .glow-card { background: #151a21; border: 1px solid #2d3748; border-radius: 15px; padding: 15px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
            .btn-blue { background: #2563eb; color: white; }
            .btn-green { background: #10b981; }
            .btn-red { background: #ef4444; }
            .btn-yellow { background: #f59e0b; color: black; }
            .nav-active { color: #3b82f6; border-top: 2px solid #3b82f6; }
        </style>
    </head>
    <body class="pb-24 p-4">
        
        <div id="home-tab" class="tab-page">
            <div class="glow-card">
                <select id="pair-select" class="w-full p-4 bg-slate-900 rounded-xl mb-4 border border-slate-700 font-bold">
                    <option value="XAUUSD">XAUUSD (GOLD)</option>
                    <option value="EURJPY">EURJPY</option>
                    <option value="NZDUSD">NZDUSD</option>
                    <option value="AUTO">AUTO (EMA STRATEGY)</option>
                </select>
                <button onclick="generateSignal()" id="gen-btn" class="w-full p-4 btn-yellow rounded-xl font-black uppercase shadow-lg">Generate & Send</button>
            </div>

            <div class="glow-card">
                <h3 class="text-[10px] font-bold text-blue-400 uppercase mb-3 tracking-tighter">Record Result</h3>
                <div class="grid grid-cols-2 gap-2">
                    <button onclick="record('win')" class="p-3 btn-blue rounded-lg text-xs font-bold uppercase">✓ Win</button>
                    <button onclick="record('loss')" class="p-3 btn-blue rounded-lg text-xs font-bold uppercase">✕ Loss</button>
                    <button onclick="record('mtg')" class="p-3 btn-blue rounded-lg text-xs font-bold uppercase">⇄ MTG</button>
                    <button onclick="record('refund')" class="p-3 btn-blue rounded-lg text-xs font-bold uppercase">↺ Refund</button>
                </div>
            </div>

            <div class="glow-card">
                <h3 class="text-[10px] font-bold text-blue-400 uppercase mb-3 tracking-tighter"><i class="fas fa-chart-line mr-1"></i> Live Chart Preview (API)</h3>
                <div id="chart-container" class="w-full aspect-video bg-slate-900 rounded-lg flex items-center justify-center overflow-hidden border border-slate-800">
                    <p class="text-slate-600 text-xs italic">No chart loaded. Generate a signal.</p>
                </div>
            </div>

            <div class="glow-card">
                <div class="flex justify-between items-center mb-3">
                    <h3 class="text-[10px] font-bold text-blue-400 uppercase tracking-tighter">Full Trading Report</h3>
                    <button onclick="clearReport()" class="text-[10px] bg-red-600 px-2 py-1 rounded font-bold uppercase">Clear All</button>
                </div>
                <div id="report-box" class="bg-slate-900 p-4 rounded-lg min-h-[100px] text-[11px] font-mono border border-slate-800 mb-4 whitespace-pre-wrap">No results yet.</div>
                <button onclick="sendFinalReport()" class="w-full p-3 btn-blue rounded-xl font-bold uppercase mb-2">Send Report</button>
                <button class="w-full p-3 btn-yellow rounded-xl font-bold uppercase text-xs">Export as PDF</button>
            </div>
        </div>

        <nav class="fixed bottom-0 left-0 right-0 bg-[#151a21] border-t border-slate-800 flex justify-around p-4 z-50">
            <button class="nav-active flex flex-col items-center"><i class="fas fa-home"></i><span class="text-[8px] mt-1">HOME</span></button>
            <button class="text-slate-500 flex flex-col items-center"><i class="fas fa-history"></i><span class="text-[8px] mt-1">HISTORY</span></button>
            <button class="text-slate-500 flex flex-col items-center"><i class="fas fa-cog"></i><span class="text-[8px] mt-1">SETTINGS</span></button>
            <button class="text-slate-500 flex flex-col items-center"><i class="fas fa-user"></i><span class="text-[8px] mt-1">PROFILE</span></button>
        </nav>

        <script>
            async function generateSignal() {
                const pair = document.getElementById('pair-select').value;
                const btn = document.getElementById('gen-btn');
                btn.disabled = true; btn.innerText = "Processing...";
                await fetch(`/api/signal?pair=${pair}`);
                
                // ১ সেকেন্ড পরপর চেক করবে স্ক্রিনশট রেডি কি না
                const checkInterval = setInterval(async () => {
                    const res = await fetch('/api/get_ss');
                    const data = await res.json();
                    if(data.ss) {
                        document.getElementById('chart-container').innerHTML = `<img src="data:image/png;base64,${data.ss}" class="w-full h-full object-cover">`;
                        btn.disabled = false; btn.innerText = "Generate & Send";
                        clearInterval(checkInterval);
                    }
                }, 1000);
            }

            async function record(type) {
                const pair = document.getElementById('pair-select').value;
                const res = await fetch(`/api/record?type=${type}&pair=${pair}`);
                const data = await res.json();
                document.getElementById('report-box').innerText = data.history.join('\\n');
            }

            async function clearReport() {
                await fetch('/api/clear');
                document.getElementById('report-box').innerText = "No results yet.";
            }

            async function sendFinalReport() {
                await fetch('/api/report');
                alert('Report Sent Successfully!');
            }
        </script>
    </body>
    </html>
    """

# --- API সিস্টেম ---
@app.get("/api/signal")
async def api_signal(pair: str):
    asyncio.create_task(process_signal(pair))
    return {"status": "started"}

@app.get("/api/get_ss")
async def get_ss(): return {"ss": current_screenshot}

@app.get("/api/record")
async def api_record(type: str, pair: str):
    global stats, report_list
    if type in stats: stats[type] += 1
    
    emoji = {"win": "✅", "loss": "❌", "mtg": "🔄", "refund": "↺"}
    now = datetime.datetime.now().strftime("%H:%M")
    # একটার পর একটা সেভ হবে
    entry = f"{emoji.get(type, '')} {pair} -> {type.upper()} ({now})"
    report_list.append(entry)
    return {"status": "ok", "history": report_list}

@app.get("/api/clear")
async def api_clear():
    global report_list, stats
    report_list = []
    stats = {k: 0 for k in stats}
    return {"status": "cleared"}

@app.get("/api/report")
async def api_report():
    # ছবির মতো রিপোর্ট ফরম্যাট
    report_text = (
        f"📊 <b>FINAL SESSION REPORT</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"✅ <b>Wins:</b> {stats['win']}\n"
        f"❌ <b>Loss:</b> {stats['loss']}\n"
        f"🔄 <b>MTG:</b> {stats['mtg']}\n"
        f"↺ <b>Refund:</b> {stats['refund']}\n"
        f"━━━━━━━━━━━━━━\n"
        f"👑 <b>Owner:</b> {config['owner_tg']}"
    )
    bot = Bot(token=config["bot_token"])
    await bot.send_message(config["chat_id"], report_text, parse_mode=ParseMode.HTML)
    return {"status": "sent"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
