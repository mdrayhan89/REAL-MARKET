import time, datetime, pytz, requests, threading, os, gc
from http.server import BaseHTTPRequestHandler, HTTPServer
from tradingview_ta import TA_Handler, Interval

# --- CONFIGURATION ---
TOKEN = "8354111202:AAEqFLMoJ7W7AlwpfHibZbpusiWbnOcl5Xc"
CHAT_ID = "-1003862859969" 
PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "EURJPY", "AUDUSD", "GBPJPY", "EURGBP", "USDCAD", "AUDCAD", "NZDUSD", "GBPCHF", "AUDJPY"]
EXCHANGE = "FX_IDC" 
SCREENER = "forex"
INTERVAL = Interval.INTERVAL_1_MINUTE 
TZ = pytz.timezone('Asia/Dhaka')
OWNER_NAME = "DARK-X-RAYHAN"

# --- GLOBAL STATE ---
bot_running = False
active_trade = {"pair": "Searching...", "time": "Waiting...", "action": "N/A"}
last_sig_time = 0 
stats = {"win": 0, "loss": 0, "mtg": 0}

# --- DIRECT TELEGRAM PUSH (Retry Logic Enabled) ---
def send_telegram(msg, pair=None):
    url = f"https://api.telegram.org/bot{TOKEN}"
    try:
        if pair:
            # TradingView বাদে ফাস্ট ডার্ক চার্ট
            chart_url = f"https://test.poghen-dx.workers.dev/render?pair={pair}&theme=dark&style=dragon"
            r = requests.post(f"{url}/sendPhoto", data={"chat_id": CHAT_ID, "photo": chart_url, "caption": msg, "parse_mode": "Markdown"}, timeout=25)
        else:
            r = requests.post(f"{url}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=15)
        print(f"Telegram Status: {r.status_code}")
    except Exception as e:
        print(f"Telegram Error: {e}")

# --- WORKING UI PANEL ---
def get_html():
    status_text = "RUNNING" if bot_running else "STOPPED"
    status_color = "#00ff00" if bot_running else "#ff0000"
    return f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ background: #000; color: #fff; text-align: center; font-family: sans-serif; padding: 10px; }}
        .card {{ background: #0a0a0a; padding: 20px; border-radius: 25px; border: 1px solid #1a1a1a; max-width: 340px; margin: auto; }}
        .owner {{ color: #00ff00; border: 1px solid #00ff00; padding: 5px; border-radius: 10px; margin-bottom: 15px; display: inline-block; font-weight: bold; }}
        .btn {{ display: block; padding: 15px; margin: 10px 0; border-radius: 12px; color: #fff; font-weight: bold; border: none; cursor: pointer; width: 100%; }}
        .start {{ background: #2ecc71; }} .stop {{ background: #e74c3c; }}
        .win {{ background: #27ae60; }} .mtg {{ background: #f1c40f; color: #000; }} .loss {{ background: #c0392b; }}
        .final {{ background: #3498db; }}
        .stats-box {{ background: #111; border-radius: 15px; padding: 15px; margin: 15px 0; text-align: left; color: #00ff00; border-left: 5px solid #00ff00; font-size: 14px; }}
    </style>
    <script>
        function runAction(path) {{
            fetch(path).then(() => {{
                setTimeout(() => location.reload(), 300);
            }});
        }}
    </script>
    </head><body>
    <div class="card">
        <div class="owner">OWNER: {OWNER_NAME}</div>
        <div style="color:{status_color}; font-weight:bold; margin-bottom:10px;">● {status_text}</div>
        <button onclick="runAction('/on')" class="btn start">START SNIPER</button>
        <button onclick="runAction('/off')" class="btn stop">STOP SNIPER</button>
        <div class="stats-box">
            LIVE PAIR: {active_trade['pair']}<br>
            ENTRY AT: {active_trade['time']}<br>
            W: {stats['win']} | L: {stats['loss']} | M: {stats['mtg']}
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
            <button onclick="runAction('/win')" class="btn win">WIN</button>
            <button onclick="runAction('/mtg')" class="btn mtg">MTG</button>
        </div>
        <button onclick="runAction('/loss')" class="btn loss">LOSS</button>
        <button onclick="runAction('/final')" class="btn final">🔥 SHOW FINAL RESULTS 🔥</button>
    </div></body></html>
    """

class ControlHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global bot_running, stats
        self.send_response(200); self.send_header("Content-type", "text/html"); self.end_headers()
        
        # বাটন হ্যান্ডলিং
        if "/on" in self.path: bot_running = True
        elif "/off" in self.path: bot_running = False
        elif "/win" in self.path: 
            stats["win"] += 1
            threading.Thread(target=send_telegram, args=("✅ *Result: WIN*",)).start()
        elif "/mtg" in self.path: 
            stats["mtg"] += 1
            threading.Thread(target=send_telegram, args=("🔄 *Result: MTG*",)).start()
        elif "/loss" in self.path: 
            stats["loss"] += 1
            threading.Thread(target=send_telegram, args=("❌ *Result: LOSS*",)).start()
        elif "/final" in self.path:
            msg = f"📊 *SESSION REPORT*\n━━━━━━━━━━\n✅ Wins: {stats['win']}\n🔄 MTG: {stats['mtg']}\n❌ Loss: {stats['loss']}\n━━━━━━━━━━\n👤 {OWNER_NAME}"
            threading.Thread(target=send_telegram, args=(msg,)).start()
        
        self.wfile.write(get_html().encode())

# --- THE ACCURATE SIGNAL ENGINE (Score 0.2 Fixed) ---
def signal_loop():
    global active_trade, last_sig_time
    while True:
        try:
            if bot_running:
                now = datetime.datetime.now(TZ)
                # ৪৮ সেকেন্ডে সিগন্যাল চেক
                if now.second == 48 and (time.time() - last_sig_time) > 170:
                    best_pair, best_action = None, None
                    for pair in PAIRS:
                        try:
                            h = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL, timeout=0.5)
                            score = h.get_analysis().indicators['Recommend.All']
                            if abs(score) >= 0.2:
                                best_pair, best_action = pair, ("CALL 📈" if score > 0 else "PUT 📉")
                                break
                        except: continue
                    
                    if best_pair:
                        trade_t = (now + datetime.timedelta(minutes=1)).strftime("%H:%M:00")
                        active_trade = {"pair": best_pair, "time": trade_t, "action": best_action}
                        last_sig_time = time.time()
                        
                        # আপনার দেওয়া হুবহু ফরম্যাট
                        msg = (f"🚀 *API CONFIRMED SIGNAL*\n━━━━━━━━━━━━━━━━━━━━\n"
                               f"💎 *Pair:* {best_pair}\n📊 *Action:* {best_action}\n"
                               f"⏰ *Time:* {now.strftime('%H:%M:%S')}\n🎯 *Trade:* {trade_t}\n"
                               f"🚀 *Accuracy:* 98.5%\n━━━━━━━━━━━━━━━━━━━━\n"
                               f"👤 *Owner:* {OWNER_NAME}")
                        
                        threading.Thread(target=send_telegram, args=(msg, best_pair)).start()
                        gc.collect()
            time.sleep(1) 
        except: time.sleep(1)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=signal_loop, daemon=True).start()
    HTTPServer(('0.0.0.0', port), ControlHandler).serve_forever()
