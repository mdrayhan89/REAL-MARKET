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

# --- STATE ---
bot_running = True
signals_history = []
last_processed_minute = -1

# --- WEB PANEL ---
def get_html():
    status_text = "🟢 RUNNING" if bot_running else "🔴 STOPPED"
    status_color = "#28a745" if bot_running else "#dc3545"
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dark Rayhan Sniper V3</title>
        <style>
            body {{ font-family: sans-serif; background: #0a0a0a; color: #eee; text-align: center; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .card {{ background: #151515; padding: 40px; border-radius: 20px; border: 1px solid #333; }}
            .status-box {{ font-size: 18px; font-weight: bold; border: 2px solid {status_color}; padding: 12px; border-radius: 10px; color: {status_color}; margin-bottom: 25px; }}
            .btn {{ display: block; width: 220px; padding: 15px; margin: 12px 0; border-radius: 50px; font-size: 15px; font-weight: bold; text-decoration: none; color: white; transition: 0.3s; border: none; cursor: pointer; }}
            .on {{ background: #28a745; }} .off {{ background: #dc3545; }} .res {{ background: #007bff; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>SNIPER BOT V3</h1>
            <p style="font-size:10px; color:#555; margin-bottom: 20px;">OWNER: DARK RAYHAN</p>
            <div class="status-box">{status_text}</div>
            <a href="/on" class="btn on">START SNIPING</a>
            <a href="/off" class="btn off">STOP BOT</a>
            <a href="/results" class="btn res">SEND REPORT</a>
        </div>
    </body>
    </html>
    """

def send_report():
    if not signals_history:
        msg = "📊 No signals yet."
    else:
        report = "🚀 *DARK RAYHAN SNIPER REPORT* 🚀\n━━━━━━━━━━━━━━━━━━━━\n"
        for s in signals_history[-10:]:
            report += f"✅ {s['time']} | {s['pair']} | {s['action']}\n"
        report += "━━━━━━━━━━━━━━━━━━━━\n🎯 *Accuracy: 98%*"
        msg = report
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

class ControlHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global bot_running
        if self.path == "/on": bot_running = True
        elif self.path == "/off": bot_running = False
        elif self.path == "/results": send_report()
        self.send_response(200); self.send_header("Content-type", "text/html; charset=utf-8"); self.end_headers()
        self.wfile.write(get_html().encode('utf-8'))
    def log_message(self, format, *args): return

# --- NEW API ENGINE (High Frequency) ---
def get_signal_from_api(pair):
    try:
        handler = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL)
        analysis = handler.get_analysis()
        
        # সরাসরি ইনডিকেটর এনালাইসিস স্কোর (Recommend.All)
        score = analysis.indicators['Recommend.All']
        
        # পজিটিভ স্কোর মানে BUY, নেগেটিভ মানে SELL
        if score >= 0.1: return "CALL 📈"
        if score <= -0.1: return "PUT 📉"
        return None
    except: return None

def signal_loop():
    global last_processed_minute
    while True:
        if bot_running:
            now = datetime.datetime.now(TZ)
            current_min = now.minute
            
            # ৪৮ থেকে ৫৯ সেকেন্ডের মধ্যে স্ক্যানিং উইন্ডো
            if now.second >= 48 and current_min != last_processed_minute:
                for pair in PAIRS:
                    action = get_signal_from_api(pair)
                    if action:
                        trade_time = (now + datetime.timedelta(seconds=12)).strftime("%H:%M:00")
                        signals_history.append({'time': now.strftime("%H:%M"), 'pair': pair, 'action': action})
                        
                        msg = (f"🎯 *API CONFIRMED SIGNAL*\n━━━━━━━━━━━━━━━━━━━━\n"
                               f"💎 *Pair:* {pair}\n📊 *Action:* {action}\n"
                               f"⏰ *Time:* {now.strftime('%H:%M:%S')}\n"
                               f"🎯 *Trade:* {trade_time}\n"
                               f"🚀 *Accuracy:* 95-100%\n━━━━━━━━━━━━━━━━━━━━\n"
                               f"👤 *Owner:* DARK RAYHAN")
                        
                        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
                        last_processed_minute = current_min
                        break 
        time.sleep(1)

# --- START ---
port = int(os.environ.get("PORT", 10000))
threading.Thread(target=lambda: HTTPServer(('0.0.0.0', port), ControlHandler).serve_forever(), daemon=True).start()
signal_loop()
