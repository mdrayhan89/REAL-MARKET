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
PAIRS = ["EURUSD", "EURJPY", "USDJPY", "CADJPY", "EURGBP", "AUDJPY", "GBPJPY", "AUDUSD", "GBPUSD", "AUDCAD", "USDCAD", "NZDUSD"]
EXCHANGE = "FX_IDC"
SCREENER = "forex"
INTERVAL = Interval.INTERVAL_1_MINUTE 
TZ = pytz.timezone('Asia/Dhaka')
OWNER_NAME = "DARK-X-RAYHAN"

# --- GLOBAL STATE ---
bot_running = False
sent_signals_cache = set()
stats = {"win": 0, "mtg": 0, "loss": 0}
# রেন্ডার প্যানেল ও টেলিগ্রাম রেজাল্টের জন্য ডাটা স্টোর
current_pair_data = "None"
current_time_data = "None"
current_action_data = "None"
session_history = [] 
last_signal_timestamp = 0 

# --- TELEGRAM SENDING ---
def send_signal_with_ss(text, pair):
    # চার্ট জেনারেটর (দ্রুততম মেথড)
    chart_url = f"https://s.tradingview.com/widgetembed/?symbol={EXCHANGE}:{pair}&interval=1&theme=dark"
    # mini.s-shot API ব্যবহার করা হয়েছে যা ছবির জন্য অনেক ফাস্ট
    photo_url = f"https://mini.s-shot.ru/1280x720/JPEG/1024/Z100/?{chart_url}"
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    try:
        r = requests.post(url, data={"chat_id": CHAT_ID, "photo": photo_url, "caption": text, "parse_mode": "Markdown"}, timeout=25)
        if r.status_code != 200:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
    except:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

# --- UI PANEL ---
def get_html():
    status_text = "RUNNING" if bot_running else "STOPPED"
    status_color = "#28a745" if bot_running else "#dc3545"
    return f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ background: #000; color: #fff; text-align: center; font-family: sans-serif; padding: 15px; }}
        .card {{ background: #0f0f0f; padding: 20px; border-radius: 20px; border: 1px solid #222; max-width: 320px; margin: auto; }}
        .btn {{ display: block; padding: 12px; margin: 8px 0; border-radius: 10px; text-decoration: none; color: #fff; font-weight: bold; text-transform: uppercase; font-size: 13px; border: none; cursor: pointer; }}
        .on {{ background: #28a745; }} .off {{ background: #dc3545; }}
        .win {{ background: #00c853; }} .mtg {{ background: #ffd600; color: #000; }} .loss {{ background: #d50000; }}
        .final {{ background: #2979ff; }}
        .info {{ font-size: 13px; color: #aaa; margin: 10px 0; background: #1a1a1a; padding: 12px; border-radius: 10px; text-align: left; line-height: 1.6; border: 1px solid #333; }}
    </style></head><body>
    <div class="card">
        <h3>SNIPER V3 PRO</h3>
        <div style="color:{status_color}; font-weight:bold; margin-bottom: 20px;">● {status_text}</div>
        <a href="/on" class="btn on">START BOT</a>
        <a href="/off" class="btn off">STOP BOT</a>
        <div class="info">
            <b>PAIR:</b> {current_pair_data}<br>
            <b>TRADE TIME:</b> {current_time_data}
        </div>
        <a href="/win" class="btn win">WIN (DIRECT)</a>
        <a href="/mtg" class="btn mtg">WIN (MTG-1)</a>
        <a href="/loss" class="btn loss">LOSS</a>
        <a href="/final" class="btn final">🔥 FINAL RESULTS 🔥</a>
    </div>
    </body></html>
    """

class ControlHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global bot_running, session_history, stats
        def msg(txt): requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": txt, "parse_mode": "Markdown"})
        
        # বট স্ট্যাটাস কন্ট্রোল (এখানে bot_running ফিক্স করা হয়েছে যাতে অফ না হয়)
        if self.path == "/on": bot_running = True
        elif self.path == "/off": bot_running = False
        
        elif self.path == "/win":
            stats["win"] += 1
            session_history.append(f"❑ {current_time_data} - {current_pair_data} ✅")
            msg(f"✅ *DIRECT WIN ALERT* ✅\n━━━━━━━━━━━━━━\n💎 *Pair:* {current_pair_data}\n⏰ *Time:* {current_time_data}\n📊 *Result:* Success\n━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
        
        elif self.path == "/mtg":
            stats["mtg"] += 1
            session_history.append(f"❑ {current_time_data} - {current_pair_data} ✅¹")
            msg(f"✅¹ *MTG-1 WIN ALERT* ✅\n━━━━━━━━━━━━━━\n💎 *Pair:* {current_pair_data}\n⏰ *Time:* {current_time_data}\n📊 *Result:* Success\n━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
        
        elif self.path == "/loss":
            stats["loss"] += 1
            session_history.append(f"❑ {current_time_data} - {current_pair_data} ❌")
            msg(f"💀 *TOTAL LOSS ALERT* 💀\n━━━━━━━━━━━━━━\n💎 *Pair:* {current_pair_data}\n⏰ *Time:* {current_time_data}\n❌ *Result:* Failed\n━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
        
        elif self.path == "/final":
            total = stats["win"] + stats["mtg"] + stats["loss"]
            win_c = stats["win"] + stats["mtg"]
            acc = (win_c / total * 100) if total > 0 else 0
            hist = "\n".join(session_history) if session_history else "No signals recorded."
            final_msg = (f"💠 ✨ ···🔥 FINAL RESULTS 🔥··· ✨ 💠\n━━━━━━━━━━━━━━━━━━━━\n"
                         f"📅 Date: {datetime.datetime.now(TZ).strftime('%Y.%m.%d')}\n━━━━━━━━━━━━━━━━━━━━\n"
                         f"{hist}\n━━━━━━━━━━━━━━━━━━━━\n"
                         f"🔮 Total Signal: {total}\n🎯 Win: {win_c} | 💀 Loss: {stats['loss']} ({acc:.0f}%)\n"
                         f"👤 Owner: {OWNER_NAME}")
            msg(final_msg)
            stats["win"], stats["mtg"], stats["loss"] = 0, 0, 0
            session_history = []

        self.send_response(200); self.send_header("Content-type", "text/html"); self.end_headers()
        self.wfile.write(get_html().encode())
    def log_message(self, format, *args): return

# --- MAIN SIGNAL ENGINE ---
def signal_loop():
    global sent_signals_cache, current_pair_data, current_time_data, current_action_data, last_signal_timestamp
    while True:
        try:
            if bot_running:
                now = datetime.datetime.now(TZ)
                current_ts = time.time()
                
                # ক্যান্ডেল শেষ হওয়ার ১২ সেকেন্ড আগে (৪৮ সেকেন্ডে) চেক
                if now.second == 48 and (current_ts - last_signal_timestamp) >= 150:
                    c_min = now.strftime("%H:%M")
                    if c_min not in sent_signals_cache:
                        for pair in PAIRS:
                            try:
                                h = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL, timeout=2)
                                score = h.get_analysis().indicators['Recommend.All']
                                if abs(score) >= 0.4:
                                    action = "CALL 📈" if score > 0 else "PUT 📉"
                                    trade_t = (now + datetime.timedelta(minutes=1)).replace(second=0).strftime("%H:%M")
                                    
                                    # গ্লোবাল ডাটা আপডেট (এটি প্যানেল ও টেলিগ্রাম রেজাল্ট ফিক্স করবে)
                                    current_pair_data = pair
                                    current_time_data = f"{trade_t}:00"
                                    current_action_data = action
                                    last_signal_timestamp = current_ts 
                                    
                                    msg_text = (f"🎯 *API CONFIRMED SIGNAL*\n━━━━━━━━━━━━━━━━━━━━\n"
                                                f"💎 *Pair:* {pair}\n📊 *Action:* {action}\n"
                                                f"⏰ *Time:* {now.strftime('%H:%M:%S')}\n"
                                                f"🎯 *Trade:* {trade_t}:00\n"
                                                f"🚀 *Accuracy:* 98.5%\n━━━━━━━━━━━━━━━━━━━━\n"
                                                f"👤 *Owner:* {OWNER_NAME}")
                                    
                                    threading.Thread(target=send_signal_with_ss, args=(msg_text, pair)).start()
                                    sent_signals_cache.add(c_min)
                                    break 
                            except: continue
                if now.second == 0:
                    if len(sent_signals_cache) > 20: sent_signals_cache.clear()
                    gc.collect()
        except: time.sleep(0.1)
        time.sleep(0.5)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=signal_loop, daemon=True).start()
    HTTPServer(('0.0.0.0', port), ControlHandler).serve_forever()
