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
stats = {"win": 0, "loss": 0}
session = requests.Session()

# --- FAST DISPATCH ENGINE ---
def send_telegram(msg, pair=None):
    base_url = f"https://api.telegram.org/bot{TOKEN}"
    try:
        if pair:
            chart_url = f"https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.html?symbol={EXCHANGE}:{pair}&width=1000&height=600&colorTheme=dark"
            photo_url = f"https://image.thum.io/get/width/1000/crop/600/noanimate/refresh/{int(time.time())}/{chart_url}"
            payload = {"chat_id": CHAT_ID, "photo": photo_url, "caption": msg, "parse_mode": "Markdown"}
            r = session.post(f"{base_url}/sendPhoto", data=payload, timeout=25)
            if r.status_code != 200:
                session.post(f"{base_url}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        else:
            session.post(f"{base_url}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=15)
    except: pass

# --- ORIGINAL DARK UI (Back to Basics) ---
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
        .stats {{ background: #111; border-radius: 15px; padding: 15px; margin: 15px 0; text-align: left; color: #00ff00; border-left: 5px solid #00ff00; }}
    </style>
    <script> function callBot(path) {{ fetch(path).then(() => location.reload()); }} </script>
    </head><body>
    <div class="card">
        <div class="owner">OWNER: {OWNER_NAME}</div>
        <div style="color:{status_color}; font-weight:bold; margin-bottom:10px;">● {status_text}</div>
        <button onclick="callBot('/on')" class="btn start">START SNIPER</button>
        <button onclick="callBot('/off')" class="btn stop">STOP SNIPER</button>
        <div class="stats">LIVE PAIR: {active_trade['pair']}<br>ENTRY AT: {active_trade['time']}</div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
            <button onclick="callBot('/win')" class="btn win">WIN</button>
            <button onclick="callBot('/mtg')" class="btn mtg">MTG</button>
        </div>
        <button onclick="callBot('/loss')" class="btn loss">LOSS</button>
        <button onclick="callBot('/final')" class="btn final">🔥 SHOW FINAL RESULTS 🔥</button>
    </div></body></html>
    """

class ControlHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global bot_running, stats
        if self.path == "/":
            self.send_response(200); self.send_header("Content-type", "text/html"); self.end_headers()
            self.wfile.write(get_html().encode()); return
        if self.path == "/on": bot_running = True
        elif self.path == "/off": bot_running = False
        elif self.path == "/win": stats["win"] += 1
        elif self.path == "/loss": stats["loss"] += 1
        self.send_response(200); self.end_headers()

# --- FAST SIGNAL ENGINE (Score 0.2) ---
def signal_loop():
    global active_trade, last_sig_time
    while True:
        try:
            if bot_running:
                now = datetime.datetime.now(TZ)
                if now.second == 48 and (time.time() - last_sig_time) > 170:
                    best_pair, best_action = None, None
                    for pair in PAIRS:
                        try:
                            h = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL, timeout=0.3)
                            score = h.get_analysis().indicators['Recommend.All']
                            if abs(score) >= 0.2: # আপনার সেট করা স্কোর ০.২
                                best_pair = pair
                                best_action = "CALL 📈" if score > 0 else "PUT 📉"
                                break
                        except: continue
                    
                    if best_pair:
                        trade_t = (now + datetime.timedelta(minutes=1)).strftime("%H:%M:00")
                        active_trade = {"pair": best_pair, "time": trade_t, "action": best_action}
                        last_sig_time = time.time()
                        msg = f"🎯 *CONFIRMED SIGNAL*\nPair: {best_pair}\nAction: {best_action}\nTrade: {trade_t}"
                        threading.Thread(target=send_telegram, args=(msg, best_pair)).start()
            time.sleep(1) 
        except: time.sleep(1)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=signal_loop, daemon=True).start()
    HTTPServer(('0.0.0.0', port), ControlHandler).serve_forever()
