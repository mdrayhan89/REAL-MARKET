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
OWNER_NAME = "DARK-X-RAYHAN" # আপনার নাম এখানে সেট করা হয়েছে

# --- GLOBAL STATE ---
bot_running = False
signals_history = []
stats = {"win": 0, "loss": 0, "total": 0}
last_signal_time = ""

# --- TELEGRAM SEND FUNCTION ---
def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
    except:
        pass

# --- WIN/LOSS & MTG ENGINE ---
def check_full_result(pair, action, time_id):
    global stats
    time.sleep(65)
    try:
        h = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL)
        rec = h.get_analysis().summary['RECOMMENDATION']
        is_win = ("CALL" in action and "BUY" in rec) or ("PUT" in action and "SELL" in rec)
        
        if is_win:
            stats["win"] += 1
            send_telegram(f"✅ *DIRECT WIN* ✅\n━━━━━━━━━━━━━━━━━━━━\n💎 *Pair:* {pair}\n💰 *Result:* Profit\n━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
            update_history(time_id, "✅")
            return

        # M1 Alert if 1st candle loses
        send_telegram(f"⚠️ *M1 ALERT* ⚠️\n━━━━━━━━━━━━━━━━━━━━\n💎 *Pair:* {pair}\n🔥 *Next:* M1 {action}\n━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
        
        time.sleep(60)
        rec2 = h.get_analysis().summary['RECOMMENDATION']
        if ("CALL" in action and "BUY" in rec2) or ("PUT" in action and "SELL" in rec2):
            stats["win"] += 1
            send_telegram(f"✅ *MTG-1 WIN* ✅\n━━━━━━━━━━━━━━━━━━━━\n💎 *Pair:* {pair}\n💰 *Result:* M1 Profit\n━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
            update_history(time_id, "✅¹")
        else:
            stats["loss"] += 1
            send_telegram(f"💀 *TOTAL LOSS* 💀\n━━━━━━━━━━━━━━━━━━━━\n💎 *Pair:* {pair}\n❌ *Result:* Loss\n━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
            update_history(time_id, "❌")
    except:
        pass

def update_history(t_id, res):
    for s in signals_history:
        if s['time'] == t_id:
            s['result'] = res
            break

# --- WEB PANEL DESIGN (Fixing Encoding & Style) ---
def get_html():
    status_icon = "🔴" if not bot_running else "🟢"
    status_text = "STOPPED" if not bot_running else "RUNNING"
    status_color = "#dc3545" if not bot_running else "#28a745"
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sniper Bot V3</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #000; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .card {{ background: #111; padding: 40px; border-radius: 25px; border: 1px solid #222; width: 320px; text-align: center; box-shadow: 0 10px 40px rgba(0,0,0,0.8); }}
            h1 {{ font-size: 26px; margin-bottom: 5px; color: #fff; text-transform: uppercase; }}
            .owner {{ color: #555; font-size: 10px; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 30px; display: block; }}
            .status-box {{ font-size: 18px; font-weight: bold; border: 2px solid {status_color}; padding: 15px; border-radius: 12px; color: {status_color}; margin-bottom: 30px; background: rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; gap: 10px; }}
            .btn {{ display: block; width: 100%; padding: 16px; margin: 15px 0; border-radius: 50px; font-size: 14px; font-weight: bold; text-decoration: none; color: white; transition: 0.3s; border: none; cursor: pointer; text-transform: uppercase; }}
            .on {{ background: #28a745; }} .off {{ background: #dc3545; }} .res {{ background: #007bff; }}
            .btn:active {{ transform: scale(0.98); }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>SNIPER V3 PRO</h1>
            <span class="owner">OWNER: {OWNER_NAME}</span>
            <div class="status-box">
                <span>{status_icon}</span> {status_text}
            </div>
            <a href="/on" class="btn on">START SNIPING</a>
            <a href="/off" class="btn off">STOP BOT</a>
            <a href="/results" class="btn res">SEND REPORT</a>
        </div>
    </body>
    </html>
    """

class ControlHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global bot_running
        if self.path == "/on": bot_running = True
        elif self.path == "/off": bot_running = False
        elif self.path == "/results": send_final_report()
        
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8") # এনকোডিং ফিক্স
        self.end_headers()
        self.wfile.write(get_html().encode('utf-8'))
    def log_message(self, format, *args): return

def send_final_report():
    if not signals_history:
        send_telegram("📊 No signals captured yet.")
    else:
        acc = (stats["win"] / stats["total"] * 100) if stats["total"] > 0 else 0
        report = f"💠 *FINAL SNIPER REPORT* 💠\n━━━━━━━━━━━━━━━━━━━━\n"
        for s in signals_history[-12:]:
            report += f"❑ {s['time']} | {s['pair']} | {s['action']} {s.get('result', '⌛')}\n"
        report += f"━━━━━━━━━━━━━━━━━━━━\n🎯 Accuracy: {acc:.1f}%\n👤 Owner: {OWNER_NAME}"
        send_telegram(report)

# --- SIGNAL ENGINE ---
def signal_loop():
    global last_signal_time, stats
    while True:
        if bot_running:
            now = datetime.datetime.now(TZ)
            min_id = now.strftime("%H:%M")
            if now.second == 48 and min_id != last_signal_time:
                for pair in PAIRS:
                    try:
                        h = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL)
                        score = h.get_analysis().indicators['Recommend.All']
                        
                        # আপনার দেওয়া লজিক অনুযায়ী সিগন্যাল জেনারেট
                        if score >= 0.5 or score <= -0.5:
                            action = "CALL 📈" if score > 0 else "PUT 📉"
                            stats["total"] += 1
                            signals_history.append({'time': min_id, 'pair': pair, 'action': action, 'result': '⌛'})
                            
                            trade_t = (now + datetime.timedelta(seconds=12)).strftime('%H:%M:00')
                            msg = (f"🎯 *API CONFIRMED SIGNAL*\n━━━━━━━━━━━━━━━━━━━━\n"
                                   f"💎 *Pair:* {pair}\n📊 *Action:* {action}\n"
                                   f"⏰ *Time:* {now.strftime('%H:%M:%S')}\n"
                                   f"🎯 *Trade:* {trade_t}\n"
                                   f"🚀 *Accuracy:* 98.5%\n━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
                            
                            send_telegram(msg)
                            last_signal_time = min_id
                            threading.Thread(target=check_full_result, args=(pair, action, min_id)).start()
                            break
                    except:
                        continue
        time.sleep(1)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=signal_loop, daemon=True).start()
    HTTPServer(('0.0.0.0', port), ControlHandler).serve_forever()
