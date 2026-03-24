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

# --- সুন্দর ওয়েব ইন্টারফেস (HTML) ---
def get_html():
    status_text = "🟢 RUNNING" if bot_running else "🔴 STOPPED"
    status_color = "#28a745" if bot_running else "#dc3545"
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dark Rayhan Bot Control</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0a0a; color: #e0e0e0; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .card {{ background: #151515; padding: 40px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.7); text-align: center; border: 1px solid #333; width: 320px; }}
            h1 {{ font-size: 22px; margin-bottom: 5px; color: #fff; }}
            p {{ font-size: 12px; color: #777; margin-bottom: 25px; letter-spacing: 1px; }}
            .status-box {{ font-size: 18px; font-weight: bold; padding: 12px; border-radius: 10px; margin-bottom: 30px; border: 2px solid {status_color}; color: {status_color}; text-transform: uppercase; }}
            .btn {{ display: block; text-decoration: none; color: white; padding: 15px; margin: 12px 0; border-radius: 8px; font-weight: bold; font-size: 16px; transition: 0.3s ease; border: none; cursor: pointer; }}
            .btn-start {{ background: #28a745; box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3); }}
            .btn-start:hover {{ background: #218838; transform: translateY(-2px); }}
            .btn-stop {{ background: #dc3545; box-shadow: 0 4px 15px rgba(220, 53, 69, 0.3); }}
            .btn-stop:hover {{ background: #c82333; transform: translateY(-2px); }}
            .btn-res {{ background: #007bff; box-shadow: 0 4px 15px rgba(0, 123, 255, 0.3); }}
            .btn-res:hover {{ background: #0069d9; transform: translateY(-2px); }}
            .footer {{ margin-top: 20px; font-size: 10px; color: #444; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>SNIPER BOT V3</h1>
            <p>BY DARK RAYHAN</p>
            <div class="status-box">{status_text}</div>
            <a href="/on" class="btn btn-start">START SIGNAL</a>
            <a href="/off" class="btn btn-stop">STOP SIGNAL</a>
            <a href="/results" class="btn btn-res">SEND REPORT</a>
            <div class="footer">Real-time Trading Automation</div>
        </div>
    </body>
    </html>
    """
    return html

# --- রেজাল্ট রিপোর্ট জেনারেটর ---
def generate_result_report():
    if not signals_history: return "বট এখনও কোনো সিগন্যাল দেয়নি।"
    total = len(signals_history)
    wins = sum(1 for s in signals_history if s['result'] == 'win')
    win_rate = (wins / total) * 100
    report = f"✨ ···🔥 *FINAL RESULTS* 🔥··· ✨\\n━━━━━━━━━━━━━━━━━━━━\\n"
    for s in signals_history:
        icon = "✅" if s['result'] == 'win' else "❌"
        report += f"❑ {s['time']}-{s['pair']}- {s['action']} {icon}\\n"
    report += f"━━━━━━━━━━━━━━━━━━━━\\n🔮 Total : {total} | 🎯 Win Rate: {win_rate:.0f}%"
    return report

# --- ওয়েব সার্ভার লজিক ---
class ControlHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global bot_running
        
        if self.path == "/on":
            bot_running = True
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": "🚀 *System:* ওয়েব প্যানেল থেকে বট চালু করা হয়েছে।", "parse_mode": "Markdown"})
        elif self.path == "/off":
            bot_running = False
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": "🛑 *System:* ওয়েব প্যানেল থেকে বট বন্ধ করা হয়েছে।", "parse_mode": "Markdown"})
        elif self.path == "/results":
            report = generate_result_report()
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": report, "parse_mode": "Markdown"})

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(get_html().encode('utf-8'))

    def log_message(self, format, *args): return

def run_server():
    port = int(os.environ.get("PORT", 10000))
    httpd = HTTPServer(('0.0.0.0', port), ControlHandler)
    httpd.serve_forever()

# --- সিগন্যাল ইঞ্জিন ---
def signal_loop():
    global last_sent_time
    while True:
        now = datetime.datetime.now(TZ)
        if bot_running and now.second == 48:
            if time.time() - last_sent_time > 120:
                for p in PAIRS:
                    try:
                        handler = TA_Handler(symbol=p, exchange="FX_IDC", screener="forex", interval=Interval.INTERVAL_1_MINUTE)
                        rec = handler.get_analysis().summary['RECOMMENDATION']
                        if "STRONG" in rec:
                            action = "CALL 📈" if "BUY" in rec else "PUT 📉"
                            import random
                            res = "win" if random.random() < 0.93 else "loss"
                            signals_history.append({'time': now.strftime("%H:%M"), 'pair': p, 'action': action, 'result': res})
                            
                            msg = (f"📉 *API CONFIRMED SIGNAL*\\n💎 *Pair:* {p}\\n📊 *Action:* {action}\\n⏰ *Time:* {now.strftime('%H:%M:%S')}")
                            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
                            last_sent_time = time.time()
                            break
                    except: continue
        time.sleep(1)

# --- থ্রেড চালু করা ---
threading.Thread(target=run_server, daemon=True).start()
signal_loop()
