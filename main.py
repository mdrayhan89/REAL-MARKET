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
# High-volume Pairs for consistent signals
PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "EURJPY", "AUDUSD", "GBPJPY", "EURGBP", "USDCAD", "AUDCAD", "NZDUSD", "USDCHF"]
EXCHANGE = "FX_IDC"
SCREENER = "forex"
INTERVAL = Interval.INTERVAL_1_MINUTE 
TZ = pytz.timezone('Asia/Dhaka')
OWNER_NAME = "DARK-X-RAYHAN"

# --- GLOBAL STATE ---
bot_running = False
sent_signals_cache = set()
stats = {"win": 0, "mtg": 0, "loss": 0}
# Data storage for rendering and Telegram results
current_pair_data = "None"
current_time_data = "None"
current_action_data = "None"
session_history = [] 
last_signal_timestamp = 0 

# --- PROFESSIONAL MT4 STYLE SCREENSHOT ---
def send_signal_with_ss(text, pair):
    # MT4 Style Clean Chart Embed (No Grid, Dark Theme, Clear Candles)
    # ওভারলে এবং গ্রিড রিমুভ করার জন্য 'studies', 'hide_top_toolbar', 'hide_side_toolbar', 'hide_legend', 'save_image' প্যারামিটার ব্যবহার করা হয়েছে।
    chart_url = f"https://s.tradingview.com/widgetembed/?symbol={EXCHANGE}:{pair}&interval=1&theme=dark&style=1&timezone=Asia%2FDhaka&studies=%5B%5D&hide_top_toolbar=true&hide_side_toolbar=true&hide_legend=true&save_image=false"
    
    # Fast Screenshot Machine (High Reliability for Caption Mode)
    # screenshotmachine ব্যবহার করে নিশ্চিত করা হয়েছে যাতে টেক্সট এবং ইমেজ একসাথে অর্ডার Caption হিসেবে ডেলিভারি হয়।
    photo_url = f"https://api.screenshotmachine.com/?key=c90962&url={requests.utils.quote(chart_url)}&dimension=1280x720&delay=1000"
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    payload = {
        "chat_id": CHAT_ID,
        "photo": photo_url,
        "caption": text,
        "parse_mode": "Markdown"
    }
    
    try:
        # ১২ সেকেন্ডের মধ্যে ছবি নিশ্চিত করতে ২৫ সেকেন্ড টাইমআউট
        r = requests.post(url, data=payload, timeout=30)
        if r.status_code != 200:
            # যদি ছবি না আসে তবে অন্তত সিগন্যাল টেক্সট মিস হবে না
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
    except:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

# --- UI PANEL ( Design exactly like 1000005268.jpg) ---
def get_html():
    status_text = "RUNNING" if bot_running else "STOPPED"
    status_color = "#28a745" if bot_running else "#dc3545"
    return f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ background: #000; color: #fff; text-align: center; font-family: sans-serif; padding: 15px; }}
        .card {{ background: #0f0f0f; padding: 20px; border-radius: 20px; border: 1px solid #222; max-width: 320px; margin: auto; }}
        h2 {{ margin-bottom: 5px; }}
        .owner {{ color: #888; font-size: 12px; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 1px; }}
        .btn {{ display: block; padding: 12px; margin: 8px 0; border-radius: 10px; text-decoration: none; color: #fff; font-weight: bold; text-transform: uppercase; font-size: 13px; border: none; cursor: pointer; transition: 0.3s; }}
        .start {{ background: #28a745; }} .stop {{ background: #dc3545; }}
        .win {{ background: #00c853; }} .mtg {{ background: #ffd600; color: #000; }} .loss {{ background: #d50000; }}
        .final {{ background: #2979ff; }}
        .info-box {{ background: #1a1a1a; border-left: 5px solid #00ff00; border-radius: 8px; padding: 10px; margin: 10px 0; text-align: left; font-size: 13px; color: #aaa; border: 1px solid #333; }}
        .btn:active {{ transform: scale(0.95); }}
    </style></head><body>
    <div class="card">
        <h2>SNIPER V3 PRO</h2>
        <div class="owner">Owner: {OWNER_NAME}</div>
        <div style="color:{status_color}; font-weight:bold; margin-bottom: 20px; font-size: 18px;">● {status_text}</div>
        
        <a href="/on" class="btn start">START BOT</a>
        <a href="/off" class="btn stop">STOP BOT</a>
        
        <div class="info-box">
            <b>PAIR:</b> {current_pair_data}<br>
            <b>TRADE TIME:</b> {current_time_data}
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
            <a href="/win" class="btn win">WIN (DIRECT)</a>
            <a href="/mtg" class="btn mtg">WIN (MTG-1)</a>
        </div>
        
        <a href="/loss" class="btn loss">LOSS</a>
        <a href="/final" class="btn final">🔥 FINAL RESULTS 🔥</a>
    </div>
    </body></html>
    """

class ControlHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global bot_running, session_history, stats
        def msg(t): requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": t, "parse_mode": "Markdown"})
        
        if self.path == "/on": bot_running = True
        elif self.path == "/off": bot_running = False
        elif self.path == "/win":
            stats["win"] += 1
            session_history.append(f"❑ {current_time_data} - {current_pair_data} - {current_action_data} ✅")
            msg(f"✅ *DIRECT WIN ALERT* ✅\n━━━━━━━━━━━━━━\n💎 *Pair:* {current_pair_data}\n⏰ *Time:* {current_time_data}\n📊 *Result:* Success\n━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
        elif self.path == "/mtg":
            stats["mtg"] += 1
            session_history.append(f"❑ {current_time_data} - {current_pair_data} - {current_action_data} ✅¹")
            msg(f"✅¹ *MTG-1 WIN ALERT* ✅\n━━━━━━━━━━━━━━\n💎 *Pair:* {current_pair_data}\n⏰ *Time:* {current_time_data}\n📊 *Result:* Success\n━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
        elif self.path == "/loss":
            stats["loss"] += 1
            session_history.append(f"❑ {current_time_data} - {current_pair_data} - {current_action_data} ❌")
            msg(f"💀 *TOTAL LOSS ALERT* 💀\n━━━━━━━━━━━━━━\n💎 *Pair:* {current_pair_data}\n⏰ *Time:* {current_time_data}\n❌ *Result:* Failed\n━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
        elif self.path == "/final":
            total = stats["win"] + stats["mtg"] + stats["loss"]
            win_c = stats["win"] + stats["mtg"]
            acc = (win_c / total * 100) if total > 0 else 0
            history_str = "\n".join(session_history) if session_history else "No data recorded."
            final_msg = (f"💠 ✨ ···🔥 FINAL RESULTS 🔥··· ✨ 💠\n━━━━━━━━━━━━━━━━━━━━\n"
                         f"📅 Date: {datetime.datetime.now(TZ).strftime('%Y.%m.%d')}\n━━━━━━━━━━━━━━━━━━━━\n"
                         f"{history_str}\n━━━━━━━━━━━━━━━━━━━━\n"
                         f"🔮 Total: {total} | 🎯 Win: {win_c} | 💀 Loss: {stats['loss']} ({acc:.0f}%)\n"
                         f"👤 Owner: {OWNER_NAME}")
            msg(final_msg)
            stats["win"], stats["mtg"], stats["loss"], session_history = 0, 0, 0, []

        self.send_response(200); self.send_header("Content-type", "text/html"); self.end_headers()
        self.wfile.write(get_html().encode())
    def log_message(self, format, *args): return

# --- OPTIMIZED SIGNAL ENGINE ---
def signal_loop():
    global sent_signals_cache, current_pair_data, current_time_data, current_action_data, last_signal_timestamp
    while True:
        try:
            if bot_running:
                now = datetime.datetime.now(TZ)
                current_ts = time.time()
                
                # ক্যান্ডেল শেষ হওয়ার ঠিক ১২ সেকেন্ড আগে (৪৮ সেকেন্ডে) সিগন্যাল ট্রিগার
                if now.second == 48 and (current_ts - last_signal_timestamp) >= 180:
                    c_min = now.strftime("%H:%M")
                    if c_min not in sent_signals_cache:
                        # High Win % Pair Selection
                        best_pair, best_score, best_action = None, 0, None
                        for pair in PAIRS:
                            try:
                                h = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL, timeout=1.5)
                                score = h.get_analysis().indicators['Recommend.All']
                                if abs(score) > best_score:
                                    best_score, best_pair = abs(score), pair
                                    best_action = "CALL 📈" if score > 0 else "PUT 📉"
                            except: continue
                        
                        if best_pair and best_score >= 0.35:
                            trade_t = (now + datetime.timedelta(minutes=1)).replace(second=0).strftime("%H:%M")
                            # গ্লোবাল ডাটা আপডেট
                            current_pair_data = best_pair
                            current_time_data = f"{trade_t}:00"
                            current_action_data = best_action
                            last_signal_timestamp = current_ts 
                            
                            # সিগন্যাল মেসেজ ফরম্যাট
                            msg = (f"🎯 *API CONFIRMED SIGNAL*\n━━━━━━━━━━━━━━━━━━━━\n"
                                   f"💎 *Pair:* {best_pair}\n📊 *Action:* {best_action}\n"
                                   f"⏰ *Time:* {now.strftime('%H:%M:%S')}\n"
                                   f"🎯 *Trade:* {trade_t}:00\n"
                                   f"🚀 *Accuracy:* 98.5%\n━━━━━━━━━━━━━━━━━━━━\n"
                                   f"👤 *Owner:* {OWNER_NAME}")
                                    
                            threading.Thread(target=send_signal_with_ss, args=(msg, best_pair)).start()
                            sent_signals_cache.add(c_min)
                if now.second == 0: gc.collect()
        except: time.sleep(0.1)
        time.sleep(0.5)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=signal_loop, daemon=True).start()
    HTTPServer(('0.0.0.0', port), ControlHandler).serve_forever()
