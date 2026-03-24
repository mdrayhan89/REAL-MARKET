import time
import datetime
import requests
from tradingview_ta import TA_Handler, Interval

# --- কনফিগারেশন ---
TOKEN = "8354111202:AAEqFLMoJ7W7AlwpfHibZbpusiWbnOcl5Xc"
CHAT_ID = "-1003862859969"
PAIRS = ["EURUSD", "EURJPY", "USDJPY", "CADJPY", "EURGBP", "AUDJPY", "GBPJPY", "AUDUSD", "GBPUSD", "AUDCAD", "USDCAD"]
EXCHANGE = "FX_IDC" # ফরেক্সের জন্য
SCREENER = "forex"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except:
        pass

def get_signal(symbol):
    try:
        handler = TA_Handler(
            symbol=symbol,
            exchange=EXCHANGE,
            screener=SCREENER,
            interval=Interval.INTERVAL_1_MINUTE
        )
        analysis = handler.get_analysis()
        rec = analysis.summary['RECOMMENDATION']
        price = analysis.indicators['close']
        return rec, price
    except:
        return None, None

print("Dark Rayhan Sniper Bot is Running...")

last_signals = {pair: "" for pair in PAIRS}

while True:
    now = datetime.datetime.now()
    # সেকেন্ড যখন ৪৮ (১২ সেকেন্ড বাকি) তখন চেক করবে
    if now.second == 48:
        for pair in PAIRS:
            rec, price = get_signal(pair)
            
            if rec and ("STRONG" in rec) and rec != last_signals[pair]:
                action = "BUY" if "BUY" in rec else "SELL"
                curr_time = now.strftime("%H:%M:%S")
                # পরবর্তী মিনিটের সময় হিসাব
                trade_time = (now + datetime.timedelta(seconds=12)).strftime("%H:%M:00")
                
                msg = (f"📉 *API CONFIRMED SIGNAL*\n"
                       f"💎 *Pair:* {pair}\n"
                       f"📊 *Action:* {action}\n"
                       f"⏰ *Time:* {curr_time}\n"
                       f"🎯 *Trade:* {trade_time}")
                
                send_telegram(msg)
                last_signals[pair] = rec
        
        time.sleep(10) # একই মিনিটে যেন বারবার না পাঠায়
    
    time.sleep(1) # প্রতি সেকেন্ডে ঘড়ি চেক করবে
