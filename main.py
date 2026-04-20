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
    "stats": {"win": 0, "loss": 0, "mtg": 0, "refund": 0},
    "current_ss": "",
    "history": [],
    "last_pair": "EURUSD"
}

def get_signal_logic(pair):
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=6)
    signal_time = (now + datetime.timedelta(minutes=1)).strftime("%H:%M")
    direction = "CALL" if (now.minute + len(pair)) % 2 == 0 else "PUT"
    return direction, signal_time

async def send_signal_task(pair):
    direction, signal_time = get_signal_logic(pair)
    state["last_pair"] = pair
    ss_url = f"https://dark-live-ss.onrender.com/?Pair={pair.lower()}"
    
    async with async_playwright() as p:
        browser = None
        current_price = "N/A" # Default if fetching fails
        try:
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--single-process'])
            context = await browser.new_context(viewport={'width': 1000, 'height': 600})
            page = await context.new_page()
            
            await page.goto(ss_url, wait_until="networkidle", timeout=90000)
            await asyncio.sleep(8) 

            # Current Price Fetching Logic from SS API
            try:
                # এখানে আপনার SS সাইটের প্রাইস এলিমেন্টটি খুঁজে বের করার চেষ্টা করবে
                # যদি আপনার সাইটে প্রাইসটি কোনো নির্দিষ্ট ক্লাস বা আইডিতে থাকে (যেমন: .price), তবে সেটি এখানে দিতে পারেন।
                # আপাতত আমি পেজ থেকে টেক্সট খুঁজে বের করার চেষ্টা করছি।
                current_price = await page.evaluate("() => document.body.innerText.match(/[0-9]+\.[0-9]+/)[0]")
            except:
                current_price = "Loading..."

            ss_bytes = await page.screenshot(type='png')
            state["current_ss"] = base64.b64encode(ss_bytes).decode('utf-8')
            
            # History update
            state["history"].append({"time": signal_time, "pair": pair, "dir": direction})

            if state["telegram_enabled"] and state["bot_token"]:
                bot = Bot(token=state["bot_token"])
                signal_msg = (
                    f"╔═━━━━━ ◥◣◆◢◤ ━━━━━═╗\n"
                    f"            PAIR        ➜ {pair}\n"
                    f"            TIME       ➜ {signal_time}\n"
                    f"            EXPIRE    ➜  M1\n"
                    f"            DIRECTION ➜ {direction}\n"
                    f"            PRICE     ➜ {current_price}\n"
                    f"╚═━━━━━ ◢◤◆◥◣ ━━━━━═╝\n\n"
                    f"📩 CONTRACT HERE : @mdrayhan85\n"
                    f"🚀 SIGNAL SEND SUCCESSFULLY"
                )
                await bot.send_photo(chat_id=state["chat_id"], photo=ss_bytes, caption=signal_msg, parse_mode=ParseMode.HTML)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if browser: await browser.close()

@app.get("/api/record")
async def record_stat(type: str):
    t = type.lower()
    if t in state["stats"]: 
        state["stats"][t] += 1
        if state["telegram_enabled"] and state["bot_token"]:
            bot = Bot(token=state["bot_token"])
            now = datetime.datetime.utcnow() + datetime.timedelta(hours=6)
            win_count = state["stats"]["win"]
            loss_count = state["stats"]["loss"]
            total = win_count + loss_count
            acc = (win_count/total*100) if total > 0 else 100
            
            res_msg = (
                f"========== 𝗥𝗘𝗦𝗨𝗟𝗧 ===========\n\n"
                f"╔═━━━━━ ◥◣◆◢◤ ━━━━━═╗\n"
                f"                 {state['last_pair']} ┃  {now.strftime('%H:%M')}\n"
                f"╚═━━━━━ ◢◤◆◥◣ ━━━━━═╝\n"
                f"       {t.upper()} {'✅' if t=='win' else '❌'}\n"
                f"╔═━━━━━ ◥◣◆◢◤ ━━━━━═╗\n"
                f"           Win: {win_count} | ️Loss: {loss_count}\n"
                f"           Current Pair: {win_count}x{loss_count}⋅({acc:.0f}%)\n"
                f"╚═━━━━━ ◢◤◆◥◣ ━━━━━═╝\n\n"
                f"🔗 TELEGRAM CLICK HERE\n"
                f"✅ RESULT SEND SUCCESSFULLY"
            )
            asyncio.create_task(bot.send_message(state["chat_id"], res_msg, parse_mode=ParseMode.HTML))
    return {"ok": True}

@app.get("/api/final_report")
async def final_report():
    if state["telegram_enabled"] and state["bot_token"]:
        bot = Bot(token=state["bot_token"])
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=6)
        s = state["stats"]
        total = s['win'] + s['loss']
        acc = (s['win']/total*100) if total > 0 else 0
        
        history_text = ""
        for h in state["history"][-10:]:
            history_text += f"〄 {h['time']} - {h['pair']} - {h['dir']}\n"

        report = (
            f"=========== 𝗣𝗔𝗥𝗧𝗜𝗔𝗟 ============\n\n"
            f"━━━━━━━━━・━━━━━━━━━\n"
            f"                  - {now.strftime('%d.%m.%Y')}\n"
            f"━━━━━━━━━・━━━━━━━━━\n"
            f"                  TOTAL : {total}\n"
            f"━━━━━━━━━・━━━━━━━━━\n"
            f"                  REAL-MARKET\n"
            f"━━━━━━━━━・━━━━━━━━━\n"
            f"{history_text}"
            f"━━━━━━━━━・━━━━━━━━━\n"
            f" 🧩 PLACER : {s['win']} x {s['loss']} ⋅◈⋅ ({acc:.0f}%)\n"
            f"━━━━━━━━━━・━━━━━━━━━\n"
            f"🏆 WIN : {s['win']} ┃ LOSS : {s['loss']} ┃ ⋅◈⋅ ({acc:.0f}%)\n"
            f"━━━━━━━━━・━━━━━━━━━\n\n"
            f"✅ PARTIAL SEND SUCCESSFULLY"
        )
        asyncio.create_task(bot.send_message(state["chat_id"], report, parse_mode=ParseMode.HTML))
    return {"ok": True}

# UI elements and backend loops remain unchanged for stability
@app.get("/", response_class=HTMLResponse)
async def main_ui():
    pair_options = "".join([f'<option value="{p}">{p}</option>' for p in ALL_PAIRS])
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DARK-X-PRO V10</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body {{ background: #0b0e14; color: #fff; font-family: sans-serif; }}
            .glow-card {{ background: #151a21; border: 1px solid #2d3748; border-radius: 12px; padding: 15px; margin-bottom: 15px; }}
            .btn-action {{ background: #2563eb; color: white; font-weight: bold; padding: 12px; border-radius: 8px; width: 100%; font-size: 11px; }}
        </style>
    </head>
    <body class="p-4">
        <div class="glow-card">
            <div class="flex gap-2 mb-2">
                <button id="auto-btn" onclick="toggleAuto()" class="flex-1 p-4 bg-slate-800 rounded-xl font-bold text-[10px]">🚀 AUTO: OFF</button>
                <select id="pair-select" class="flex-1 p-4 bg-slate-900 rounded-xl font-bold text-[10px] border border-slate-700 outline-none uppercase">
                    {pair_options}
                </select>
            </div>
            <button onclick="manualGenerate()" class="w-full p-4 bg-yellow-500 text-black font-bold text-[12px] rounded-xl uppercase">Generate Signal</button>
        </div>
        <div class="glow-card">
            <div id="chart-box" class="w-full aspect-video bg-black rounded-lg flex items-center justify-center border border-slate-800 text-[10px] text-slate-700 italic">Live Preview Area</div>
        </div>
        <div class="glow-card grid grid-cols-2 gap-3">
            <button onclick="record('win')" class="btn-action">✓ WIN</button>
            <button onclick="record('loss')" class="btn-action">✗ LOSS</button>
            <button onclick="record('mtg')" class="btn-action">⇄ MTG</button>
            <button onclick="record('refund')" class="btn-action bg-slate-700">↺ REFUND</button>
            <button onclick="sendReport()" class="col-span-2 p-3 bg-yellow-500 text-black font-bold rounded-lg text-[10px] uppercase">Send Partial Report</button>
        </div>
        <script>
            async function record(type) {{ await fetch(`/api/record?type=${{type}}`); }}
            async function sendReport() {{ await fetch('/api/final_report'); }}
            async function toggleAuto() {{
                const res = await fetch('/api/toggle_auto');
                const d = await res.json();
                document.getElementById('auto-btn').innerText = d.active ? "🚀 AUTO: ON" : "🚀 AUTO: OFF";
            }}
            async function manualGenerate() {{
                const p = document.getElementById('pair-select').value;
                await fetch(`/api/manual?pair=${{p}}`);
            }}
            async function updateStats() {{
                const r = await fetch('/api/get_state');
                const d = await r.json();
                if(d.current_ss) document.getElementById('chart-box').innerHTML = `<img src="data:image/png;base64,${{d.current_ss}}" class="w-full rounded-lg">`;
            }}
            setInterval(updateStats, 5000);
        </script>
    </body>
    </html>
    """

@app.get("/api/toggle_auto")
async def toggle_auto(): state["auto_scan_active"] = not state["auto_scan_active"]; return {"active": state["auto_scan_active"]}
@app.get("/api/manual")
async def manual_signal(pair: str): asyncio.create_task(send_signal_task(pair.upper())); return {"ok": True}
@app.get("/api/get_state")
async def get_state(): return state

async def auto_scan_loop():
    while True:
        if state["auto_scan_active"]:
            await send_signal_task(random.choice(ALL_PAIRS))
            await asyncio.sleep(120)
        else: await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event(): asyncio.create_task(auto_scan_loop())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
