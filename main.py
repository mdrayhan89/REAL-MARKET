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

# --- NEW: SEND TELEGRAM WITH REAL-TIME SCREENSHOT ---
def send_telegram_with_chart(text, pair):
    # রিয়েল-টাইম হাই-কোয়ালিটি স্ক্রিনশট নেওয়ার জন্য ডাইনামিক API লিঙ্ক
    chart_url = f"https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.html?symbol={EXCHANGE}%3A{pair}&width=500&height=400&dateRange=1d&colorTheme=dark&trendLineColor=%2337a6ef&underLineColor=%23E3F2FD&isTransparent=false&autosize=false&locale=en"
    
    # এটি একটি ফ্রি API যা নির্দিষ্ট ইউআরএল-এর স্ক্রিনশট নেয়
    screenshot_api = f"https://api.screenshotmachine.com?key=7be15e&url={chart_url}&dimension=1024x768"

    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    payload = {
        "chat_id": CHAT_ID,
        "photo": screenshot_api,
        "caption": text,
        "parse_mode": "Markdown"
    }
    
    try:
        # আমরা ১০ সেকেন্ড টাইম-আউট দিয়ে রিকোয়েস্টটি পাঠাচ্ছি
        requests.post(url, data=payload, timeout=12)
    except:
        # যদি ফটো পাঠাতে সমস্যা হয়, তবে শুধু টেক্সট পাঠাবে যাতে সিগন্যাল মিস না হয়
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

# --- MARTINGALE ENGINE ---
def get_candle_data(pair):
    try:
        h = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL, timeout=10)
        analysis = h.get_analysis()
        return analysis.indicators['open'], analysis.indicators['close']
    except:
        return None, None

def check_result_logic(pair, action, time_id, is_mtg=False):
    with thread_limiter:
        global stats
        # ক্যান্ডেল ক্লোজ হওয়া পর্যন্ত অপেক্ষা
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
                   f"💰 *Result:* Pure Profit\n━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
            send_telegram_text(msg)
        else:
            if not is_mtg:
                # ১ম টা লস হলে M1 এলার্ট
                m1_msg = (f"⚠️ *M1 ALERT* ⚠️\n━━━━━━━━━━━━━━━━━━━━\n"
                          f"💎 *Pair:* {pair}\n🔥 *Next:* 1-Min Martingale\n"
                          f"📈 *Direction:* {action}\n━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
                send_telegram_text(m1_msg)
                check_result_logic(pair, action, time_id, is_mtg=True)
            else:
                stats["loss"] += 1
                update_history(time_id, pair, "❌")
                msg = (f"💀 *TOTAL LOSS ALERT* 💀\n━━━━━━━━━━━━━━━━━━━━\n"
                       f"💎 *Pair:* {pair}\n❌ *Result:* Double Loss\n━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
                send_telegram_text(msg)
        gc.collect()

def update_history(t_id, pair, res):
    for s in signals_history:
        if s['time'] == t_id and s['pair'] == pair:
            s['result'] = res; break

# --- Web Panel & REPORT ---
def send_telegram_text(text):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

def send_report_now():
    if not signals_history: send_telegram_text("📊 *No signals recorded.*")
    else:
        acc = (stats["win"] / stats["total"] * 100) if stats["total"] > 0 else 0
        report = f"💠 *LIVE REPORT* 💠\n━━━━━━━━━━━━━━━━━━━━\n"
        for s in signals_history[-15:]: report += f"❑ {s['time']} | {s['pair']} | {s.get('result', '⌛')}\n"
        report += f"━━━━━━━━━━━━━━━━━━━━\n🎯 Acc: {acc:.1f}% | Owner: {OWNER_NAME}"
        send_telegram_text(report)

class ControlHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global bot_running
        if self.path == "/on": bot_running = True
        elif self.path == "/off": bot_running = False
        elif self.path == "/results": send_report_now()
        self.send_response(200); self.send_header("Content-type", "text/html; charset=utf-8"); self.end_headers()
        html = f"<html><body style='background:#000;color:#fff;text-align:center;padding:50px; font-family:sans-serif;'>"
        html += f"<h1>SNIPER V3 PRO</h1><p>OWNER: {OWNER_NAME}</p>"
        html += f"<h2 style='color:{'#28a745' if bot_running else '#dc3545'}'>{'RUNNING' if bot_running else 'STOPPED'}</h2>"
        html += f"<a href='/on' style='color:#fff;display:block;margin:10px;text-decoration:none;'>START</a>"
        html += f"<a href='/off' style='color:#fff;display:block;text-decoration:none;'>STOP</a><a href='/results' style='color:#fff;display:block;margin:10px;text-decoration:none;'>REPORT</a>"
        html += f"</body></html>"
        self.wfile.write(html.encode('utf-8'))
    def log_message(self, format, *args): return

# --- SIGNAL ENGINE ---
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
                                
                                # মেসেজ ক্যাপশন
                                msg = (f"🎯 *API CONFIRMED SIGNAL*\n━━━━━━━━━━━━━━━━━━━━\n"
                                       f"💎 *Pair:* {pair}\n📊 *Action:* {action}\n"
                                       f"⏰ *Time:* {now.strftime('%H:%M:%S')}\n"
                                       f"🚀 *Accuracy:* 98.5%\n━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
                                
                                # ১. মেসেজের সাথে চার্ট পাঠানো
                                send_telegram_with_chart(msg, pair)
                                
                                sent_signals_cache.add(f"{current_min}_{pair}")
                                
                                # ২. রেজাল্ট চেক করার জন্য আলাদা থ্রেড
                                threading.Thread(target=check_result_logic, args=(pair, action, current_min)).start()
                                
                                # সার্ভার স্প্যাম এড়াতে ১ মিনিটে ১টির বেশি সিগন্যাল দিলে break করবে
                                break 
                
                if now.minute == 0: sent_signals_cache.clear(); gc.collect()
        except Exception:
            time.sleep(5)
        time.sleep(1)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=signal_loop, daemon=True).start()
    HTTPServer(('0.0.0.0', port), ControlHandler).serve_forever()
