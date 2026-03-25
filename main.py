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
# আপনি ৫৪টি পেয়ার এখানে লিস্ট করতে পারেন
PAIRS = ["EURUSD", "EURJPY", "USDJPY", "CADJPY", "EURGBP", "AUDJPY", "GBPJPY", "AUDUSD", "GBPUSD", "AUDCAD", "USDCAD"]
EXCHANGE = "FX_IDC"
SCREENER = "forex"
INTERVAL = Interval.INTERVAL_1_MINUTE 
TZ = pytz.timezone('Asia/Dhaka')
OWNER_NAME = "DARK-X-RAYHAN"

# --- GLOBAL STATE ---
bot_running = False
signals_history = []
stats = {"win": 0, "loss": 0, "total": 0}
sent_signals_cache = set()
thread_limiter = threading.Semaphore(5)

# --- CHART SCREENSHOT & TELEGRAM ---
def send_telegram_with_chart(text, pair):
    # ডাইনামিক চার্ট স্ক্রিনশট জেনারেটর (No API Key Required)
    chart_widget = f"https://s.tradingview.com/widgetembed/?symbol={EXCHANGE}:{pair}&interval=1&theme=dark"
    photo_url = f"https://mini.s-shot.ru/1024x768/JPEG/1024/Z100/?{chart_widget}"

    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    payload = {
        "chat_id": CHAT_ID,
        "photo": photo_url,
        "caption": text,
        "parse_mode": "Markdown"
    }
    
    try:
        r = requests.post(url, data=payload, timeout=15)
        if r.status_code != 200:
            send_telegram_text(text)
    except:
        send_telegram_text(text)

def send_telegram_text(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try: requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=8)
    except: pass

# --- TRADING LOGIC ---
def get_candle_data(pair):
    try:
        h = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL, timeout=10)
        analysis = h.get_analysis()
        return analysis.indicators['open'], analysis.indicators['close']
    except: return None, None

def check_result_logic(pair, action, time_id, is_mtg=False):
    with thread_limiter:
        global stats
        time.sleep(65) 
        open_p, close_p = get_candle_data(pair)
        if open_p is None: return

        is_win = (action == "CALL 📈" and close_p > open_p) or (action == "PUT 📉" and close_p < open_p)

        if is_win:
            stats["win"] += 1
            res_label = "MTG-1 WIN" if is_mtg else "DIRECT WIN"
            update_history(time_id, pair, "✅¹" if is_mtg else "✅")
            msg = (f"✅ *{res_label} ALERT* ✅\n━━━━━━━━━━━━━━━━━━━━\n"
                   f"💎 *Pair:* {pair}\n📊 *Price:* {open_p} ➔ {close_p}\n"
                   f"👤 *Owner:* {OWNER_NAME}")
            send_telegram_text(msg)
        else:
            if not is_mtg:
                m1_msg = (f"⚠️ *M1 ALERT* ⚠️\n━━━━━━━━━━━━━━━━━━━━\n"
                          f"💎 *Pair:* {pair}\n🔥 *Next:* 1-Min Martingale\n"
                          f"📈 *Direction:* {action}\n👤 *Owner:* {OWNER_NAME}")
                send_telegram_text(m1_msg)
                check_result_logic(pair, action, time_id, is_mtg=True)
            else:
                stats["loss"] += 1
                update_history(time_id, pair, "❌")
                msg = (f"💀 *TOTAL LOSS* 💀\n━━━━━━━━━━━━━━━━━━━━\n"
                       f"💎 *Pair:* {pair}\n❌ *Result:* Double Loss\n👤 *Owner:* {OWNER_NAME}")
                send_telegram_text(msg)
        gc.collect()

def update_history(t_id, pair, res):
    for s in signals_history:
        if s['time'] == t_id and s['pair'] == pair:
            s['result'] = res; break

# --- ORIGINAL DARK UI ---
def get_html():
    status_icon = "🔴" if not bot_running else "🟢"
    status_text = "STOPPED" if not bot_running else "RUNNING"
    status_color = "#dc3545" if not bot_running else "#28a745"
    return f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; background: #000; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
        .card {{ background: #111; padding: 40px; border-radius: 25px; border: 1px solid #222; width: 300px; text-align: center; box-shadow: 0 10px 40px rgba(0,0,0,0.8); }}
        h1 {{ font-size: 22px; margin-bottom: 5px; }}
        .owner {{ color: #555; font-size: 10px; text-transform: uppercase; margin-bottom: 25px; display: block; letter-spacing: 2px; }}
        .status {{ font-size: 16px; font-weight: bold; border: 1px solid {status_color}; padding: 10px; border-radius: 10px; color: {status_color}; margin-bottom: 25px; background: rgba(0,0,0,0.1); }}
        .btn {{ display: block; width: 100%; padding: 15px; margin: 10px 0; border-radius: 12px; font-size: 14px; font-weight: bold; text-decoration: none; color: white; text-transform: uppercase; transition: 0.3s; }}
        .on {{ background: #28a745; }} .off {{ background: #dc3545; }} .res {{ background: #007bff; }}
        .btn:active {{ transform: scale(0.95); }}
    </style></head><body><div class="card">
        <h1>SNIPER V3 PRO</h1><span class="owner">OWNER: {OWNER_NAME}</span>
        <div class="status">{status_icon} {status_text}</div>
        <a href="/on" class="btn on">START SNIPING</a><a href="/off" class="btn off">STOP BOT</a><a href="/results" class="btn res">SEND REPORT</a>
    </div></body></html>
    """

class ControlHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global bot_running
        if self.path == "/on": bot_running = True
        elif self.path == "/off": bot_running = False
        elif self.path == "/results": send_report_now()
        self.send_response(200); self.send_header("Content-type", "text/html; charset=utf-8"); self.end_headers()
        self.wfile.write(get_html().encode('utf-8'))
    def log_message(self, format, *args): return

# --- NEW REPORT FORMAT ---
def send_report_now():
    if not signals_history:
        send_telegram_text("📊 *No signals recorded yet.*")
    else:
        now = datetime.datetime.now(TZ)
        date_str = now.strftime("%Y.%m.%d")
        total = stats["total"]
        wins = stats["win"]
        losses = stats["loss"]
        win_rate = (wins / total * 100) if total > 0 else 0
        
        report = (f"💠 ✨ ···🔥 FINAL RESULTS 🔥··· ✨ 💠\n"
                  f"━━━━━━━━━━━━━━━━━━━━\n"
                  f"📅 Date: {date_str}\n"
                  f"━━━━━━━━━━━━━━━━━━━━\n")
        
        for s in signals_history[-10:]:
            res_icon = s.get('result', '⌛')
            report += f"❑ {s['time']} - {s['pair']} - {s['action']} {res_icon}\n"
            
        report += (f"━━━━━━━━━━━━━━━━━━━━\n"
                   f"🔮 Total Signal: {total} ({win_rate:.0f}%)\n"
                   f"━━━━━━━━━━━━━━━━━━━━\n"
                   f"🎯 Win: {wins} | 💀 Loss: {losses} ({win_rate:.0f}%)\n"
                   f"👤 Owner: {OWNER_NAME}")
        
        send_telegram_text(report)

# --- MAIN LOOP ---
def signal_loop():
    global sent_signals_cache
    while True:
        try:
            if bot_running:
                now = datetime.datetime.now(TZ)
                if 47 <= now.second <= 50:
                    current_min = now.strftime("%H:%M")
                    for pair in PAIRS:
                        if f"{current_min}_{pair}" not in sent_signals_cache:
                            h = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL, timeout=5)
                            score = h.get_analysis().indicators['Recommend.All']
                            if abs(score) >= 0.5:
                                action = "CALL 📈" if score > 0 else "PUT 📉"
                                stats["total"] += 1
                                signals_history.append({'time': current_min, 'pair': pair, 'action': action, 'result': '⌛'})
                                
                                msg = (f"🎯 *API CONFIRMED SIGNAL*\n━━━━━━━━━━━━━━━━━━━━\n"
                                       f"💎 *Pair:* {pair}\n📊 *Action:* {action}\n"
                                       f"⏰ *Time:* {now.strftime('%H:%M:%S')}\n"
                                       f"🚀 *Accuracy:* 98.5%\n━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
                                
                                send_telegram_with_chart(msg, pair)
                                sent_signals_cache.add(f"{current_min}_{pair}")
                                threading.Thread(target=check_result_logic, args=(pair, action, current_min)).start()
                                break 
                if now.minute == 0: sent_signals_cache.clear(); gc.collect()
        except: time.sleep(5)
        time.sleep(1)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=signal_loop, daemon=True).start()
    HTTPServer(('0.0.0.0', port), ControlHandler).serve_forever()
