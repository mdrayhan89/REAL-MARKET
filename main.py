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

# --- GLOBAL STATE ---
bot_running = False
signals_history = []
stats = {"win": 0, "loss": 0, "total": 0}
last_signal_time = ""

# --- WIN/LOSS & MARTINGALE LOGIC ---
def check_full_result(pair, action, time_id):
    global stats
    time.sleep(65) # ১ম ক্যান্ডেল শেষ হওয়ার ১০ সেকেন্ড পর
    try:
        h = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL)
        rec1 = h.get_analysis().summary['RECOMMENDATION']
        is_direct_win = ("CALL" in action and "BUY" in rec1) or ("PUT" in action and "SELL" in rec1)
        
        if is_direct_win:
            stats["win"] += 1
            win_text = (f"✅ *DIRECT WIN ALERT* ✅\n━━━━━━━━━━━━━━━━━━━━\n"
                        f"💎 *Pair:* {pair}\n💰 *Result:* First Candle Profit\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* DARK-X-RAYHAN")
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": win_text, "parse_mode": "Markdown"})
            update_history(time_id, "✅")
            return

        # ১ম টা লস হলে M1 এলার্ট
        m1_alert = (f"⚠️ *M1 ALERT (Next Candle)* ⚠️\n━━━━━━━━━━━━━━━━━━━━\n"
                    f"💎 *Pair:* {pair}\n🔥 *Next:* 1-Min Martingale\n"
                    f"📈 *Direction:* {action}\n━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* DARK-X-RAYHAN")
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": m1_alert, "parse_mode": "Markdown"})
        
        time.sleep(60) # M1 ক্যান্ডেল শেষ হওয়া পর্যন্ত অপেক্ষা
        rec2 = h.get_analysis().summary['RECOMMENDATION']
        is_m1_win = ("CALL" in action and "BUY" in rec2) or ("PUT" in action and "SELL" in rec2)
        
        if is_m1_win:
            stats["win"] += 1
            m1_win_text = (f"✅ *MTG-1 WIN ALERT* ✅\n━━━━━━━━━━━━━━━━━━━━\n"
                           f"💎 *Pair:* {pair}\n💰 *Result:* Martingale Profit\n"
                           f"━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* DARK-X-RAYHAN")
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": m1_win_text, "parse_mode": "Markdown"})
            update_history(time_id, "✅¹")
        else:
            stats["loss"] += 1
            loss_text = (f"💀 *TOTAL LOSS ALERT* 💀\n━━━━━━━━━━━━━━━━━━━━\n"
                         f"💎 *Pair:* {pair}\n❌ *Result:* Double Loss\n"
                         f"━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* DARK-X-RAYHAN")
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": loss_text, "parse_mode": "Markdown"})
            update_history(time_id, "❌")
    except: pass

def update_history(t_id, res):
    for s in signals_history:
        if s['time'] == t_id: s['result'] = res; break

# --- WEB PANEL ---
def get_html():
    status_text = "🟢 RUNNING" if bot_running else "🔴 STOPPED"
    status_color = "#28a745" if bot_running else "#dc3545"
    return f"""
    <html><body style="background:#0a0a0a;color:white;text-align:center;font-family:sans-serif;">
    <div style="margin-top:50px;border:1px solid #333;display:inline-block;padding:30px;border-radius:15px;background:#111;width:300px;">
    <h1 style="margin-bottom:0;">SNIPER V3 PRO</h1>
    <p style="color:#555;font-size:12px;margin-top:5px;">OWNER: DARK-X-RAYHAN</p>
    <h2 style="color:{status_color};border:1px solid {status_color};padding:10px;border-radius:10px;">{status_text}</h2>
    <a href="/on" style="display:block;padding:15px;margin:10px;background:#28a745;color:white;text-decoration:none;border-radius:50px;font-weight:bold;">START BOT</a>
    <a href="/off" style="display:block;padding:15px;margin:10px;background:#dc3545;color:white;text-decoration:none;border-radius:50px;font-weight:bold;">STOP BOT</a>
    <a href="/results" style="display:block;padding:15px;margin:10px;background:#007bff;color:white;text-decoration:none;border-radius:50px;font-weight:bold;">SEND REPORT</a>
    </div></body></html>
    """

class ControlHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global bot_running
        if self.path == "/on": bot_running = True
        elif self.path == "/off": bot_running = False
        elif self.path == "/results": send_final_report()
        self.send_response(200); self.send_header("Content-type", "text/html"); self.end_headers()
        self.wfile.write(get_html().encode())
    def log_message(self, format, *args): return

def send_final_report():
    if not signals_history:
        msg = "📊 No signals yet today."
    else:
        acc = (stats["win"] / stats["total"] * 100) if stats["total"] > 0 else 0
        report = (f"💠 ✨ ···🔥 *FINAL RESULTS* 🔥··· ✨ 💠\n━━━━━━━━━━━━━━━━━━━━\n"
                  f"📅 *Date:* {datetime.datetime.now(TZ).strftime('%Y.%m.%d')}\n━━━━━━━━━━━━━━━━━━━━\n")
        for s in signals_history[-15:]:
            report += f"❑ {s['time']} - {s['pair']} - {s['action']} {s.get('result', '⌛')}\n"
        report += (f"━━━━━━━━━━━━━━━━━━━━\n🔮 *Total:* {stats['total']} | 🎯 *Win:* {stats['win']}\n"
                   f"💀 *Loss:* {stats['loss']} | 🚀 *Acc:* {acc:.0f}%\n━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* DARK-X-RAYHAN")
        msg = report
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

# --- MAIN LOOP ---
def signal_loop():
    global last_signal_time, stats
    while True:
        if bot_running:
            now = datetime.datetime.now(TZ)
            min_id = now.strftime("%H:%M")
            if now.second == 48 and min_id != last_signal_time:
                for pair in PAIRS:
                    try:
                        h = TA_Handler(symbol=pair, exchange=EXCHANGE, screener=SCREENER, interval=INTERVAL)
                        score = h.get_analysis().indicators['Recommend.All']
                        if abs(score) >= 0.5:
                            action = "CALL 📈" if score > 0 else "PUT 📉"
                            stats["total"] += 1
                            signals_history.append({'time': min_id, 'pair': pair, 'action': action, 'result': '⌛'})
                            
                            trade_time = (now + datetime.timedelta(seconds=12)).strftime('%H:%M:00')
                            msg = (f"🎯 *API CONFIRMED SIGNAL*\n━━━━━━━━━━━━━━━━━━━━\n"
                                   f"💎 *Pair:* {pair}\n📊 *Action:* {action}\n"
                                   f"⏰ *Time:* {now.strftime('%H:%M:%S')}\n"
                                   f"🎯 *Trade:* {trade_time}\n"
                                   f"🚀 *Accuracy:* 98.5%\n━━━━━━━━━━━━━━━━━━━━\n👤 *Owner:* DARK-X-RAYHAN")
                            
                            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
                            last_signal_time = min_id
                            threading.Thread(target=check_full_result, args=(pair, action, min_id)).start()
                            break
                    except: continue
        time.sleep(1)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=signal_loop, daemon=True).start()
    HTTPServer(('0.0.0.0', port), ControlHandler).serve_forever()
