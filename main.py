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

# --- WEB PANEL (Original Style) ---
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
            <a href="/" class="btn res">REFRESH PAGE</a>
        </div>
    </body>
    </html>
    """

class ControlHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global bot_running
        if self.path == "/on": bot_running = True
        elif self.path == "/off": bot_running = False
        self.send_response(200); self.send_header("Content-type", "text/html; charset=utf-8"); self.end_headers()
        self.wfile.write(get_html().encode('utf-8'))
    def log_message(self, format, *args): return

# --- SIGNAL ENGINE (আপনার মূল লজিক) ---
def signal_loop():
    print("Dark Rayhan Sniper Bot is Active...")
    
    while True:
        if bot_running:
            now = datetime.datetime.now(TZ)
            
            # আপনার কোডের লজিক: ৪৮ নম্বর সেকেন্ডে চেক
            if now.second == 48:
                found_signal = False
                for pair in PAIRS:
                    try:
                        handler = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL)
                        analysis = handler.get_analysis()
                        rec = analysis.summary['RECOMMENDATION']
                        
                        # আপনার অরিজিনাল STRONG সিগন্যাল ফিল্টার
                        if rec and ("STRONG" in rec):
                            action = "CALL 📈" if "BUY" in rec else "PUT 📉"
                            trade_time = (now + datetime.timedelta(seconds=12)).strftime("%H:%M:00")
                            
                            msg = (f"🚀 *DARK RAYHAN SNIPER SIGNAL*\n"
                                   f"━━━━━━━━━━━━━━━━━━━━\n"
                                   f"💎 *Pair:* {pair}\n"
                                   f"📊 *Action:* {action}\n"
                                   f"⏰ *Time:* {now.strftime('%H:%M:%S')}\n"
                                   f"🎯 *Trade:* {trade_time}\n"
                                   f"━━━━━━━━━━━━━━━━━━━━")
                            
                            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                          data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
                            
                            found_signal = True
                            break # প্রথম ১টি সিগন্যাল পাওয়ামাত্র লুপ থেকে বের হয়ে যাবে
                    except: continue
                
                time.sleep(10) # একই মিনিটে ডাবল সিগন্যাল আটকানো
        time.sleep(1)

# --- RUNNER ---
port = int(os.environ.get("PORT", 10000))
threading.Thread(target=lambda: HTTPServer(('0.0.0.0', port), ControlHandler).serve_forever(), daemon=True).start()
signal_loop()
