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

# --- WEB PANEL (আপনার ছবির ডার্ক ডিজাইন) ---
def get_html():
    status_text = "🟢 RUNNING" if bot_running else "🔴 STOPPED"
    status_color = "#28a745" if bot_running else "#dc3545"
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sniper Bot V3</title>
        <style>
            body {{ font-family: sans-serif; background: #0a0a0a; color: #eee; text-align: center; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .card {{ background: #151515; padding: 40px; border-radius: 20px; border: 1px solid #333; }}
            h1 {{ margin-bottom: 5px; font-size: 22px; color: #fff; }}
            .status-box {{ font-size: 18px; font-weight: bold; border: 2px solid {status_color}; padding: 12px; border-radius: 10px; color: {status_color}; margin-bottom: 25px; }}
            .btn {{ display: block; width: 220px; padding: 15px; margin: 12px 0; border-radius: 50px; font-size: 15px; font-weight: bold; text-decoration: none; color: white; transition: 0.3s; border: none; cursor: pointer; }}
            .on {{ background: #28a745; }} .off {{ background: #dc3545; }} .res {{ background: #007bff; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>SNIPER BOT V3</h1>
            <p style="font-size:10px; color:#555; margin-bottom: 20px;">BY DARK RAYHAN</p>
            <div class="status-box">{status_text}</div>
            <a href="/on" class="btn on">START SIGNAL</a>
            <a href="/off" class="btn off">STOP SIGNAL</a>
            <a href="/results" class="btn res">SEND REPORT</a>
        </div>
    </body>
    </html>
    """

def send_report():
    if not signals_history:
        msg = "📊 No signals yet."
    else:
        report = "✨ ···🔥 *DARK RAYHAN RESULTS* 🔥··· ✨\n━━━━━━━━━━━━━━━━━━━━\n"
        for s in signals_history[-10:]:
            report += f"❑ {s['time']} - {s['pair']} - {s['action']} ✅\n"
        report += "━━━━━━━━━━━━━━━━━━━━"
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

# --- SIGNAL ENGINE (আপনার অরিজিনাল লজিক ১:১ রাখা হয়েছে) ---
def signal_loop():
    last_signals = {pair: "" for pair in PAIRS}
    print("Dark Rayhan Sniper Bot is Online...")
    
    while True:
        if bot_running:
            now = datetime.datetime.now(TZ)
            # ঠিক ৪৮ সেকেন্ডে স্ক্যান শুরু হবে
            if now.second == 48:
                for pair in PAIRS:
                    try:
                        handler = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL)
                        analysis = handler.get_analysis()
                        rec = analysis.summary['RECOMMENDATION']
                        
                        # আপনার অরিজিনাল লজিক: শুধুমাত্র STRONG থাকলেই সিগন্যাল
                        if rec and ("STRONG" in rec) and rec != last_signals[pair]:
                            action = "BUY 📈" if "BUY" in rec else "SELL 📉"
                            curr_time = now.strftime("%H:%M:%S")
                            trade_time = (now + datetime.timedelta(seconds=12)).strftime("%H:%M:00")
                            
                            signals_history.append({'time': now.strftime("%H:%M"), 'pair': pair, 'action': action})
                            
                            msg = (f"🚀 *DARK RAYHAN SNIPER SIGNAL*\n━━━━━━━━━━━━━━━━━━━━\n"
                                   f"💎 *Pair:* {pair}\n📊 *Action:* {action}\n"
                                   f"⏰ *Time:* {curr_time}\n"
                                   f"🎯 *Trade:* {trade_time}\n━━━━━━━━━━━━━━━━━━━━")
                            
                            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
                            
                            last_signals[pair] = rec
                            break # ১১টি একসাথে আসা বন্ধ করবে
                    except Exception as e:
                        print(f"Error fetching {pair}: {e}")
                        continue
                time.sleep(10)
        time.sleep(1)

port = int(os.environ.get("PORT", 10000))
threading.Thread(target=lambda: HTTPServer(('0.0.0.0', port), ControlHandler).serve_forever(), daemon=True).start()
signal_loop()
