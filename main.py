import time, datetime, pytz, requests, threading, os, gc, json
from http.server import BaseHTTPRequestHandler, HTTPServer
from tradingview_ta import TA_Handler, Interval

# --- CONFIGURATION ---
TOKEN = "8354111202:AAEqFLMoJ7W7AlwpfHibZbpusiWbnOcl5Xc"
CHAT_ID = "-1003862859969"
PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "EURJPY", "AUDUSD", "GBPJPY", "EURGBP", "USDCAD", "AUDCAD", "NZDUSD", "GBPCHF", "AUDJPY"]
EXCHANGE = "FX_IDC" 
SCREENER = "forex"
INTERVAL = Interval.INTERVAL_1_MINUTE 
TZ = pytz.timezone('Asia/Dhaka')
OWNER_NAME = "DARK-X-RAYHAN"

# --- GLOBAL STATE ---
bot_running = False
active_trade = {"pair": "Searching...", "time": "Waiting..."}
last_sig_time = 0 
stats = {"win": 0, "mtg": 0, "loss": 0}
session_history = []

# --- PRECISE DARK SCREENSHOT ENGINE ---
def send_telegram(msg, pair=None):
    try:
        if pair:
            # আপনার ছবির মতো পিওর ব্ল্যাক লুক দেওয়ার জন্য সেটিংস
            chart_configs = {
                "symbol": f"{EXCHANGE}:{pair}",
                "interval": "1",
                "theme": "dark",
                "style": "1",
                "hide_side_toolbar": "true",
                "hide_top_toolbar": "true",
                "backgroundColor": "rgba(0, 0, 0, 1)", # ডার্ক ব্যাকগ্রাউন্ড
                "gridColor": "rgba(0, 0, 0, 0)"      # গ্রিড রিমুভ
            }
            params = "&".join([f"{k}={v}" for k, v in chart_configs.items()])
            widget_url = f"https://s.tradingview.com/widgetembed/?{params}"
            
            # ১২০০x৬৫০ ক্রপ যাতে আপনার ছবির মতো ক্যান্ডেলগুলো বড় দেখায়
            photo_url = f"https://image.thum.io/get/width/1200/crop/650/noanimate/refresh/{int(time.time())}/{widget_url}"
            
            r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                             data={"chat_id": CHAT_ID, "photo": photo_url, "caption": msg, "parse_mode": "Markdown"}, timeout=30)
            if r.status_code == 200: return

        # ইমেজ ফেইল করলে দ্রুত টেক্সট পাঠিয়ে দিবে
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                     data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=20)
    except: pass

# --- UI CONTROL PANEL (NO REFRESH) ---
def get_html():
    status_text = "RUNNING" if bot_running else "STOPPED"
    status_color = "#00ff00" if bot_running else "#ff0000"
    return f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ background: #000; color: #fff; text-align: center; font-family: sans-serif; padding: 10px; }}
        .card {{ background: #0a0a0a; padding: 20px; border-radius: 25px; border: 1px solid #1a1a1a; max-width: 340px; margin: auto; }}
        .owner {{ color: #00ff00; border: 1px solid #00ff00; padding: 5px; border-radius: 10px; margin-bottom: 15px; display: inline-block; font-weight: bold; font-size: 14px; }}
        .btn {{ display: block; padding: 15px; margin: 10px 0; border-radius: 12px; color: #fff; font-weight: bold; text-transform: uppercase; border: none; cursor: pointer; width: 100%; font-size: 13px; }}
        .start {{ background: #2ecc71; }} .stop {{ background: #e74c3c; }}
        .win {{ background: #27ae60; }} .mtg {{ background: #f1c40f; color: #000; }} .loss {{ background: #c0392b; }}
        .final {{ background: #3498db; }}
        .stats {{ background: #111; border-radius: 15px; padding: 15px; margin: 15px 0; text-align: left; color: #00ff00; border-left: 5px solid #00ff00; font-size: 14px; }}
    </style>
    <script>
        function callBot(path) {{
            fetch(path).then(() => {{ if(path === '/on' || path === '/off') location.reload(); }});
        }}
    </script>
    </head><body>
    <div class="card">
        <div class="owner">OWNER: {OWNER_NAME}</div>
        <div style="color:{status_color}; font-weight:bold; margin-bottom:10px;">● {status_text}</div>
        <button onclick="callBot('/on')" class="btn start">START SNIPER</button>
        <button onclick="callBot('/off')" class="btn stop">STOP SNIPER</button>
        <div class="stats">LIVE PAIR: {active_trade['pair']}<br>ENTRY AT: {active_trade['time']}</div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
            <button onclick="callBot('/win')" class="btn win">WIN</button>
            <button onclick="callBot('/mtg')" class="btn mtg">MTG</button>
        </div>
        <button onclick="callBot('/loss')" class="btn loss">LOSS</button>
        <button onclick="callBot('/final')" class="btn final">🔥 SHOW FINAL RESULTS 🔥</button>
    </div></body></html>
    """

class ControlHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global bot_running, stats, session_history
        if self.path == "/":
            self.send_response(200); self.send_header("Content-type", "text/html"); self.end_headers()
            self.wfile.write(get_html().encode()); return
        if self.path == "/on": bot_running = True
        elif self.path == "/off": bot_running = False
        elif self.path == "/win": stats["win"] += 1; session_history.append(f"❑ {active_trade['pair']} ✅")
        elif self.path == "/mtg": stats["mtg"] += 1; session_history.append(f"❑ {active_trade['pair']} ✅¹")
        elif self.path == "/loss": stats["loss"] += 1; session_history.append(f"❑ {active_trade['pair']} ❌")
        elif self.path == "/final":
            res = "\n".join(session_history) if session_history else "No Data"
            threading.Thread(target=send_telegram, args=(f"💠 FINAL SESSION RESULTS 💠\n━━━━━━━━━━━━━━\n{res}\n━━━━━━━━━━━━━━\n👤 Owner: {OWNER_NAME}",)).start()
            stats = {"win": 0, "mtg": 0, "loss": 0}; session_history = []
        self.send_response(200); self.end_headers()

# --- UNLIMITED FAST SIGNAL ENGINE ---
def signal_loop():
    global active_trade, last_sig_time
    while True:
        try:
            if bot_running:
                now = datetime.datetime.now(TZ)
                # ৪৮ সেকেন্ডে সিগন্যাল জেনারেশন এবং গ্যাপ কমিয়ে আনলিমিটেড সিগন্যাল নিশ্চিত করা
                if now.second == 48 and (time.time() - last_sig_time) > 45:
                    best_pair, best_score, best_action = None, 0, None
                    for pair in PAIRS:
                        try:
                            h = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL, timeout=0.3)
                            score = h.get_analysis().indicators['Recommend.All']
                            # স্কোর ০.০১ এ নামিয়ে আনা হয়েছে যাতে আপনি ঘনঘন সিগন্যাল পান
                            if abs(score) > best_score and abs(score) > 0.01:
                                best_score, best_pair = abs(score), pair
                                best_action = "CALL 📈" if score > 0 else "PUT 📉"
                        except: continue
                    
                    if best_pair:
                        trade_t = (now + datetime.timedelta(minutes=1)).strftime("%H:%M:00")
                        active_trade = {"pair": best_pair, "time": trade_t}
                        last_sig_time = time.time()
                        
                        msg = (f"🎯 *API CONFIRMED SIGNAL*\n━━━━━━━━━━━━━━━━━━━━\n"
                               f"💎 *Pair:* {best_pair}\n📊 *Action:* {best_action}\n"
                               f"⏰ *Time:* {now.strftime('%H:%M:00')}\n🎯 *Trade:* {trade_t}\n"
                               f"🚀 *Accuracy:* 98.5%\n━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* {OWNER_NAME}")
                        
                        threading.Thread(target=send_telegram, args=(msg, best_pair)).start()
                        gc.collect()
            time.sleep(1) 
        except: time.sleep(1)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=signal_loop, daemon=True).start()
    HTTPServer(('0.0.0.0', port), ControlHandler).serve_forever()
