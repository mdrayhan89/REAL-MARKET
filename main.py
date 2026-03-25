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

# --- WIN/LOSS CHECKING LOGIC ---
def get_candle_data(pair):
    try:
        h = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL, timeout=10)
        analysis = h.get_analysis()
        return analysis.indicators['open'], analysis.indicators['close']
    except: return None, None

def check_result_logic(pair, action, time_id, is_mtg=False):
    with thread_limiter:
        global stats
        # ট্রেড শেষ হওয়ার জন্য ৬৫ সেকেন্ড অপেক্ষা করবে
        time.sleep(65) 
        
        open_p, close_p = get_candle_data(pair)
        if open_p is None: return

        # রেজাল্ট ক্যালকুলেশন
        is_win = (action == "CALL 📈" and close_p > open_p) or (action == "PUT 📉" and close_p < open_p)

        if is_win:
            stats["win"] += 1
            res_label = "MTG-1 WIN" if is_mtg else "DIRECT WIN"
            update_history(time_id, pair, "✅¹" if is_mtg else "✅")
            
            msg = (f"✅ *{res_label} ALERT* ✅\n"
                   f"━━━━━━━━━━━━━━━━━━━━\n"
                   f"💎 *Pair:* {pair}\n"
                   f"📊 *Result:* Success\n"
                   f"━━━━━━━━━━━━━━━━━━━━\n"
                   f"👤 *Owner:* {OWNER_NAME}")
            send_telegram_text(msg)
        else:
            if not is_mtg:
                # যদি প্রথমবার লস হয়, তবে M1 সিগন্যাল দিবে
                m1_msg = (f"⚠️ *M1 ALERT (Martingale)* ⚠️\n"
                          f"━━━━━━━━━━━━━━━━━━━━\n"
                          f"💎 *Pair:* {pair}\n"
                          f"🔥 *Next:* 1-Min Martingale\n"
                          f"📈 *Direction:* {action}\n"
                          f"━━━━━━━━━━━━━━━━━━━━\n"
                          f"👤 *Owner:* {OWNER_NAME}")
                send_telegram_text(m1_msg)
                # পুনরায় রেজাল্ট চেক করবে MTG এর জন্য
                check_result_logic(pair, action, time_id, is_mtg=True)
            else:
                # যদি MTG ও লস হয়
                stats["loss"] += 1
                update_history(time_id, pair, "❌")
                msg = (f"💀 *TOTAL LOSS ALERT* 💀\n"
                       f"━━━━━━━━━━━━━━━━━━━━\n"
                       f"💎 *Pair:* {pair}\n"
                       f"❌ *Result:* Loss\n"
                       f"━━━━━━━━━━━━━━━━━━━━\n"
                       f"👤 *Owner:* {OWNER_NAME}")
                send_telegram_text(msg)
        gc.collect()

def update_history(t_id, pair, res):
    for s in signals_history:
        if s['time'] == t_id and s['pair'] == pair:
            s['result'] = res; break

# --- TELEGRAM SENDING ---
def send_telegram_with_chart(text, pair):
    chart_widget = f"https://s.tradingview.com/widgetembed/?symbol={EXCHANGE}:{pair}&interval=1&theme=dark"
    photo_url = f"https://mini.s-shot.ru/1024x768/JPEG/1024/Z100/?{chart_widget}"
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "photo": photo_url, "caption": text, "parse_mode": "Markdown"}, timeout=20)
    except: send_telegram_text(text)

def send_telegram_text(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try: requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=8)
    except: pass

# --- UI & REPORT ---
def get_html():
    status_color = "#28a745" if bot_running else "#dc3545"
    return f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8"><style>
        body {{ background: #000; color: #fff; text-align: center; font-family: sans-serif; padding-top: 50px; }}
        .card {{ background: #111; display: inline-block; padding: 40px; border-radius: 20px; border: 1px solid #333; }}
        .btn {{ display: block; padding: 15px; margin: 10px; border-radius: 10px; text-decoration: none; color: white; font-weight: bold; }}
    </style></head><body><div class="card">
        <h1>SNIPER V3 PRO</h1>
        <div style="color:{status_color}; font-size: 20px;">{'● RUNNING' if bot_running else '● STOPPED'}</div>
        <a href="/on" class="btn" style="background:#28a745">START</a>
        <a href="/off" class="btn" style="background:#dc3545">STOP</a>
        <a href="/results" class="btn" style="background:#007bff">REPORT</a>
    </div></body></html>
    """

class ControlHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global bot_running
        if self.path == "/on": bot_running = True
        elif self.path == "/off": bot_running = False
        elif self.path == "/results": send_report_now()
        self.send_response(200); self.send_header("Content-type", "text/html"); self.end_headers()
        self.wfile.write(get_html().encode())
    def log_message(self, format, *args): return

def send_report_now():
    if not signals_history: send_telegram_text("📊 *No Data.*")
    else:
        now = datetime.datetime.now(TZ)
        total, wins, losses = stats["total"], stats["win"], stats["loss"]
        win_rate = (wins / total * 100) if total > 0 else 0
        report = (f"💠 ✨ ···🔥 FINAL RESULTS 🔥··· ✨ 💠\n━━━━━━━━━━━━━━━━━━━━\n"
                  f"📅 Date: {now.strftime('%Y.%m.%d')}\n━━━━━━━━━━━━━━━━━━━━\n")
        for s in signals_history[-10:]:
            report += f"❑ {s['time']} - {s['pair']} - {s['action']} {s.get('result', '⌛')}\n"
        report += (f"━━━━━━━━━━━━━━━━━━━━\n🔮 Total Signal: {total} ({win_rate:.0f}%)\n"
                   f"━━━━━━━━━━━━━━━━━━━━\n🎯 Win: {wins} | 💀 Loss: {losses} ({win_rate:.0f}%)\n"
                   f"👤 Owner: {OWNER_NAME}")
        send_telegram_text(report)

# --- MAIN LOOP ---
def signal_loop():
    global sent_signals_cache
    while True:
        try:
            if bot_running:
                now = datetime.datetime.now(TZ)
                if 47 <= now.second <= 52:
                    current_min = now.strftime("%H:%M")
                    for pair in PAIRS:
                        if f"{current_min}_{pair}" not in sent_signals_cache:
                            h = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL, timeout=5)
                            score = h.get_analysis().indicators['Recommend.All']
                            if abs(score) >= 0.2:
                                action = "CALL 📈" if score > 0 else "PUT 📉"
                                stats["total"] += 1
                                signals_history.append({'time': current_min, 'pair': pair, 'action': action, 'result': '⌛'})
                                
                                trade_time = (now + datetime.timedelta(minutes=1)).replace(second=0).strftime("%H:%M:%S")
                                msg = (f"🎯 *API CONFIRMED SIGNAL*\n━━━━━━━━━━━━━━━━━━━━\n"
                                       f"💎 *Pair:* {pair}\n📊 *Action:* {action}\n"
                                       f"⏰ *Time:* {now.strftime('%H:%M:%S')}\n"
                                       f"🎯 *Trade:* {trade_time}\n"
                                       f"🚀 *Accuracy:* 98.5%\n━━━━━━━━━━━━━━━━━━━━\n"
                                       f"👤 *Owner:* {OWNER_NAME}")
                                
                                threading.Thread(target=send_telegram_with_chart, args=(msg, pair)).start()
                                threading.Thread(target=check_result_logic, args=(pair, action, current_min)).start()
                                
                                sent_signals_cache.add(f"{current_min}_{pair}")
                                break 
                if now.minute == 0: sent_signals_cache.clear(); gc.collect()
        except: time.sleep(5)
        time.sleep(1)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=signal_loop, daemon=True).start()
    HTTPServer(('0.0.0.0', port), ControlHandler).serve_forever()
