import time
import datetime
import pytz
import requests
from tradingview_ta import TA_Handler, Interval

# --- কনফিগারেশন ---
TOKEN = "8354111202:AAEqFLMoJ7W7AlwpfHibZbpusiWbnOcl5Xc"
CHAT_ID = "-1003862859969"
PAIRS = ["EURUSD", "EURJPY", "USDJPY", "CADJPY", "EURGBP", "AUDJPY", "GBPJPY", "AUDUSD", "GBPUSD", "AUDCAD", "USDCAD"]
TZ = pytz.timezone('Asia/Dhaka') # বাংলাদেশ সময় (UTC+6)

# --- গ্যাপ এবং লজিক ভেরিয়েবল ---
last_sent_time = 0 
cooldown_seconds = 120 # ২ মিনিট গ্যাপ (একটি সিগন্যাল আসার পর ২ মিনিট বিরতি)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending telegram: {e}")

def get_signal(symbol):
    try:
        handler = TA_Handler(
            symbol=symbol,
            exchange="FX_IDC",
            screener="forex",
            interval=Interval.INTERVAL_1_MINUTE
        )
        analysis = handler.get_analysis()
        # আপনার অরিজিনাল স্ট্রং বাই/সেল লজিক
        return analysis.summary['RECOMMENDATION']
    except Exception as e:
        return None

print("Dark Rayhan Sniper Bot - Running with 2 Min Gap & UTC+6")

while True:
    now = datetime.datetime.now(TZ)
    current_timestamp = time.time()
    
    # ক্যান্ডেল শেষ হওয়ার ১২ সেকেন্ড আগে (৪৮তম সেকেন্ডে) চেক করবে
    if now.second == 48:
        # ২ মিনিট পার হয়েছে কিনা চেক (কোoldown)
        if current_timestamp - last_sent_time > cooldown_seconds:
            for pair in PAIRS:
                recommendation = get_signal(pair)
                
                # শুধুমাত্র STRONG_BUY বা STRONG_SELL হলে সিগন্যাল দিবে
                if recommendation and ("STRONG" in recommendation):
                    action = "BUY 📈" if "BUY" in recommendation else "SELL 📉"
                    curr_time_str = now.strftime("%H:%M:%S")
                    
                    # পরবর্তী ক্যান্ডেল শুরুর সময় (Trade Time)
                    trade_time = (now + datetime.timedelta(seconds=12)).strftime("%H:%M:00")
                    
                    # আপনার দেওয়া প্রফেশনাল ফরম্যাট
                    msg = (f"📉 *API CONFIRMED SIGNAL*\n"
                           f"💎 *Pair:* {pair}\n"
                           f"📊 *Action:* {action}\n"
                           f"⏰ *Time:* {curr_time_str}\n"
                           f"🎯 *Trade:* {trade_time}")
                    
                    send_telegram(msg)
                    last_sent_time = current_timestamp # সময় আপডেট
                    break # একটি সিগন্যাল পাঠানোর পর ওই মিনিটের জন্য লুপ বন্ধ
        
        time.sleep(10) # একই মিনিটে ডাবল সিগন্যাল যেন না আসে
    
    time.sleep(1) # প্রতি সেকেন্ডে ঘড়ি চেক
