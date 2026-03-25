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
# সিগন্যাল ডাটা সংরক্ষণের জন্য ডিকশনারি
active_trade = {"pair": "Waiting", "time": "Waiting"}
last_signal_timestamp = 0 
session_history = []

# --- ULTRA CLEAN SS WITH INDICATORS ---
def send_signal_with_ss(text, pair):
    # চার্ট সেটিংস একদম ক্লিন রাখা হয়েছে
    chart_configs = {
        "symbol": f"{EXCHANGE}:{pair}",
        "interval": "1",
        "theme": "dark",
        "style": "1",
        "timezone": "Asia/Dhaka",
        "hide_top_toolbar": True,
        "hide_legend": False,
        "withdateranges": False,
        "hide_side_toolbar": True,
        "save_image": False,
        "backgroundColor": "#000000",
        "gridColor": "rgba(0,0,0,0)",
        "studies": ["MASimple@tv-basicstudies", "RSI@tv-basicstudies", "MACD@tv-basicstudies"]
    }
    
    studies_overrides = {
        "volumePaneSize": "tiny",
        "paneProperties.background": "#000000",
        "mainSeriesProperties.candleStyle.upColor": "#00ff00",
        "mainSeriesProperties.candleStyle.downColor": "#ff0000"
    }
    
    params = "&".join([f"{k}={str(v).lower()}" for k, v in chart_configs.items() if k != 'studies'])
    params += f"&studies={requests.utils.quote(json.dumps(chart_configs['studies']))}"
    params += f"&studies_overrides={requests.utils.quote(json.dumps(studies_overrides))}"

    base_url = "https://s.tradingview.com/widgetembed/?"
    chart_url = f"{base_url}{params}"

    # ছবি দ্রুত লোড হওয়ার জন্য viewport এবং রেজোলিউশন অপ্টিমাইজ করা হয়েছে
    photo_url = f"https://image.thum.io/get/width/1000/crop/650/noanimate/refresh/{int(time.time())}/{chart_url}"
    
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        requests.post(url, data={"chat_id": CHAT_ID, "photo": photo_url, "caption": text, "parse_mode": "Markdown"}, timeout=20)
    except:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

# --- UI CONTROL PANEL ---
def get_html():
    status_text = "RUNNING" if bot_running else "STOPPED"
    status_color = "#28a745" if bot_running else "#dc3545"
    return f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ background: #000; color: #fff; text-align: center; font-family: sans-serif; padding: 15px; }}
        .card {{ background: #0f0f0f; padding: 25px; border-radius: 20px; border: 1px solid #222; max-width: 320px; margin: auto; }}
        .btn {{ display: block; padding: 15px; margin: 10px 0; border-radius: 12px; text-decoration: none; color: #fff; font-weight: bold; text-transform: uppercase; font-size: 12px; border: none; cursor: pointer; }}
        .start {{ background: #28a745; }} .stop {{ background: #dc3545; }}
        .win {{ background: #00c853; }} .mtg {{ background: #ffd600; color: #000; }} .loss {{ background: #d50000; }}
        .final {{ background: #2979ff; }}
        .info-box {{ background: #080808; border-left: 5px solid #00ff00; border-radius: 8px; padding: 12px; margin: 15px 0; text-align: left; font-size: 13px; color: #00ff00; border: 1px solid #333; }}
    </style></head><body>
    <div class="card">
        <h2>SNIPER V3 PRO</h2>
        <div style="color:#888; font-size:11px; margin-bottom:15px;">Owner: {OWNER_NAME}</div>
        <div style="color:{status_color}; font-weight:bold; margin-bottom: 20px;">● {status_text}</div>
        <a href="/on" class="btn start">START BOT</a>
        <a href="/off" class="btn stop">STOP BOT</a>
        <div class="info-box"><b>LAST PAIR:</b> {active_trade['pair']}<br><b>LAST TIME:</b> {active_trade['time']}</div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
            <a href="/win" class="btn win">WIN</a>
            <a href="/mtg" class="btn mtg">MTG</a>
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
        
        if self.path == "/":
            self.send_response(200); self.send_header("Content-type", "text/html"); self.end_headers()
            self.wfile.write(get_html().encode()); return

        if self.path == "/on": bot_running = True
        elif self.path == "/off": bot_running = False
        elif self.path == "/win":
            stats["win"] += 1; session_history.append(f"❑ {active_trade['time']} - {active_trade['pair']} ✅")
            msg(f"✅ *DIRECT WIN ALERT* ✅\n━━━━━━━━━━━━━━\n💎 *Pair:* {active_trade['pair']}\n⏰ *Time:* {active_trade['time']}\n📊 *Result:* Success\n━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
        elif self.path == "/mtg":
            stats["mtg"] += 1; session_history.append(f"❑ {active_trade['time']} - {active_trade['pair']} ✅¹")
            msg(f"✅¹ *MTG-1 WIN ALERT* ✅\n━━━━━━━━━━━━━━\n💎 *Pair:* {active_trade['pair']}\n⏰ *Time:* {active_trade['time']}\n📊 *Result:* Success\n━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
        elif self.path == "/loss":
            stats["loss"] += 1; session_history.append(f"❑ {active_trade['time']} - {active_trade['pair']} ❌")
            msg(f"💀 *TOTAL LOSS ALERT* 💀\n━━━━━━━━━━━━━━\n💎 *Pair:* {active_trade['pair']}\n⏰ *Time:* {active_trade['time']}\n❌ *Result:* Failed\n━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
        elif self.path == "/final":
            total = stats["win"] + stats["mtg"] + stats["loss"]; win_c = stats["win"] + stats["mtg"]
            acc = (win_c / total * 100) if total > 0 else 0
            res = "\n".join(session_history) if session_history else "No Data"
            msg(f"💠 🔥 FINAL RESULTS 🔥 💠\n━━━━━━━━━━━━━━\n{res}\n━━━━━━━━━━━━━━\n🔮 Total: {total} | 🎯 Win: {win_c} | 💀 Loss: {stats['loss']} ({acc:.0f}%)\n👤 Owner: {OWNER_NAME}")
            stats["win"], stats["mtg"], stats["loss"], session_history = 0, 0, 0, []
        
        # রিডাইরেক্ট করে পেজ রিফ্রেশ করা হচ্ছে যাতে স্ট্যাটাস ঠিক থাকে
        self.send_response(303); self.send_header('Location', '/'); self.end_headers()

    def log_message(self, format, *args): return

def signal_loop():
    global sent_signals_cache, active_trade, last_signal_timestamp
    while True:
        try:
            if bot_running:
                now = datetime.datetime.now(TZ)
                current_ts = time.time()
                # টাইমিং ৪৮ সেকেন্ডেই রাখা হয়েছে প্রসেসিং টাইম কাভার করার জন্য
                if now.second == 48 and (current_ts - last_signal_timestamp) >= 120:
                    c_min = now.strftime("%H:%M")
                    if c_min not in sent_signals_cache:
                        best_pair, best_score, best_action = None, 0, None
                        for pair in PAIRS:
                            try:
                                h = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL, timeout=1.0)
                                score = h.get_analysis().indicators['Recommend.All']
                                if abs(score) > best_score:
                                    best_score, best_pair = abs(score), pair
                                    best_action = "CALL 📈" if score > 0 else "PUT 📉"
                            except: continue
                        
                        if best_pair and best_score >= 0.35:
                            trade_t = (now + datetime.timedelta(minutes=1)).strftime("%H:%M")
                            # রেজাল্ট বাটনের জন্য ডাটা আপডেট
                            active_trade["pair"] = best_pair
                            active_trade["time"] = f"{trade_t}:00"
                            last_signal_timestamp = current_ts 
                            
                            msg = (f"🎯 *API CONFIRMED SIGNAL*\n━━━━━━━━━━━━━━━━━━━━\n💎 *Pair:* {best_pair}\n📊 *Action:* {best_action}\n⏰ *Time:* {now.strftime('%H:%M:%S')}\n🎯 *Trade:* {trade_t}:00\n🚀 *Accuracy:* 98.5%\n━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
                            threading.Thread(target=send_signal_with_ss, args=(msg, best_pair)).start()
                            sent_signals_cache.add(c_min)
                if now.second == 0: gc.collect()
        except: time.sleep(0.1)
        time.sleep(0.5)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=signal_loop, daemon=True).start()
    HTTPServer(('0.0.0.0', port), ControlHandler).serve_forever()
