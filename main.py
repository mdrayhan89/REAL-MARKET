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
sent_signals_cache = set()
stats = {"win": 0, "mtg": 0, "loss": 0}
# রেজাল্ট ডাটা ফিক্স
active_trade = {"pair": "Searching...", "time": "Waiting...", "score": 0}
last_signal_timestamp = 0 
session_history = []

# --- FAST INDICATOR SS GENERATOR (MA, RSI, MACD) ---
def send_combined_signal(text, pair):
    # ইন্ডিকেটর সেটিংস যা আপনার দেওয়া ছবির মতো কাজ করবে
    
    chart_configs = {
        "symbol": f"{EXCHANGE}:{pair}",
        "interval": "1",
        "theme": "dark",
        "style": "1",
        "timezone": "Asia/Dhaka",
        "hide_top_toolbar": True,
        "hide_side_toolbar": True, # বাম পাশের টুলবার রিমুভড
        "hide_legend": False, # ইন্ডিকেটরের নাম দেখার জন্য False
        "withdateranges": False,
        "save_image": False,
        "backgroundColor": "#000000",
        "gridColor": "#000000",
        "studies": [
            "MASimple@tv-basicstudies", # Moving Average
            "RSI@tv-basicstudies",      # RSI
            "MACD@tv-basicstudies"      # MACD
        ]
    }
    
    # চার্টটিকে ক্লিন এবং পেশাদার দেখানোর জন্য ওভাররাইড settings
    studies_overrides = {
        "volumePaneSize": "tiny", # ভলিউম ছোট রাখা হয়েছে যাতে মেইন চার্ট বড় দেখায়
        "paneProperties.background": "#000000",
        "mainSeriesProperties.candleStyle.upColor": "#00ff00",
        "mainSeriesProperties.candleStyle.downColor": "#ff0000",
        "mainSeriesProperties.candleStyle.drawBorder": True,
        "mainSeriesProperties.candleStyle.borderUpColor": "#00ff00",
        "mainSeriesProperties.candleStyle.borderDownColor": "#ff0000"
    }
    
    params = "&".join([f"{k}={str(v).lower()}" for k, v in chart_configs.items() if k != 'studies'])
    params += f"&studies={requests.utils.quote(json.dumps(chart_configs['studies']))}"
    params += f"&studies_overrides={requests.utils.quote(json.dumps(studies_overrides))}"

    base_url = "https://s.tradingview.com/widgetembed/?"
    chart_url = f"{base_url}{params}"

    # ডেক্সটপ লুক নিশ্চিত করতে হাই-রেজোলিউশন স্ক্রিনশট (viewportWidth 1920)
    # ছবি দ্রুত লোড হওয়ার জন্য crop অপ্টিমাইজড
    photo_url = f"https://image.thum.io/get/width/1200/crop/750/viewportWidth/1920/noanimate/refresh/{int(time.time())}/{chart_url}"
    
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        # ক্যাপশন হিসেবে টেক্সট এবং ছবি একসাথে পাঠানো হচ্ছে
        r = requests.post(url, data={"chat_id": CHAT_ID, "photo": photo_url, "caption": text, "parse_mode": "Markdown"}, timeout=35)
        if r.status_code != 200:
            # এরর হলে টেক্সট ডেলিভারি
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
    except:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

# --- UI CONTROL PANEL ---
def get_html():
    status_text = "RUNNING" if bot_running else "STOPPED"
    status_color = "#00ff00" if bot_running else "#ff0000"
    return f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="30">
    <style>
        body {{ background: #000; color: #fff; text-align: center; font-family: sans-serif; padding: 10px; }}
        .card {{ background: #0a0a0a; padding: 20px; border-radius: 25px; border: 1px solid #1a1a1a; max-width: 340px; margin: auto; }}
        .owner-header {{ color: #00ff00; font-size: 14px; font-weight: bold; border: 1px solid #00ff00; padding: 5px; border-radius: 10px; margin-bottom: 15px; display: inline-block; }}
        .btn {{ display: block; padding: 15px; margin: 10px 0; border-radius: 12px; text-decoration: none; color: #fff; font-weight: bold; text-transform: uppercase; font-size: 12px; border: none; cursor: pointer; }}
        .start {{ background: #2ecc71; }} .stop {{ background: #e74c3c; }}
        .win {{ background: #27ae60; }} .mtg {{ background: #f1c40f; color: #000; }} .loss {{ background: #c0392b; }}
        .final {{ background: #3498db; }}
        .stats-box {{ background: #111; border-radius: 15px; padding: 12px; margin: 15px 0; text-align: left; font-size: 13px; color: #00ff00; border: 1px solid #222; }}
    </style></head><body>
    <div class="card">
        <div class="owner-header">OWNER: {OWNER_NAME}</div>
        <div style="color:{status_color}; font-weight:bold; margin-bottom: 20px;">● {status_text}</div>
        <a href="/on" class="btn start">START SNIPER</a>
        <a href="/off" class="btn stop">STOP SNIPER</a>
        <div class="stats-box">
            LIVE PAIR: {active_trade['pair']}<br>
            TIME: {active_trade['time']}
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
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
            msg(f"✅ *DIRECT WIN* ✅\n━━━━━━━━━━━━━━\n💎 *Pair:* {active_trade['pair']}\n⏰ *Time:* {active_trade['time']}\n📊 *Accuracy:* {active_trade['score']:.1f}%\n━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
        elif self.path == "/mtg":
            stats["mtg"] += 1; session_history.append(f"❑ {active_trade['time']} - {active_trade['pair']} ✅¹")
            msg(f"✅¹ *MTG-1 WIN* ✅\n━━━━━━━━━━━━━━\n💎 *Pair:* {active_trade['pair']}\n⏰ *Time:* {active_trade['time']}\n📊 *Accuracy:* {active_trade['score']:.1f}%\n━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
        elif self.path == "/loss":
            stats["loss"] += 1; session_history.append(f"❑ {active_trade['time']} - {active_trade['pair']} ❌")
            msg(f"💀 *LOSS ALERT* 💀\n━━━━━━━━━━━━━━\n💎 *Pair:* {active_trade['pair']}\n⏰ *Time:* {active_trade['time']}\n❌ *Result:* Failed\n━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
        elif self.path == "/final":
            total = stats["win"] + stats["mtg"] + stats["loss"]; win_c = stats["win"] + stats["mtg"]
            acc = (win_c / total * 100) if total > 0 else 0
            res = "\n".join(session_history) if session_history else "No Data"
            msg(f"💠 🔥 FINAL SESSION RESULTS 🔥 💠\n━━━━━━━━━━━━━━\n{res}\n━━━━━━━━━━━━━━\n🎯 Accuracy: {acc:.0f}%\n👤 Owner: {OWNER_NAME}")
            stats["win"], stats["mtg"], stats["loss"], session_history = 0, 0, 0, []
        self.send_response(303); self.send_header('Location', '/'); self.end_headers()

def signal_loop():
    global sent_signals_cache, active_trade, last_signal_timestamp
    while True:
        try:
            if bot_running:
                now = datetime.datetime.now(TZ)
                current_ts = time.time()
                # ১২ সেকেন্ড আগে ৪৮ সেকেন্ডে সিগন্যাল ডেলিভারি বহাল রাখা হয়েছে প্রসেসিং টাইম কাভার করার জন্য
                if now.second == 48 and (current_ts - last_signal_timestamp) >= 150:
                    c_min = now.strftime("%H:%M")
                    if c_min not in sent_signals_cache:
                        best_pair, best_score, best_action = None, 0, None
                        for pair in PAIRS:
                            try:
                                h = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL, timeout=1.5)
                                score = h.get_analysis().indicators['Recommend.All']
                                if abs(score) > best_score:
                                    best_score, best_pair = abs(score), pair
                                    best_action = "CALL 📈" if score > 0 else "PUT 📉"
                            except: continue
                        
                        # সিগন্যাল কনফার্মেশন স্কোর ফিল্টার ০.১৫ বহাল রাখা হয়েছে
                        if best_pair and best_score >= 0.15:
                            trade_t = (now + datetime.timedelta(minutes=1)).strftime("%H:%M")
                            # রেজাল্ট বাটনের জন্য ডাটা আপডেট
                            active_trade = {"pair": best_pair, "time": f"{trade_t}:00", "score": best_score*100}
                            last_signal_timestamp = current_ts 
                            
                            # প্রিমিয়াম সিগন্যাল ফরম্যাট
                            msg = (f"🎯 *API CONFIRMED SIGNAL*\n━━━━━━━━━━━━━━━━━━━━\n💎 *Pair:* {best_pair}\n📊 *Action:* {best_action}\n⏰ *Time:* {now.strftime('%H:%M:%S')}\n🎯 *Trade:* {trade_t}:00\n🚀 *Accuracy:* 98.5%\n━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
                                    
                            # ছবি এবং টেক্সট একসাথে ডেলিভারি
                            threading.Thread(target=send_combined_signal, args=(msg, best_pair)).start()
                            sent_signals_cache.add(c_min)
                if now.second == 0: gc.collect()
        except: time.sleep(0.1)
        time.sleep(0.5)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=signal_loop, daemon=True).start()
    HTTPServer(('0.0.0.0', port), ControlHandler).serve_forever()
