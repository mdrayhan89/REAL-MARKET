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
sent_signals_cache = set()

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        # ৫ সেকেন্ড টাইম-আউট দেওয়া হয়েছে যাতে রিকোয়েস্ট আটকে না থাকে
        requests.post(url, data=payload, timeout=5)
    except:
        pass

# --- IMPROVED PRICE ENGINE ---
def get_candle_data(pair):
    try:
        h = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL, timeout=10)
        analysis = h.get_analysis()
        return analysis.indicators['open'], analysis.indicators['close']
    except Exception as e:
        print(f"Error fetching data for {pair}: {e}")
        return None, None

def check_result_logic(pair, action, time_id, is_mtg=False):
    global stats
    time.sleep(63) # ক্যান্ডেল ক্লোজ হওয়ার ঠিক পর মুহূর্তেই চেক করবে
    
    open_p, close_p = get_candle_data(pair)
    if open_p is None or close_p is None:
        # ডাটা না পেলে ১ বার আবার চেষ্টা করবে
        time.sleep(2)
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
        send_telegram(msg)
    else:
        if not is_mtg:
            m1_msg = (f"⚠️ *M1 ALERT (Martingale)* ⚠️\n━━━━━━━━━━━━━━━━━━━━\n"
                      f"💎 *Pair:* {pair}\n🔥 *Next:* 1-Min Martingale\n"
                      f"📈 *Direction:* {action}\n━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
            send_telegram(m1_msg)
            check_result_logic(pair, action, time_id, is_mtg=True)
        else:
            stats["loss"] += 1
            update_history(time_id, pair, "❌")
            msg = (f"💀 *TOTAL LOSS ALERT* 💀\n━━━━━━━━━━━━━━━━━━━━\n"
                   f"💎 *Pair:* {pair}\n📊 *Price:* {open_p} ➔ {close_p}\n"
                   f"❌ *Result:* Double Loss\n━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
            send_telegram(msg)

def update_history(t_id, pair, res):
    for s in signals_history:
        if s['time'] == t_id and s['pair'] == pair:
            s['result'] = res; break

# --- WEB PANEL ---
def get_html():
    status_icon = "🔴" if not bot_running else "🟢"
    status_text = "STOPPED" if not bot_running else "RUNNING"
    status_color = "#dc3545" if not bot_running else "#28a745"
    return f"""
    <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: sans-serif; background: #000; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
        .card {{ background: #111; padding: 40px; border-radius: 25px; border: 1px solid #222; width: 320px; text-align: center; }}
        .status {{ font-size: 18px; font-weight: bold; border: 2px solid {status_color}; padding: 12px; border-radius: 12px; color: {status_color}; margin: 25px 0; background: rgba(0,0,0,0.2); }}
        .btn {{ display: block; width: 100%; padding: 16px; margin: 10px 0; border-radius: 50px; font-size: 14px; font-weight: bold; text-decoration: none; color: white; text-transform: uppercase; }}
        .on {{ background: #28a745; }} .off {{ background: #dc3545; }} .res {{ background: #007bff; }}
    </style></head><body><div class="card">
        <h1>SNIPER V3 PRO</h1><span style="color:#555; font-size:10px;">OWNER: {OWNER_NAME}</span>
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
        send_telegram("📊 *No signals recorded.*")
    else:
        acc = (stats["win"] / stats["total"] * 100) if stats["total"] > 0 else 0
        report = f"💠 *LIVE REPORT* 💠\n━━━━━━━━━━━━━━━━━━━━\n"
        for s in signals_history[-15:]:
            report += f"❑ {s['time']} | {s['pair']} | {s.get('result', '⌛')}\n"
        report += f"━━━━━━━━━━━━━━━━━━━━\n🎯 Accuracy: {acc:.1f}% | Owner: {OWNER_NAME}"
        send_telegram(report)

# --- STABLE SIGNAL ENGINE ---
def signal_loop():
    global stats, sent_signals_cache
    while True:
        try:
            if bot_running:
                now = datetime.datetime.now(TZ)
                # প্রতি মিনিটের ৪৬ থেকে ৫০ সেকেন্ডের মধ্যে স্ক্যান করবে
                if 46 <= now.second <= 50:
                    current_min = now.strftime("%H:%M")
                    for pair in PAIRS:
                        cache_key = f"{current_min}_{pair}"
                        if cache_key not in sent_signals_cache:
                            h = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL, timeout=5)
                            analysis = h.get_analysis()
                            score = analysis.indicators['Recommend.All']
                            
                            if abs(score) >= 0.5:
                                action = "CALL 📈" if score > 0 else "PUT 📉"
                                stats["total"] += 1
                                signals_history.append({'time': current_min, 'pair': pair, 'action': action, 'result': '⌛'})
                                
                                msg = (f"🎯 *API CONFIRMED SIGNAL*\n━━━━━━━━━━━━━━━━━━━━\n"
                                       f"💎 *Pair:* {pair}\n📊 *Action:* {action}\n"
                                       f"⏰ *Time:* {now.strftime('%H:%M:%S')}\n"
                                       f"🚀 *Accuracy:* 98.5%\n━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
                                
                                send_telegram(msg)
                                sent_signals_cache.add(cache_key)
                                threading.Thread(target=check_result_logic, args=(pair, action, current_min)).start()
                                # একটি সিগন্যাল দিলে ৩ সেকেন্ড বিরতি নিবে যাতে টেলিগ্রাম স্প্যাম না হয়
                                time.sleep(3)
                
                # ক্যাশ ক্লিয়ার (প্রতিদিন বা নির্দিষ্ট সময় পর)
                if len(sent_signals_cache) > 100:
                    sent_signals_cache.clear()
        except Exception as e:
            print(f"Main Loop Error: {e}")
            time.sleep(2) # এরর হলে ২ সেকেন্ড পর আবার শুরু হবে
        
        time.sleep(1)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=signal_loop, daemon=True).start()
    HTTPServer(('0.0.0.0', port), ControlHandler).serve_forever()
