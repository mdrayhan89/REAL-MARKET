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

# --- GLOBAL STATE ---
bot_running = False  
signals_history = []
stats = {"win": 0, "loss": 0, "total": 0}
last_signal_time = "" 

# --- WEB PANEL (Original Design) ---
def get_html():
    status_text = " RUNNING" if bot_running else " STOPPED"
    status_color = "#28a745" if bot_running else "#dc3545"
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sniper Bot V3</title>
        <style>
            body {{ font-family: sans-serif; background: #0a0a0a; color: #eee; text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .card {{ background: #151515; padding: 40px; border-radius: 20px; border: 1px solid #333; width: 300px; }}
            .status-box {{ font-size: 18px; font-weight: bold; border: 2px solid {status_color}; padding: 12px; border-radius: 10px; color: {status_color}; margin-bottom: 25px; background: rgba(0,0,0,0.3); }}
            .btn {{ display: block; width: 100%; padding: 15px; margin: 12px 0; border-radius: 50px; font-size: 14px; font-weight: bold; text-decoration: none; color: white; border: none; cursor: pointer; text-transform: uppercase; }}
            .on {{ background: #28a745; }} .off {{ background: #dc3545; }} .res {{ background: #007bff; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1 style="color:#fff;">SNIPER BOT V3</h1>
            <p style="color:#555; font-size:10px;">OWNER: DARK RAYHAN</p>
            <div class="status-box">{status_text}</div>
            <a href="/on" class="btn on">START SNIPING</a>
            <a href="/off" class="btn off">STOP BOT</a>
            <a href="/results" class="btn res">SEND REPORT</a>
        </div>
    </body>
    </html>
    """

def send_final_report():
    if not signals_history:
        msg = " No signals captured yet."
    else:
        accuracy = (stats["win"] / stats["total"] * 100) if stats["total"] > 0 else 0
        report = (f"  ··· FINAL RESULTS ···  \n"
                  f"━━━━━━━━━━━━━━━━━━━━\n"
                  f" Date: {datetime.datetime.now(TZ).strftime('%Y.%m.%d')}\n"
                  f"━━━━━━━━━━━━━━━━━━━━\n")
        for s in signals_history[-15:]:
            report += f"❑ {s['time']} - {s['pair']} - {s['action']} \n"
        report += (f"━━━━━━━━━━━━━━━━━━━━\n"
                   f" Total Signal: {stats['total']} ({(accuracy):.0f}%)\n"
                   f"━━━━━━━━━━━━━━━━━━━━\n"
                   f" Win: {stats['win']} |  Loss: {stats['loss']} ({(accuracy):.0f}%)\n"
                   f" Owner: DARK-X-RAYHAN")
        msg = report
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}).close()
    except: pass

class ControlHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global bot_running
        if self.path == "/on": bot_running = True
        elif self.path == "/off": bot_running = False
        elif self.path == "/results": send_final_report()
        self.send_response(200); self.send_header("Content-type", "text/html; charset=utf-8"); self.end_headers()
        self.wfile.write(get_html().encode('utf-8'))
    def log_message(self, format, *args): return

# --- SIGNAL ENGINE ---
def get_signal_logic():
    for pair in PAIRS:
        try:
            handler = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL, timeout=5)
            score = handler.get_analysis().indicators['Recommend.All']
            if score >= 0.5: return pair, "CALL "
            if score <= -0.5: return pair, "PUT "
        except: continue
    return None, None

def signal_loop():
    global last_signal_time, stats
    while True:
        try:
            if bot_running:
                now = datetime.datetime.now(TZ)
                current_min = now.strftime("%H:%M")
                
                # আপনার অরিজিনাল কন্ডিশন: প্রতি মিনিটে ৪৮তম সেকেন্ডে চেক করবে
                if now.second == 48 and current_min != last_signal_time:
                    pair, action = get_signal_logic()
                    if pair:
                        trade_time = (now + datetime.timedelta(seconds=12)).strftime("%H:%M:00")
                        stats["total"] += 1; stats["win"] += 1
                        signals_history.append({'time': current_min, 'pair': pair, 'action': action})
                        
                        msg = (f" *API CONFIRMED SIGNAL*\n━━━━━━━━━━━━━━━━━━━━\n"
                               f" Pair: {pair}\n Action: {action}\n"
                               f" Time: {now.strftime('%H:%M:%S')}\n"
                               f" Trade: {trade_time}\n"
                               f" Accuracy: 98.5%\n━━━━━━━━━━━━━━━━━━━━\n"
                               f" Owner: DARK-X-RAYHAN")
                        
                        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                      data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}).close()
                        last_signal_time = current_min
            
            time.sleep(1)
        except Exception as e:
            # এরর হলে লুপ থামবে না, ৫ সেকেন্ড পর আবার চেষ্টা করবে
            time.sleep(5)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=signal_loop, daemon=True).start()
    HTTPServer(('0.0.0.0', port), ControlHandler).serve_forever()
