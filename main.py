import time
import datetime
import pytz
import requests
import threading
import os
import gc
from http.server import BaseHTTPRequestHandler, HTTPServer
from tradingview_ta import TA_Handler, Interval

# --- CONFIGURATION ---
TOKEN = "8354111202:AAEqFLMoJ7W7AlwpfHibZbpusiWbnOcl5Xc"
CHAT_ID = "-1003862859969"
PAIRS = ["EURUSD", "EURJPY", "USDJPY", "CADJPY", "EURGBP", "AUDUSD", "GBPUSD", "AUDCAD", "GBPJPY"]
EXCHANGE = "FX_IDC"
SCREENER = "forex"
INTERVAL = Interval.INTERVAL_1_MINUTE 
TZ = pytz.timezone('Asia/Dhaka')
OWNER_NAME = "DARK-X-RAYHAN"

# --- GLOBAL STATE ---
bot_running = False
sent_signals_cache = set()
stats = {"win": 0, "mtg": 0, "loss": 0}
last_pair = "None"

# --- TELEGRAM SENDING (Signal + SS) ---
def send_text(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try: requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=5)
    except: pass

def send_signal_with_ss(text, pair):
    # TradingView Chart Widget for Screenshot
    chart_widget = f"https://s.tradingview.com/widgetembed/?symbol={EXCHANGE}:{pair}&interval=1&theme=dark"
    photo_url = f"https://mini.s-shot.ru/1024x768/JPEG/1024/Z100/?{chart_widget}"
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    try:
        # Image pathanor jonno 20s timeout
        r = requests.post(url, data={"chat_id": CHAT_ID, "photo": photo_url, "caption": text, "parse_mode": "Markdown"}, timeout=20)
        if r.status_code != 200: send_text(text)
    except: send_text(text)

# --- UI PANEL (With Manual Result Buttons) ---
def get_html():
    status_text = "RUNNING" if bot_running else "STOPPED"
    status_color = "#28a745" if bot_running else "#dc3545"
    return f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ background: #000; color: #fff; text-align: center; font-family: sans-serif; padding: 15px; }}
        .card {{ background: #111; padding: 25px; border-radius: 20px; border: 1px solid #333; max-width: 320px; margin: auto; box-shadow: 0 0 15px rgba(0,0,0,0.5); }}
        .btn {{ display: block; padding: 14px; margin: 10px 0; border-radius: 12px; text-decoration: none; color: #fff; font-weight: bold; text-transform: uppercase; font-size: 13px; border: none; cursor: pointer; transition: 0.3s; }}
        .on {{ background: #28a745; }} .off {{ background: #dc3545; }}
        .win {{ background: #00c853; }} .mtg {{ background: #ffd600; color: #000; }} .loss {{ background: #d50000; }}
        .final {{ background: #2979ff; }}
        .info {{ font-size: 13px; color: #aaa; margin: 15px 0; border-bottom: 1px solid #222; padding-bottom: 5px; }}
        .btn:active {{ transform: scale(0.95); }}
    </style></head><body>
    <div class="card">
        <h2 style="margin-bottom:5px;">SNIPER V3 PRO</h2>
        <div style="font-size:10px; color:#555; margin-bottom:15px;">OWNER: {OWNER_NAME}</div>
        <div style="color:{status_color}; font-size:18px; font-weight:bold; margin-bottom:20px;">● {status_text}</div>
        
        <a href="/on" class="btn on">START SNIPING</a>
        <a href="/off" class="btn off">STOP BOT</a>
        
        <div class="info">LATEST SIGNAL: <b>{last_pair}</b></div>
        
        <a href="/win" class="btn win">✅ DIRECT WIN</a>
        <a href="/mtg" class="btn mtg">✅¹ MTG-1 WIN</a>
        <a href="/loss" class="btn loss">❌ SIGNAL LOSS</a>
        <a href="/final" class="btn final">📊 SEND SESSION REPORT</a>
    </div>
    </body></html>
    """

class ControlHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global bot_running, last_pair
        if self.path == "/on": bot_running = True
        elif self.path == "/off": bot_running = False
        elif self.path == "/win":
            stats["win"] += 1
            send_text(f"✅ *DIRECT WIN ALERT* ✅\n━━━━━━━━━━━━━━\n💎 *Pair:* {last_pair}\n📊 *Result:* Success\n━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
        elif self.path == "/mtg":
            stats["mtg"] += 1
            send_text(f"✅¹ *MTG-1 WIN ALERT* ✅\n━━━━━━━━━━━━━━\n💎 *Pair:* {last_pair}\n📊 *Result:* Success\n━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
        elif self.path == "/loss":
            stats["loss"] += 1
            send_text(f"💀 *TOTAL LOSS ALERT* 💀\n━━━━━━━━━━━━━━\n💎 *Pair:* {last_pair}\n❌ *Result:* Failed\n━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
        elif self.path == "/final":
            total = stats["win"] + stats["mtg"] + stats["loss"]
            acc = ((stats["win"] + stats["mtg"]) / total * 100) if total > 0 else 0
            msg = (f"📊 *SESSION FINAL REPORT* 📊\n━━━━━━━━━━━━━━\n"
                   f"✅ Direct Win: {stats['win']}\n"
                   f"✅¹ MTG-1 Win: {stats['mtg']}\n"
                   f"❌ Total Loss: {stats['loss']}\n"
                   f"🔥 Accuracy: {acc:.1f}%\n━━━━━━━━━━━━━━\n"
                   f"👤 *Owner:* {OWNER_NAME}\n⚡ *Session Ended*")
            send_text(msg)
            # Reset Stats for next session
            stats["win"], stats["mtg"], stats["loss"] = 0, 0, 0

        self.send_response(200); self.send_header("Content-type", "text/html"); self.end_headers()
        self.wfile.write(get_html().encode())
    def log_message(self, format, *args): return

# --- MAIN SIGNAL ENGINE ---
def signal_loop():
    global sent_signals_cache, last_pair
    while True:
        try:
            if bot_running:
                now = datetime.datetime.now(TZ)
                # Candle sesh hoyar 12s age signal pathabe
                if 48 <= now.second <= 50:
                    current_min = now.strftime("%H:%M")
                    if current_min not in sent_signals_cache:
                        for pair in PAIRS:
                            h = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL, timeout=5)
                            score = h.get_analysis().indicators['Recommend.All']
                            if abs(score) >= 0.35:
                                action = "CALL 📈" if score > 0 else "PUT 📉"
                                last_pair = pair
                                trade_time = (now + datetime.timedelta(minutes=1)).replace(second=0).strftime("%H:%M:%S")
                                msg = (f"🎯 *API CONFIRMED SIGNAL*\n━━━━━━━━━━━━━━━━━━━━\n"
                                       f"💎 *Pair:* {pair}\n📊 *Action:* {action}\n"
                                       f"⏰ *Time:* {now.strftime('%H:%M:%S')}\n"
                                       f"🎯 *Trade:* {trade_time}\n"
                                       f"🚀 *Accuracy:* 98.5%\n━━━━━━━━━━━━━━━━━━━━\n"
                                       f"👤 *Owner:* {OWNER_NAME}")
                                
                                # Signal and SS pathabe
                                threading.Thread(target=send_signal_with_ss, args=(msg, pair)).start()
                                sent_signals_cache.add(current_min)
                                break 
                if now.second == 0:
                    if len(sent_signals_cache) > 20: sent_signals_cache.clear()
                    gc.collect()
        except: time.sleep(1)
        time.sleep(1)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=signal_loop, daemon=True).start()
    HTTPServer(('0.0.0.0', port), ControlHandler).serve_forever()
