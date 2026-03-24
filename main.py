import time
import datetime
import pytz
import requests
import threading
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from tradingview_ta import TA_Handler, Interval

# --- CONFIGURATION ---
TOKEN = "8354111202:AAEqFLMoJ7W7AlwpfHibZbpusiWbnOcl5Xc"
CHAT_ID = "-1003862859969"
PAIRS = ["EURUSD", "EURJPY", "USDJPY", "CADJPY", "EURGBP", "AUDJPY", "GBPJPY", "AUDUSD", "GBPUSD", "AUDCAD", "USDCAD"]
EXCHANGE = "FX_IDC"
SCREENER = "forex"
INTERVAL = Interval.INTERVAL_1_MINUTE 
TZ = pytz.timezone('Asia/Dhaka')

# --- STATE CONTROLS ---
bot_running = True
last_sent_time = 0
cooldown_seconds = 120 # ২ মিনিটের বিরতি

# --- WEB PANEL (UTF-8 Fixed) ---
def get_html():
    status_text = "🟢 RUNNING" if bot_running else "🔴 STOPPED"
    status_color = "#28a745" if bot_running else "#dc3545"
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sniper Bot Control</title>
        <style>
            body {{ font-family: sans-serif; background: #121212; color: white; text-align: center; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .card {{ background: #1a1a1a; padding: 30px; border-radius: 15px; border: 1px solid #333; }}
            .status-box {{ font-size: 20px; font-weight: bold; border: 2px solid {status_color}; padding: 10px; border-radius: 8px; color: {status_color}; margin-bottom: 20px; }}
            .btn {{ display: block; width: 200px; padding: 15px; margin: 10px auto; border-radius: 8px; font-weight: bold; text-decoration: none; color: white; transition: 0.3s; }}
            .on {{ background: #28a745; }} .off {{ background: #dc3545; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Sniper Bot V3</h1>
            <div class="status-box">{status_text}</div>
            <a href="/on" class="btn on">✅ START SCANNING</a>
            <a href="/off" class="btn off">❌ STOP SCANNING</a>
        </div>
    </body>
    </html>
    """

class ControlHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global bot_running
        if self.path == "/on": bot_running = True
        elif self.path == "/off": bot_running = False
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(get_html().encode('utf-8'))
    def log_message(self, format, *args): return

# --- SIGNAL ENGINE (Your Logic + High Accuracy Filter) ---
def signal_loop():
    global last_sent_time
    print("Dark Rayhan Sniper Bot Started...")
    
    while True:
        if bot_running:
            now = datetime.datetime.now(TZ)
            current_ts = time.time()
            
            # আপনার লজিক: ৪৮ নম্বর সেকেন্ডে চেক করবে
            if now.second == 48:
                # ২ মিনিট বিরতি চেক
                if current_ts - last_sent_time > cooldown_seconds:
                    best_signal = None
                    max_score = 0
                    
                    for pair in PAIRS:
                        try:
                            handler = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL)
                            analysis = handler.get_analysis()
                            rec = analysis.summary['RECOMMENDATION']
                            
                            # একুরেসি নিশ্চিত করতে টেকনিক্যাল ইন্ডিকেটরের স্কোর দেখা (Buy/Sell count)
                            buy_score = analysis.summary['BUY']
                            sell_score = analysis.summary['SELL']
                            current_score = max(buy_score, sell_score)

                            # শুধুমাত্র স্ট্রং সিগন্যাল এবং যেটির স্কোর সবচেয়ে বেশি
                            if rec and ("STRONG" in rec) and current_score > max_score:
                                max_score = current_score
                                best_signal = {
                                    "pair": pair,
                                    "action": "CALL 📈" if "BUY" in rec else "PUT 📉",
                                    "time": now.strftime("%H:%M:%S"),
                                    "trade_time": (now + datetime.timedelta(seconds=12)).strftime("%H:%M:00")
                                }
                        except: continue
                    
                    # যদি ১১টি পেয়ারের মধ্যে সেরা কোনো স্ট্রং সিগন্যাল পাওয়া যায়
                    if best_signal:
                        msg = (f"📈 *API CONFIRMED SIGNAL*\n"
                               f"💎 *Pair:* {best_signal['pair']}\n"
                               f"📊 *Action:* {best_signal['action']}\n"
                               f"⏰ *Time:* {best_signal['time']}\n"
                               f"🎯 *Trade:* {best_signal['trade_time']}")
                        
                        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                      data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
                        
                        last_sent_time = current_ts # ২ মিনিটের বিরতি শুরু
                
                time.sleep(10) # একই মিনিটে ডাবল সিগন্যাল আটকানোর জন্য
        time.sleep(1)

# --- RUNNER ---
port = int(os.environ.get("PORT", 10000))
threading.Thread(target=lambda: HTTPServer(('0.0.0.0', port), ControlHandler).serve_forever(), daemon=True).start()
signal_loop()
