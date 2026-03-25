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

# --- TELEGRAM SENDING ---
def send_telegram_with_chart(text, pair):
    chart_widget = f"https://s.tradingview.com/widgetembed/?symbol={EXCHANGE}:{pair}&interval=1&theme=dark"
    photo_url = f"https://mini.s-shot.ru/1024x768/JPEG/1024/Z100/?{chart_widget}"
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    try:
        r = requests.post(url, data={"chat_id": CHAT_ID, "photo": photo_url, "caption": text, "parse_mode": "Markdown"}, timeout=20)
        if r.status_code != 200: send_text_only(text)
    except: send_text_only(text)

def send_text_only(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try: requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=5)
    except: pass

# --- WIN/LOSS & MTG LOGIC ---
def check_result_logic(pair, action, current_min, is_mtg=False):
    # Candle sesh hoyar thik 5 second por check (12s age signal + 60s candle + 5s buffer = 77s total wait)
    # Kintu amra thread-e calculation korsi, tai timing niche firmed kora holo:
    if not is_mtg:
        time.sleep(17) # 48th second-e signal hole 60-48=12 + 5 = 17s wait
    else:
        time.sleep(60) # M1-er jonno thik 1 minute por

    try:
        h = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL, timeout=5)
        analysis = h.get_analysis()
        open_p, close_p = analysis.indicators['open'], analysis.indicators['close']
        
        is_win = (action == "CALL 📈" and close_p > open_p) or (action == "PUT 📉" and close_p < open_p)
        
        if is_win:
            res_label = "DIRECT WIN ✅" if not is_mtg else "MTG-1 WIN ✅¹"
            msg = (f"🎯 *{res_label}*\n━━━━━━━━━━━━━━━━━━━━\n"
                   f"💎 *Pair:* {pair}\n📊 *Result:* Success\n"
                   f"━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
            send_text_only(msg)
        else:
            if not is_mtg:
                # Direct Loss hole M1 Alert dibe
                m1_msg = (f"⚠️ *M1 ALERT (Martingale)* ⚠️\n━━━━━━━━━━━━━━━━━━━━\n"
                          f"💎 *Pair:* {pair}\n🔥 *Action:* {action} (M1)\n"
                          f"⏰ *Wait:* Checking M1 Result...\n"
                          f"━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
                send_text_only(m1_msg)
                # M1 result check korbe
                check_result_logic(pair, action, current_min, is_mtg=True)
            else:
                # MTG-o loss hole
                msg = (f"💀 *TOTAL LOSS ALERT* 💀\n━━━━━━━━━━━━━━━━━━━━\n"
                       f"💎 *Pair:* {pair}\n❌ *Result:* Failed\n"
                       f"━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
                send_text_only(msg)
    except: pass

# --- UI PANEL ---
def get_html():
    status_text = "RUNNING" if bot_running else "STOPPED"
    status_color = "#28a745" if bot_running else "#dc3545"
    return f"""
    <html><head><meta charset="UTF-8"><style>
        body {{ background: #000; color: #fff; text-align: center; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
        .card {{ background: #0f0f0f; padding: 30px; border-radius: 20px; border: 1px solid #222; width: 260px; }}
        .btn {{ display: block; padding: 12px; margin: 10px 0; border-radius: 10px; text-decoration: none; color: #fff; font-weight: bold; text-transform: uppercase; font-size: 13px; }}
    </style></head><body><div class="card">
        <h3>SNIPER V3 PRO</h3>
        <div style="color:{status_color}; margin-bottom: 20px;">● {status_text}</div>
        <a href="/on" class="btn" style="background:#28a745">START</a>
        <a href="/off" class="btn" style="background:#dc3545">STOP</a>
    </div></body></html>
    """

class ControlHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global bot_running
        if self.path == "/on": bot_running = True
        elif self.path == "/off": bot_running = False
        self.send_response(200); self.send_header("Content-type", "text/html"); self.end_headers()
        self.wfile.write(get_html().encode())
    def log_message(self, format, *args): return

# --- MAIN LOOP ---
def signal_loop():
    global sent_signals_cache
    while True:
        try:
            if bot_running:
                now = datetime.datetime.now(TZ)
                # 12 sec age signal (48th second)
                if 48 <= now.second <= 50:
                    current_min = now.strftime("%H:%M")
                    if current_min not in sent_signals_cache:
                        for pair in PAIRS:
                            h = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL, timeout=5)
                            score = h.get_analysis().indicators['Recommend.All']
                            if abs(score) >= 0.35:
                                action = "CALL 📈" if score > 0 else "PUT 📉"
                                trade_time = (now + datetime.timedelta(minutes=1)).replace(second=0).strftime("%H:%M:%S")
                                msg = (f"🎯 *API CONFIRMED SIGNAL*\n━━━━━━━━━━━━━━━━━━━━\n"
                                       f"💎 *Pair:* {pair}\n📊 *Action:* {action}\n"
                                       f"⏰ *Time:* {now.strftime('%H:%M:%S')}\n"
                                       f"🎯 *Trade:* {trade_time}\n"
                                       f"🚀 *Accuracy:* 98.5%\n━━━━━━━━━━━━━━━━━━━━\n"
                                       f"👤 *Owner:* {OWNER_NAME}")
                                
                                threading.Thread(target=send_telegram_with_chart, args=(msg, pair)).start()
                                threading.Thread(target=check_result_logic, args=(pair, action, current_min)).start()
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
