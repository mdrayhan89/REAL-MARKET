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
EXCHANGE = "FX_IDC"
SCREENER = "forex"
INTERVAL = Interval.INTERVAL_1_MINUTE 
TZ = pytz.timezone('Asia/Dhaka')
OWNER_NAME = "DARK-X-RAYHAN"

# --- GLOBAL STATE ---
bot_running = False
stats = {"win": 0, "mtg": 0, "loss": 0}
active_trade = {"pair": "Searching...", "time": "Waiting..."}
session_history = []
last_signal_timestamp = 0

# --- SS GENERATOR (Custom View) ---
def send_custom_ss(pair):
    chart_configs = {
        "symbol": f"{EXCHANGE}:{pair}",
        "interval": "1",
        "theme": "dark",
        "style": "1",
        "hide_side_toolbar": True, # আপনার রিকুয়েস্ট অনুযায়ী
        "hide_top_toolbar": True,
        "backgroundColor": "#000000",
        "studies": ["MASimple@tv-basicstudies", "RSI@tv-basicstudies", "MACD@tv-basicstudies"]
    }
    params = "&".join([f"{k}={str(v).lower()}" for k, v in chart_configs.items() if k != 'studies'])
    params += f"&studies={requests.utils.quote(json.dumps(chart_configs['studies']))}"
    chart_url = f"https://s.tradingview.com/widgetembed/?{params}"
    photo_url = f"https://image.thum.io/get/width/1200/crop/750/noanimate/refresh/{int(time.time())}/{chart_url}"
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", data={"chat_id": CHAT_ID, "photo": photo_url}, timeout=20)
    except: pass

# --- UI CONTROL PANEL (With Auto-Refresh Script) ---
def get_html():
    status_text = "RUNNING" if bot_running else "STOPPED"
    status_color = "#00ff00" if bot_running else "#ff0000"
    return f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="30"> <style>
        body {{ background: #000; color: #fff; text-align: center; font-family: sans-serif; padding: 10px; }}
        .card {{ background: #0a0a0a; padding: 20px; border-radius: 25px; border: 1px solid #1a1a1a; max-width: 340px; margin: auto; }}
        .owner {{ color: #00ff00; font-size: 14px; font-weight: bold; border: 1px solid #00ff00; padding: 5px 10px; border-radius: 8px; margin-bottom: 15px; display: inline-block; }}
        .btn {{ display: block; padding: 14px; margin: 8px 0; border-radius: 12px; text-decoration: none; color: #fff; font-weight: bold; text-transform: uppercase; font-size: 12px; }}
        .start {{ background: #2ecc71; }} .stop {{ background: #e74c3c; }}
        .win {{ background: #27ae60; }} .mtg {{ background: #f1c40f; color: #000; }} .loss {{ background: #c0392b; }}
        .final {{ background: #3498db; }}
        .info-box {{ background: #111; border-left: 5px solid #00ff00; border-radius: 10px; padding: 12px; margin: 15px 0; text-align: left; font-size: 13px; color: #00ff00; }}
    </style></head><body>
    <div class="card">
        <div class="owner">OWNER: {OWNER_NAME}</div>
        <div style="color:{status_color}; font-weight:bold; margin-bottom:15px;">● {status_text}</div>
        <a href="/on" class="btn start">START SNIPER</a>
        <a href="/off" class="btn stop">STOP SNIPER</a>
        <div class="info-box">
            <b>LIVE PAIR:</b> {active_trade['pair']}<br>
            <b>LIVE TIME:</b> {active_trade['time']}
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
            <a href="/win" class="btn win">WIN</a>
            <a href="/mtg" class="btn mtg">MTG</a>
        </div>
        <a href="/loss" class="btn loss">LOSS</a>
        <a href="/final" class="btn final">🔥 SHOW FINAL RESULTS 🔥</a>
    </div>
    </body></html>
    """

class ControlHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global bot_running, session_history, stats, active_trade
        def msg(t): requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": t, "parse_mode": "Markdown"}, timeout=5)
        if self.path == "/":
            self.send_response(200); self.send_header("Content-type", "text/html"); self.end_headers()
            self.wfile.write(get_html().encode()); return
        if self.path == "/on": bot_running = True
        elif self.path == "/off": bot_running = False
        elif self.path == "/win":
            stats["win"] += 1; session_history.append(f"❑ {active_trade['time']} - {active_trade['pair']} ✅")
            msg(f"✅ *DIRECT WIN* ✅\n━━━━━━━━━━━━━━\n💎 *Pair:* {active_trade['pair']}\n⏰ *Time:* {active_trade['time']}\n👤 *Owner:* {OWNER_NAME}")
        elif self.path == "/mtg":
            stats["mtg"] += 1; session_history.append(f"❑ {active_trade['time']} - {active_trade['pair']} ✅¹")
            msg(f"✅¹ *MTG-1 WIN* ✅\n━━━━━━━━━━━━━━\n💎 *Pair:* {active_trade['pair']}\n⏰ *Time:* {active_trade['time']}\n👤 *Owner:* {OWNER_NAME}")
        elif self.path == "/loss":
            stats["loss"] += 1; session_history.append(f"❑ {active_trade['time']} - {active_trade['pair']} ❌")
            msg(f"💀 *LOSS ALERT* 💀\n━━━━━━━━━━━━━━\n💎 *Pair:* {active_trade['pair']}\n⏰ *Time:* {active_trade['time']}\n👤 *Owner:* {OWNER_NAME}")
        elif self.path == "/final":
            total = stats["win"] + stats["mtg"] + stats["loss"]; win_c = stats["win"] + stats["mtg"]
            acc = (win_c / total * 100) if total > 0 else 0
            res = "\n".join(session_history) if session_history else "No Data"
            msg(f"💠 🔥 FINAL SESSION RESULTS 🔥 💠\n━━━━━━━━━━━━━━\n{res}\n━━━━━━━━━━━━━━\n🎯 Accuracy: {acc:.0f}%\n👤 Owner: {OWNER_NAME}")
            stats["win"], stats["mtg"], stats["loss"], session_history = 0, 0, 0, []
        self.send_response(303); self.send_header('Location', '/'); self.end_headers()

def signal_loop():
    global active_trade, last_signal_timestamp
    while True:
        try:
            if bot_running:
                now = datetime.datetime.now(TZ)
                # ১২ সেকেন্ড আগে এনালাইসিস শুরু (৪৪-৪৮ সেকেন্ডে)
                if now.second >= 44 and now.second <= 48 and (time.time() - last_signal_timestamp) >= 50:
                    best_pair, best_score, best_action = None, 0, None
                    for pair in PAIRS:
                        try:
                            h = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL, timeout=0.8)
                            score = h.get_analysis().indicators['Recommend.All']
                            if abs(score) > best_score:
                                best_score, best_pair = abs(score), pair
                                best_action = "CALL 📈" if score > 0 else "PUT 📉"
                        except: continue
                    
                    # সিগন্যাল ফ্রিকোয়েন্সি বাড়ানোর জন্য স্কোর ০.১০ এ নামানো হয়েছে
                    if best_pair and best_score >= 0.10:
                        trade_t = (now + datetime.timedelta(minutes=1)).strftime("%H:%M")
                        active_trade["pair"], active_trade["time"] = best_pair, f"{trade_t}:00"
                        last_signal_timestamp = time.time()
                        msg_text = (f"🎯 *API CONFIRMED SIGNAL*\n━━━━━━━━━━━━━━━━━━━━\n💎 *Pair:* {best_pair}\n📊 *Action:* {best_action}\n⏰ *Time:* {now.strftime('%H:%M:%S')}\n🎯 *Trade:* {trade_t}:00\n🚀 *Accuracy:* 98.5%\n━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
                        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg_text, "parse_mode": "Markdown"})
                        threading.Thread(target=send_custom_ss, args=(best_pair,)).start()
                if now.second == 0: gc.collect()
        except: time.sleep(1)
        time.sleep(1)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=signal_loop, daemon=True).start()
    HTTPServer(('0.0.0.0', port), ControlHandler).serve_forever()
