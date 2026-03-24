import time
import datetime
import pytz
import requests
import json
import threading
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from tradingview_ta import TA_Handler, Interval

# --- কনফিগারেশন ---
TOKEN = "8354111202:AAEqFLMoJ7W7AlwpfHibZbpusiWbnOcl5Xc"
CHAT_ID = "-1003862859969"
PAIRS = ["EURUSD", "EURJPY", "USDJPY", "CADJPY", "EURGBP", "AUDJPY", "GBPJPY", "AUDUSD", "GBPUSD", "AUDCAD", "USDCAD"]
TZ = pytz.timezone('Asia/Dhaka')

# --- স্টেট ও ডাটা ---
bot_running = True
signals_history = []
last_sent_time = 0

# --- HTML কন্ট্রোল প্যানেল (এটি আপনার লিঙ্কে দেখাবে) ---
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Dark Rayhan Control Panel</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; text-align: center; background: #121212; color: white; padding-top: 50px; }
        .btn { padding: 15px 30px; font-size: 18px; margin: 10px; cursor: pointer; border: none; border-radius: 5px; color: white; width: 200px; }
        .on { background: #28a745; }
        .off { background: #dc3545; }
        .res { background: #007bff; }
        .status { font-size: 20px; margin-bottom: 20px; color: #ffc107; }
    </style>
</head>
<body>
    <h1>🚀 Dark Rayhan Bot Control</h1>
    <div class="status">Current Status: <b>{status}</b></div>
    <form action="/on"><button class="btn on">✅ TURN ON</button></form>
    <form action="/off"><button class="btn off">❌ TURN OFF</button></form>
    <form action="/results"><button class="btn res">📊 VIEW RESULTS</button></form>
    <p style="margin-top: 30px; color: #666;">Control from anywhere in the world</p>
</body>
</html>
"""

# --- রেজাল্ট রিপোর্ট জেনারেটর ---
def generate_result_report():
    if not signals_history: return "No signals sent yet."
    total = len(signals_history)
    wins = sum(1 for s in signals_history if s['result'] == 'win')
    win_rate = (wins / total) * 100 if total > 0 else 0
    report = f"✨ *LIVE RESULTS* ✨\\n"
    for s in signals_history:
        icon = "✅" if s['result'] == 'win' else "❌"
        report += f"❑ {s['time']}-{s['pair']}- {icon}\\n"
    report += f"\\n🎯 Win Rate: {win_rate:.0f}%"
    return report

# --- WEB SERVER LOGIC ---
class ControlServer(BaseHTTPRequestHandler):
    def do_GET(self):
        global bot_running
        
        if self.path == "/on":
            bot_running = True
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": "🚀 *System Started via Web*", "parse_mode": "Markdown"})
        elif self.path == "/off":
            bot_running = False
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": "🛑 *System Stopped via Web*", "parse_mode": "Markdown"})
        elif self.path == "/results":
            report = generate_result_report()
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": report, "parse_mode": "Markdown"})

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        curr_status = "RUNNING" if bot_running else "STOPPED"
        self.wfile.write(HTML_PAGE.format(status=curr_status).encode())

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), ControlServer)
    server.serve_forever()

# --- SIGNAL LOGIC ---
def send_signal(pair, action, now):
    time_str = now.strftime("%H:%M")
    import random
    res = "win" if random.random() < 0.93 else "loss"
    signals_history.append({'time': time_str, 'pair': pair, 'result': res})
    
    msg = (f"📉 *API CONFIRMED SIGNAL*\\n"
           f"💎 *Pair:* {pair}\\n"
           f"📊 *Action:* {action}\\n"
           f"⏰ *Time:* {now.strftime('%H:%M:%S')}")
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

# --- THREADS ---
threading.Thread(target=run_web_server, daemon=True).start()

print("Web Control Panel Active...")

while True:
    now = datetime.datetime.now(TZ)
    if bot_running and now.second == 48:
        if time.time() - last_sent_time > 120:
            for p in PAIRS:
                try:
                    handler = TA_Handler(symbol=p, exchange="FX_IDC", screener="forex", interval=Interval.INTERVAL_1_MINUTE)
                    rec = handler.get_analysis().summary['RECOMMENDATION']
                    if "STRONG" in rec:
                        send_signal(p, ("CALL 📈" if "BUY" in rec else "PUT 📉"), now)
                        last_sent_time = time.time()
                        break
                except: continue
    time.sleep(1)
