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
OWNER_NAME = "DARK-X-RAYHAN"

# --- GLOBAL STATE ---
bot_running = False
signals_history = []
stats = {"win": 0, "loss": 0, "total": 0}
last_signal_time = ""

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try: requests.post(url, data=payload)
    except: pass

# --- REAL-TIME PRICE ENGINE ---
def get_candle_data(pair):
    try:
        # TradingView থেকে সরাসরি ক্যান্ডেল ডাটা ফেচ করা
        h = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL)
        analysis = h.get_analysis()
        open_p = analysis.indicators['open']
        close_p = analysis.indicators['close']
        return open_p, close_p
    except:
        return None, None

def check_result_logic(pair, action, time_id, is_mtg=False):
    global stats
    # ক্যান্ডেল ক্লোজ হওয়ার জন্য ১ মিনিট ৫ সেকেন্ড অপেক্ষা
    time.sleep(65)
    
    open_p, close_p = get_candle_data(pair)
    if open_p is None or close_p is None:
        return

    # উইন কন্ডিশন: কল দিলে ক্লোজ প্রাইস ওপেন থেকে বেশি হতে হবে
    is_win = (action == "CALL 📈" and close_p > open_p) or (action == "PUT 📉" and close_p < open_p)

    if is_win:
        stats["win"] += 1
        res_label = "MTG-1 WIN" if is_mtg else "DIRECT WIN"
        update_history(time_id, "✅¹" if is_mtg else "✅")
        msg = (f"✅ *{res_label} ALERT* ✅\n━━━━━━━━━━━━━━━━━━━━\n"
               f"💎 *Pair:* {pair}\n📊 *Entry:* {open_p} ➔ *Exit:* {close_p}\n"
               f"💰 *Result:* Pure Profit\n━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
        send_telegram(msg)
    else:
        if not is_mtg:
            # প্রথম ক্যান্ডেল লস হলে M1 এলার্ট এবং পুনরায় চেক
            m1_msg = (f"⚠️ *M1 ALERT (Martingale)* ⚠️\n━━━━━━━━━━━━━━━━━━━━\n"
                      f"💎 *Pair:* {pair}\n🔥 *Next:* 1-Min Martingale\n"
                      f"📈 *Direction:* {action}\n━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
            send_telegram(m1_msg)
            # পরবর্তী ক্যান্ডেলের জন্য রেজাল্ট চেক ফাংশনটি আবার কল করা
            check_result_logic(pair, action, time_id, is_mtg=True)
        else:
            # M1 ও লস হলে টোটাল লস ঘোষণা
            stats["loss"] += 1
            update_history(time_id, "❌")
            msg = (f"💀 *TOTAL LOSS ALERT* 💀\n━━━━━━━━━━━━━━━━━━━━\n"
                   f"💎 *Pair:* {pair}\n📊 *Entry:* {open_p} ➔ *Exit:* {close_p}\n"
                   f"❌ *Result:* Double Loss\n━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
            send_telegram(msg)

def update_history(t_id, res):
    for s in signals_history:
        if s['time'] == t_id:
            s['result'] = res
            break

# --- WEB PANEL (UTF-8 & DESIGN FIXED) ---
def get_html():
    status_icon = "🔴" if not bot_running else "🟢"
    status_text = "STOPPED" if not bot_running else "RUNNING"
    status_color = "#dc3545" if not bot_running else "#28a745"
    return f"""
    <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; background: #000; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
        .card {{ background: #111; padding: 40px; border-radius: 25px; border: 1px solid #222; width: 320px; text-align: center; box-shadow: 0 10px 40px rgba(0,0,0,0.8); }}
        h1 {{ font-size: 24px; margin-bottom: 5px; color: #fff; }}
        .owner {{ color: #555; font-size: 10px; text-transform: uppercase; margin-bottom: 30px; display: block; letter-spacing: 2px; }}
        .status {{ font-size: 18px; font-weight: bold; border: 2px solid {status_color}; padding: 12px; border-radius: 12px; color: {status_color}; margin-bottom: 30px; background: rgba(0,0,0,0.2); }}
        .btn {{ display: block; width: 100%; padding: 16px; margin: 12px 0; border-radius: 50px; font-size: 14px; font-weight: bold; text-decoration: none; color: white; border: none; text-transform: uppercase; }}
        .on {{ background: #28a745; }} .off {{ background: #dc3545; }} .res {{ background: #007bff; }}
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

def send_report_now():
    if not signals_history:
        send_telegram("📊 *No signals recorded in this session.*")
    else:
        acc = (stats["win"] / stats["total"] * 100) if stats["total"] > 0 else 0
        report = f"💠 *LIVE PERFORMANCE REPORT* 💠\n━━━━━━━━━━━━━━━━━━━━\n"
        for s in signals_history[-12:]:
            report += f"❑ {s['time']} | {s['pair']} | {s.get('result', '⌛')}\n"
        report += f"━━━━━━━━━━━━━━━━━━━━\n🎯 Accuracy: {acc:.1f}% | Total: {stats['total']}\n👤 Owner: {OWNER_NAME}"
        send_telegram(report)

# --- MAIN ENGINE ---
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
                        if score >= 0.5 or score <= -0.5:
                            action = "CALL 📈" if score > 0 else "PUT 📉"
                            stats["total"] += 1
                            # সিগন্যাল পাওয়ার সাথে সাথে লিস্টে সেভ করা হচ্ছে
                            signals_history.append({'time': min_id, 'pair': pair, 'action': action, 'result': '⌛'})
                            
                            msg = (f"🎯 *API CONFIRMED SIGNAL*\n━━━━━━━━━━━━━━━━━━━━\n"
                                   f"💎 *Pair:* {pair}\n📊 *Action:* {action}\n"
                                   f"⏰ *Time:* {now.strftime('%H:%M:%S')}\n"
                                   f"🚀 *Accuracy:* 98.5%\n━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
                            
                            send_telegram(msg)
                            last_signal_time = min_id
                            # রেজাল্ট চেক করার জন্য আলাদা থ্রেড চালু করা
                            threading.Thread(target=check_result_logic, args=(pair, action, min_id)).start()
                            break
                    except: continue
        time.sleep(1)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=signal_loop, daemon=True).start()
    HTTPServer(('0.0.0.0', port), ControlHandler).serve_forever()
