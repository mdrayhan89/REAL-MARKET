import asyncio
import os
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
from playwright.async_api import async_playwright

# --- কনফিগারেশন ---
TOKEN = '8354111202:AAEqFLMoJ7W7AlwpfHibZbpusiWbnOcl5Xc'
CHAT_ID = '-1003862859969'
BASE_URL = "https://dark-live-ss.onrender.com/"
current_pair = "EURJPY"
bot_running = False

# --- কন্ট্রোল প্যানেল কিবোর্ড ---
def get_control_keyboard():
    status = "🟢 RUNNING" if bot_running else "🔴 STOPPED"
    keyboard = [
        [InlineKeyboardButton(f"Status: {status}", callback_data="none")],
        [
            InlineKeyboardButton("▶️ START", callback_data="start_bot"),
            InlineKeyboardButton("⏹️ STOP", callback_data="stop_bot")
        ],
        [InlineKeyboardButton("🔄 Pair: " + current_pair, callback_data="change_pair")],
        [InlineKeyboardButton("📊 Session Report", callback_data="get_report")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- সিগন্যাল ফরম্যাটিং (আপনার প্রিমিয়াম ইমোজি ম্যাপ অনুযায়ী) ---
def format_signal(pair, action, acc):
    now = datetime.datetime.now()
    trade_time = (now + datetime.timedelta(minutes=1)).strftime("%H:%M:00")
    current_time = now.strftime("%H:%M:%S")
    
    msg = (
        f'━━━━━━━━━━━━━━━━━━━━\n'
        f'<tg-emoji emoji-id="6325797905663791037">💎</tg-emoji> <b>API CONFIRMED SIGNAL</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━\n'
        f'<tg-emoji emoji-id="5472416843438246859">📊</tg-emoji> <b>Pair:</b> {pair}\n'
        f'<tg-emoji emoji-id="6264696987946324240">🔋</tg-emoji> <b>Action:</b> {action}\n'
        f'<tg-emoji emoji-id="6325717349257187998">🕒</tg-emoji> <b>Time:</b> {current_time}\n'
        f'<tg-emoji emoji-id="5212985021870123409">🚀</tg-emoji> <b>Trade:</b> {trade_time}\n'
        f'<tg-emoji emoji-id="6325667390197600621">🎯</tg-emoji> <b>Accuracy:</b> {acc}%\n'
        f'━━━━━━━━━━━━━━━━━━━━\n'
        f'<tg-emoji emoji-id="5384513813670279219">👑</tg-emoji> <b>Owner:</b> DARK-X-RAYHAN'
    )
    return msg

# --- স্ক্রিনশট এবং অ্যানালাইসিস ফাংশন ---
async def capture_and_analyze(context):
    global bot_running, current_pair
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        while bot_running:
            try:
                url = f"{BASE_URL}?Pair={current_pair}"
                await page.goto(url)
                await asyncio.sleep(5) # চার্ট লোড হওয়ার সময়
                
                path = "signal_ss.png"
                await page.screenshot(path=path)
                
                # এখানে আপনার স্ট্র্যাটেজি (EMA, RSI, FVG) অনুযায়ী কন্ডিশন চেক হবে
                # ডেমো হিসেবে একটি সিগন্যাল পাঠানো হচ্ছে
                signal_text = format_signal(current_pair, "CALL ⬆️", "98.5")
                
                await context.bot.send_photo(
                    chat_id=CHAT_ID,
                    photo=open(path, 'rb'),
                    caption=signal_text,
                    parse_mode=ParseMode.HTML
                )
                
                await asyncio.sleep(60) # প্রতি ১ মিনিট পর পর
            except Exception as e:
                print(f"Error: {e}")
                await asyncio.sleep(10)
        await browser.close()

# --- বট হ্যান্ডলারস ---
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "<b>DARK-X-SNIPER CONTROL PANEL</b>",
        reply_markup=get_control_keyboard(),
        parse_mode=ParseMode.HTML
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    global bot_running
    await query.answer()

    if query.data == "start_bot":
        if not bot_running:
            bot_running = True
            asyncio.create_task(capture_and_analyze(context))
            await query.edit_message_text("✅ Bot Started! Analyzing...", reply_markup=get_control_keyboard())
    
    elif query.data == "stop_bot":
        bot_running = False
        await query.edit_message_text("🛑 Bot Stopped!", reply_markup=get_control_keyboard())

# --- মেইন ফাংশন ---
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot is live...")
    app.run_polling()

if __name__ == '__main__':
    main()
