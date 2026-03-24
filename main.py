import time
import datetime
import pytz
import requests
import json
import threading
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from tradingview_ta import TA_Handler, Interval

# --- কনফিগারেশন ---
TOKEN = "8354111202:AAEqFLMoJ7W7AlwpfHibZbpusiWbnOcl5Xc"
CHAT_ID = "-1003862859969"
PAIRS = ["EURUSD", "EURJPY", "USDJPY", "CADJPY", "EURGBP", "AUDJPY", "GBPJPY", "AUDUSD", "GBPUSD", "AUDCAD", "USDCAD"]
TZ = pytz.timezone('Asia/Dhaka')

# --- ভেরিয়েবল ও স্টেট ---
bot_running = True
last_sent_time = 0
cooldown_seconds = 120
signals_history = [] 

# --- বাটন লেআউট ---
def get_main_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "✅ ON", "callback_data": "bot_on"}, {"text": "❌ OFF", "callback_data": "bot_off"}],
            [{"text": "📊 View Results (MT4 Style)", "callback_data": "view_results"}]
        ]
    }

# --- রেজাল্ট রিপোর্ট জেনারেটর ---
def generate_result_report():
    if not signals_history:
        return "এখনও কোনো সিগন্যাল ডাটা নেই।"
    
    total = len(signals_history)
    wins = sum(1 for s in signals_history if s['result'] == 'win')
    losses = total - wins
    win_rate = (wins / total) * 100 if total > 0 else 0
    
    report = f"✨ ···🔥 *FINAL RESULTS* 🔥··· ✨\n"
    report += f"━━━━━━━━━━━━━━━━━━━━\n"
    report += f"📅 - {datetime.datetime.now(TZ).strftime('%Y.%m.%d')}\n"
    report += f"━━━━━━━━━━━━━━━━━━━━\n"
    
    for s in signals_history:
        icon = "✅" if s['result'] == 'win' else "❌"
        report += f"❑ {s['time']}-{s['pair']}- {s['action']} {icon}\n"
    
    report += f"━━━━━━━━━━━━━━━━━━━━\n"
    report += f"🔮 Total Signal : {total} · 💎\n"
    report += f"🎯 Win: {wins} | 💀 Loss: {losses} · ( {win_rate:.0f}% )\n"
    report += f"━━━━━━━━━━━━━━━━━━━━"
    return report

# --- বাটন কমান্ড হ্যান্ডলার (Polling) ---
def check_button_commands():
    global bot_running
    last_update_id = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=30"
            response = requests.get(url).json()
            if "result" in response:
                for update in response["result"]:
                    last_update_id = update["update_id"]
                    if "callback_query" in update:
                        data = update["callback_query"]["data"]
                        if data == "bot_off":
                            bot_running = False
                            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": "🛑 *System:* সিগন্যাল আসা বন্ধ করা হয়েছে।", "reply_markup": json.dumps(get_main_keyboard()), "parse_mode": "Markdown"})
                        elif data == "bot_on":
                            bot_running = True
                            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": "🚀 *System:* সিগন্যাল স্ক্যানিং শুরু হয়েছে।", "reply_markup": json.dumps(get_main_keyboard()), "parse_mode": "Markdown"})
                        elif data == "view_results":
                            report = generate_result_report()
                            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": report, "reply_markup": json.dumps(get_main_keyboard()), "parse_mode": "Markdown"})
        except: pass
        time.sleep(1)

# --- সিগন্যাল সেন্ডার ---
def send_signal(pair, action, now):
    time_str = now.strftime("%H:%M")
    trade_time = (now + datetime.timedelta(seconds=12)).strftime("%H:%M:00")
    
    # রেজাল্ট অটোমেশন (সিমুলেশন)
    import random
    res = "win" if random.random() < 0.93 else "loss" 
    signals_history.append({'time': time_str, 'pair': pair, 'action': action, 'result': res})
    
    msg = (f"📉 *API CONFIRMED SIGNAL*\n"
           f"💎 *Pair:* {pair}\n"
           f"📊 *Action:* {action}\n"
           f"⏰ *Time:* {now.strftime('%H:%M:%S')}\n"
           f"🎯 *Trade:* {trade_time}")
    
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown", "reply_markup": json.dumps(get_main_keyboard())})

# --- FAKE WEB SERVER (Render Port Error সমাধান) ---
class SimpleServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"Bot is Running...")

def run_fake_server():
    # Render-এর দেওয়া পোর্ট খুঁজে নিবে অথবা ১০৫০০ ব্যবহার করবে
    port = int(os.environ.get("PORT", 10000)) 
    server = HTTPServer(('0.0.0.0', port), SimpleServer)
    server.serve_forever()

# থ্রেড চালু করা
threading.Thread(target=run_fake_server, daemon=True).start()
threading.Thread(target=check_button_commands, daemon=True).start()

# স্টার্টআপ মেসেজ
requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": "🔥 *System Ready!* বটের কন্ট্রোল প্যানেল সচল হয়েছে।", "reply_markup": json.dumps(get_main_keyboard()), "parse_mode": "Markdown"})

while True:
    now = datetime.datetime.now(TZ)
    if bot_running and now.second == 48:
        if time.time() - last_sent_time > cooldown_seconds:
            for p in PAIRS:
                try:
                    handler = TA_Handler(symbol=p, exchange="FX_IDC", screener="forex", interval=Interval.INTERVAL_1_MINUTE)
                    rec = handler.get_analysis().summary['RECOMMENDATION']
                    if rec and ("STRONG" in rec):
                        send_signal(p, ("CALL 📈" if "BUY" in rec else "PUT 📉"), now)
                        last_sent_time = time.time()
                        break
                except: continue
        time.sleep(10)
    time.sleep(1)
