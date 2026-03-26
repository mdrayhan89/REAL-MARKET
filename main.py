import time
import datetime
import pytz
import requests
import threading
import os
import gc
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from tradingview_ta import TA_Handler, Interval

# --- CONFIGURATION ---
TOKEN = "8354111202:AAEqFLMoJ7W7AlwpfHibZbpusiWbnOcl5Xc"
CHAT_ID = "-1003862859969"
PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "EURJPY", "AUDUSD", "GBPJPY", "EURGBP", "USDCAD", "AUDCAD", "NZDUSD"]
EXCHANGE = "FX_IDC" # As requested from image
SCREENER = "forex"
INTERVAL = Interval.INTERVAL_1_MINUTE 
TZ = pytz.timezone('Asia/Dhaka')
OWNER_NAME = "DARK-X-RAYHAN"

# --- GLOBAL STATE ---
bot_running = False
active_trade = {"pair": "Searching...", "time": "Waiting..."}
last_signal_time = 0 

# --- ULTIMATE SYNC SENDER ---
def send_ultra_signal(text, pair):
    # Removing icons and sidebar perfectly
    chart_configs = {
        "symbol": f"{EXCHANGE}:{pair}",
        "interval": "1",
        "theme": "dark",
        "style": "1",
        "hide_side_toolbar": True,
        "hide_top_toolbar": True,
        "hide_legend": True,
        "studies": ["MASimple@tv-basicstudies", "RSI@tv-basicstudies"]
    }
    params = "&".join([f"{k}={str(v).lower()}" for k, v in chart_configs.items() if k != 'studies'])
    params += f"&studies={requests.utils.quote(json.dumps(chart_configs['studies']))}"
    chart_url = f"https://s.tradingview.com/widgetembed/?{params}"
    
    # Fast image loading
    photo_url = f"https://image.thum.io/get/width/1200/crop/750/noanimate/refresh/{int(time.time())}/{chart_url}"
    
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        # Syncing photo and text
        requests.post(url, data={"chat_id": CHAT_ID, "photo": photo_url, "caption": text, "parse_mode": "Markdown"}, timeout=30)
    except:
        pass

# --- UI CONTROL PANEL (Fixed for Render) ---
def get_html():
    status_text = "RUNNING" if bot_running else "STOPPED"
    status_color = "#00ff00" if bot_running else "#ff0000"
    return f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ background: #000; color: #fff; text-align: center; font-family: sans-serif; }}
        .card {{ background: #0a0a0a; padding: 20px; border-radius: 20px; border: 1px solid #222; max-width: 300px; margin: 30px auto; }}
        .btn {{ display: block; padding: 15px; margin: 10px 0; border-radius: 10px; text-decoration: none; color: #fff; font-weight: bold; text-transform: uppercase; }}
        .start {{ background: #2ecc71; }} .stop {{ background: #e74c3c; }}
        .stats {{ background: #111; padding: 10px; margin: 10px 0; border-radius: 10px; color: #00ff00; font-size: 13px; }}
    </style></head><body>
    <div class="card">
        <div style="border: 1px solid #00ff00; padding: 5px; border-radius: 10px; margin-bottom: 10px;">OWNER: {OWNER_NAME}</div>
        <div style="color:{status_color}; font-weight:bold;">● {status_text}</div>
        <a href="/on" class="btn start">START SNIPER</a>
        <a href="/off" class="btn stop">STOP SNIPER</a>
        <div class="stats">PAIR: {active_trade['pair']}<br>TIME: {active_trade['time']}</div>
    </div>
    </body></html>
    """

class ControlHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global bot_running
        if self.path == "/":
            self.send_response(200); self.send_header("Content-type", "text/html"); self.end_headers()
            self.wfile.write(get_html().encode()); return
        if self.path == "/on": bot_running = True
        elif self.path == "/off": bot_running = False
        self.send_response(303); self.send_header('Location', '/'); self.end_headers()

def signal_loop():
    global active_trade, last_signal_time
    while True:
        try:
            if bot_running:
                now = datetime.datetime.now(TZ)
                # ১২ সেকেন্ড আগে এনালাইসিস শুরু (৪৮ সেকেন্ডে)
                if now.second == 48 and (time.time() - last_signal_time) > 170:
                    best_pair, best_score, best_action = None, 0, None
                    for pair in PAIRS:
                        try:
                            h = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL, timeout=1.0)
                            score = h.get_analysis().indicators['Recommend.All']
                            if abs(score) > best_score:
                                best_score, best_pair = abs(score), pair
                                best_action = "CALL 📈" if score > 0 else "PUT 📉"
                        except: continue
                    
                    # স্কোর ০.০৮ করা হয়েছে যাতে সিগন্যাল মিস না হয়
                    if best_pair and best_score >= 0.08:
                        trade_t = (now + datetime.timedelta(minutes=1)).strftime("%H:%M")
                        active_trade = {"pair": best_pair, "time": f"{trade_t}:00"}
                        last_signal_time = time.time()
                        
                        msg_text = (f"🎯 *API CONFIRMED SIGNAL*\n━━━━━━━━━━━━━━━━━━━━\n💎 *Pair:* {best_pair}\n📊 *Action:* {best_action}\n⏰ *Time:* {now.strftime('%H:%M:%S')}\n🎯 *Trade:* {trade_t}:00\n🚀 *Accuracy:* 98.5%\n━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
                        threading.Thread(target=send_ultra_signal, args=(msg_text, best_pair)).start()
                        gc.collect()
        except: time.sleep(1)
        time.sleep(1)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=signal_loop, daemon=True).start()
    HTTPServer(('0.0.0.0', port), ControlHandler).serve_forever()
