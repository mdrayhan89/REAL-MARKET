import time
import datetime
import pytz
import requests
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from tradingview_ta import TA_Handler, Interval

# --- কনফিগারেশন ---
TOKEN = "8354111202:AAEqFLMoJ7W7AlwpfHibZbpusiWbnOcl5Xc"
CHAT_ID = "-1003862859969"
PAIRS = ["EURUSD", "EURJPY", "USDJPY", "CADJPY", "EURGBP", "AUDJPY", "GBPJPY", "AUDUSD", "GBPUSD", "AUDCAD", "USDCAD"]
TZ = pytz.timezone('Asia/Dhaka')

# --- স্টেট কন্ট্রোল ---
bot_running = True  # শুরুতে বট চালু থাকবে
last_sent_time = 0 
cooldown_seconds = 120 

# --- FAKE WEB SERVER (Render Free Plan-এর জন্য) ---
class SimpleServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running...")

def run_fake_server():
    server = HTTPServer(('0.0.0.0', 10000), SimpleServer)
    server.serve_forever()

# --- বাটনের কমান্ড চেক করার ফাংশন ---
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
                        callback_id = update["callback_query"]["id"]
                        
                        if data == "bot_off":
                            bot_running = False
                            requests.post(f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery", data={"callback_query_id": callback_id, "text": "বট এখন বন্ধ করা হয়েছে ❌"})
                            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": "🛑 *System:* সিগন্যাল আসা বন্ধ করা হয়েছে।", "parse_mode": "Markdown"})
                        
                        elif data == "bot_on":
                            bot_running = True
                            requests.post(f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery", data={"callback_query_id": callback_id, "text": "বট এখন চালু করা হয়েছে ✅"})
                            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": "🚀 *System:* সিগন্যাল স্ক্যানিং শুরু হয়েছে।", "parse_mode": "Markdown"})
        except:
            pass
        time.sleep(1)

# --- সিগন্যাল পাঠানোর ফাংশন ---
def send_signal(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    keyboard = {
        "inline_keyboard": [
            [{"text": "✅ TURN ON", "callback_data": "bot_on"}, {"text": "❌ TURN OFF", "callback_data": "bot_off"}]
        ]
    }
    payload = {
        "chat_id": CHAT_ID, 
        "text": message, 
        "parse_mode": "Markdown",
        "reply_markup": json.dumps(keyboard)
    }
    requests.post(url, data=payload)

def get_tv_analysis(symbol):
    try:
        handler = TA_Handler(symbol=symbol, exchange="FX_IDC", screener="forex", interval=Interval.INTERVAL_1_MINUTE)
        return handler.get_analysis().summary['RECOMMENDATION']
    except: return None

# সার্ভার এবং বাটন লিসেনার আলাদা থ্রেডে চালানো
threading.Thread(target=run_fake_server, daemon=True).start()
threading.Thread(target=check_button_commands, daemon=True).start()

print("Dark Rayhan Sniper Bot - Interactive Mode Started...")

while True:
    now = datetime.datetime.now(TZ)
    current_timestamp = time.time()
    
    # শুধুমাত্র যদি bot_running = True থাকে তবেই সিগন্যাল খুঁজবে
    if bot_running and now.second == 48:
        if current_timestamp - last_sent_time > cooldown_seconds:
            for pair in PAIRS:
                rec = get_tv_analysis(pair)
                if rec and ("STRONG" in rec):
                    action = "BUY 📈" if "BUY" in rec else "SELL 📉"
                    trade_time = (now + datetime.timedelta(seconds=12)).strftime("%H:%M:00")
                    
                    msg = (f"📉 *API CONFIRMED SIGNAL*\n💎 *Pair:* {pair}\n📊 *Action:* {action}\n⏰ *Time:* {now.strftime('%H:%M:%S')}\n🎯 *Trade:* {trade_time}")
                    send_signal(msg)
                    last_sent_time = current_timestamp
                    break
        time.sleep(10)
    time.sleep(1)
