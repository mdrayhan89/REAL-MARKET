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
    "premium_key": "DARK-X-RAYHAN",
    "stats": {"win": 0, "loss": 0, "mtg": 0, "refund": 0},
    "current_ss": "",
    "history": [],
    "last_pair": "EURUSD",
    "user_role": "FREE USER"
}

def get_signal_logic(pair):
    # UTC +6 (Bangladesh Time)
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=6)
    signal_time = (now + datetime.timedelta(minutes=1)).strftime("%H:%M")
    
    accuracy = 96 + (now.minute % 4) 
    direction = "CALL" if (now.minute + len(pair)) % 2 == 0 else "PUT"
    strategies = ["EMA Cross", "Price Action", "Bollinger Break", "Support Zone", "RSI Reverse"]
    strat = strategies[now.minute % 5]
    return direction, accuracy, strat, signal_time

async def send_signal_task(pair):
    direction, accuracy, strategy, signal_time = get_signal_logic(pair)
    state["last_pair"] = pair
    ss_url = f"https://dark-live-ss.onrender.com/?Pair={pair.lower()}"
    
    # Store for Report
    state["history"].append({"time": signal_time, "pair": pair, "dir": direction})
    
    async with async_playwright() as p:
        browser = None
        current_price = "N/A"
        try:
            # SS Fix: Optimized for Render/Linux
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--single-process'])
            context = await browser.new_context(viewport={'width': 1000, 'height': 600})
            page = await context.new_page()
            
            await page.goto(ss_url, wait_until="networkidle", timeout=90000)
            await asyncio.sleep(8) 

            # Price Fetching from Page
            try:
                current_price = await page.evaluate("() => document.body.innerText.match(/[0-9]+\.[0-9]+/)[0]")
            except:
                current_price = "N/A"

            ss_bytes = await page.screenshot(type='png')
            state["current_ss"] = base64.b64encode(ss_bytes).decode('utf-8')
            
            if state["telegram_enabled"] and state["bot_token"]:
                bot = Bot(token=state["bot_token"])
                # Your requested Signal Output
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
            print(f"SS Error: {e}")
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
            
            # Your requested Result Output
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

        # Your requested Partial/Final Report Output
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
            f"━━━━━━━━━・━━━━━━━━━\n"
            f"🏆 WIN : {s['win']} ┃ LOSS : {s['loss']} ┃ ⋅◈⋅ ({acc:.0f}%)\n"
            f"━━━━━━━━━・━━━━━━━━━\n\n"
            f"✅ PARTIAL SEND SUCCESSFULLY"
        )
        asyncio.create_task(bot.send_message(state["chat_id"], report, parse_mode=ParseMode.HTML))
    return {"ok": True}

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
            .hidden {{ display: none; }}
        </style>
    </head>
    <body class="pb-24 p-4">
        <div id="auth-screen" class="fixed inset-0 z-[100] bg-[#0b0e14] flex flex-col items-center justify-center p-6 text-center">
            <h1 class="text-3xl font-black mb-10 text-blue-500 italic">DARK-X-PRO</h1>
            <button onclick="doLogin('FREE USER')" class="w-full max-w-xs p-4 bg-slate-800 rounded-xl font-bold mb-4 border border-slate-700">👤 FREE USER ACCESS</button>
            <div class="w-full max-w-xs p-1 bg-slate-900 rounded-xl mb-4 border border-slate-800">
                <input id="key-input" type="password" placeholder="Enter Premium Key" class="w-full p-3 bg-transparent text-center outline-none">
            </div>
            <button onclick="doLogin('PREMIUM')" class="w-full max-w-xs p-4 bg-blue-600 rounded-xl font-bold">💎 UNLOCK PREMIUM</button>
        </div>

        <div id="main-content" class="hidden">
            <div id="home-tab" class="tab-page">
                <div class="glow-card">
                    <div class="flex flex-col gap-2">
                        <div class="flex gap-2">
                            <button id="auto-btn" onclick="toggleAuto()" class="flex-1 p-4 bg-slate-800 rounded-xl font-bold text-[10px] uppercase">🚀 AUTO: OFF</button>
                            <select id="pair-select" class="flex-1 p-4 bg-slate-900 rounded-xl font-bold text-[10px] border border-slate-700 outline-none uppercase uppercase">
                                {pair_options}
                            </select>
                        </div>
                        <button id="gen-btn" onclick="manualGenerate()" class="w-full p-4 bg-yellow-500 text-black font-bold text-[12px] rounded-xl uppercase">Generate Signal</button>
                    </div>
                </div>
                <div class="glow-card">
                    <div id="chart-box" class="w-full aspect-video bg-black rounded-lg flex items-center justify-center border border-slate-800 text-[10px] text-slate-700 italic">Live Preview Area</div>
                </div>
                <div class="glow-card grid grid-cols-2 gap-3">
                    <button onclick="record('win')" class="btn-action">✓ WIN</button>
                    <button onclick="record('loss')" class="btn-action">✗ LOSS</button>
                    <button onclick="record('mtg')" class="btn-action">⇄ MTG</button>
                    <button onclick="record('refund')" class="btn-action bg-slate-700">↺ REFUND</button>
                    <button onclick="sendReport()" class="col-span-2 p-3 bg-yellow-500 text-black font-bold rounded-lg text-[10px] uppercase">Send Final Report</button>
                </div>
            </div>

            <div id="history-tab" class="tab-page hidden">
                <div class="glow-card"><h3 class="text-blue-500 font-bold mb-4 text-xs uppercase">Signal History</h3><div id="hist-list" class="space-y-3 text-[11px]"></div></div>
            </div>
            <div id="profile-tab" class="tab-page hidden text-center py-10">
                <h2 class="font-bold text-xl uppercase">Dark-X-Rayhan</h2>
                <div id="display-role" class="text-blue-500 font-bold text-[10px] mb-8 uppercase tracking-widest">FREE USER</div>
                <div class="grid grid-cols-4 gap-2 px-1">
                    <div class="bg-slate-800 p-2 rounded-lg"><p class="text-lg font-black" id="p-win">0</p><p class="text-[8px]">WIN</p></div>
                    <div class="bg-slate-800 p-2 rounded-lg"><p class="text-lg font-black" id="p-loss">0</p><p class="text-[8px]">LOSS</p></div>
                    <div class="bg-slate-800 p-2 rounded-lg"><p class="text-lg font-black" id="p-mtg">0</p><p class="text-[8px]">MTG</p></div>
                    <div class="bg-slate-800 p-2 rounded-lg"><p class="text-lg font-black" id="p-ref">0</p><p class="text-[8px]">REF</p></div>
                </div>
            </div>
            <div id="settings-tab" class="tab-page hidden">
                <div class="glow-card">
                    <input id="bot-token" type="text" class="w-full p-4 bg-slate-900 border border-slate-800 rounded-xl mb-4 text-xs" value="{state['bot_token']}" onchange="saveConfig()">
                    <input id="chat-id" type="text" class="w-full p-4 bg-slate-900 border border-slate-800 rounded-xl text-xs" value="{state['chat_id']}" onchange="saveConfig()">
                </div>
            </div>
        </div>

        <nav class="fixed bottom-0 left-0 right-0 bg-[#151a21] border-t border-slate-800 flex justify-around p-3 z-[100]">
            <button onclick="switchTab('home')" class="flex flex-col items-center text-[9px] uppercase"><i class="fas fa-home text-lg mb-1"></i>HOME</button>
            <button onclick="switchTab('history')" class="flex flex-col items-center text-[9px] uppercase"><i class="fas fa-history text-lg mb-1"></i>HISTORY</button>
            <button onclick="switchTab('settings')" class="flex flex-col items-center text-[9px] uppercase"><i class="fas fa-cog text-lg mb-1"></i>SETTING</button>
            <button onclick="switchTab('profile')" class="flex flex-col items-center text-[9px] uppercase"><i class="fas fa-user text-lg mb-1"></i>PROFILE</button>
        </nav>

        <script>
            async function saveConfig() {{
                const token = document.getElementById('bot-token').value;
                const chat = document.getElementById('chat-id').value;
                await fetch(`/api/update_config?token=${{token}}&chat=${{chat}}`);
            }}
            async function record(type) {{ await fetch(`/api/record?type=${{type}}`); updateStats(); }}
            async function sendReport() {{ await fetch('/api/final_report'); }}
            async function doLogin(role) {{
                if(role === 'PREMIUM' && document.getElementById('key-input').value !== 'DARK-X-RAYHAN') return alert('Invalid Key!');
                document.getElementById('auth-screen').classList.add('hidden');
                document.getElementById('main-content').classList.remove('hidden');
                document.getElementById('display-role').innerText = role === 'PREMIUM' ? '💎 PREMIUM USER' : '👤 FREE USER';
                await fetch(`/api/set_role?role=${{role}}`);
            }}
            function switchTab(t) {{
                document.querySelectorAll('.tab-page').forEach(p => p.classList.add('hidden'));
                document.getElementById(t + '-tab').classList.remove('hidden');
            }}
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
                document.getElementById('p-win').innerText = d.stats.win;
                document.getElementById('p-loss').innerText = d.stats.loss;
                document.getElementById('p-mtg').innerText = d.stats.mtg;
                document.getElementById('p-ref').innerText = d.stats.refund;
                if(d.current_ss) document.getElementById('chart-box').innerHTML = `<img src="data:image/png;base64,${{d.current_ss}}" class="w-full rounded-lg">`;
            }}
            setInterval(updateStats, 5000);
        </script>
    </body>
    </html>
    """

# API handlers
@app.get("/api/update_config")
async def update_config(token: str, chat: str): state["bot_token"], state["chat_id"] = token, chat; return {"ok": True}
@app.get("/api/set_role")
async def set_role(role: str): state["user_role"] = role; return {"ok": True}
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
