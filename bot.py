import logging
import json
import requests
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Logging setup
logging.basicConfig(level=logging.INFO)

ASK_DOB = 0
user_data = {}
DB_FILE = "users.json"

def load_users():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

def get_sun_sign(day, month):
    signs = [
        ("Capricorn", (12, 22), (1, 19)),
        ("Aquarius", (1, 20), (2, 18)),
        ("Pisces", (2, 19), (3, 20)),
        ("Aries", (3, 21), (4, 19)),
        ("Taurus", (4, 20), (5, 20)),
        ("Gemini", (5, 21), (6, 20)),
        ("Cancer", (6, 21), (7, 22)),
        ("Leo", (7, 23), (8, 22)),
        ("Virgo", (8, 23), (9, 22)),
        ("Libra", (9, 23), (10, 22)),
        ("Scorpio", (10, 23), (11, 21)),
        ("Sagittarius", (11, 22), (12, 21)),
    ]
    for sign, start, end in signs:
        if (month == start[0] and day >= start[1]) or (month == end[0] and day <= end[1]):
            return sign
    return "Capricorn"

def fetch_daily_horoscope(sign):
    sign_id = {
        "Aries": 1, "Taurus": 2, "Gemini": 3, "Cancer": 4,
        "Leo": 5, "Virgo": 6, "Libra": 7, "Scorpio": 8,
        "Sagittarius": 9, "Capricorn": 10, "Aquarius": 11, "Pisces": 12
    }
    url = f"https://www.horoscope.com/us/horoscopes/general/horoscope-general-daily-today.aspx?sign={sign_id[sign]}"
    page = requests.get(url)
    text = page.text.split('<div class="main-horoscope">')[1].split("</div>")[0]
    horoscope = text.split("<p>")[1].split("</p>")[0]
    return horoscope.strip()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Please enter your Date of Birth (DD-MM-YYYY):")
    return ASK_DOB

async def get_dob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        day, month, year = map(int, update.message.text.split("-"))
        sign = get_sun_sign(day, month)
        users = load_users()
        users[str(update.effective_user.id)] = {"sign": sign}
        save_users(users)
        await update.message.reply_text(f"Got it! Your sun sign is {sign}. You'll receive daily horoscopes automatically.")
    except:
        await update.message.reply_text("Invalid format. Please enter in DD-MM-YYYY format.")
    return ConversationHandler.END

async def send_daily_horoscopes(app):
    users = load_users()
    for user_id, info in users.items():
        try:
            sign = info["sign"]
            horoscope = fetch_daily_horoscope(sign)
            await app.bot.send_message(chat_id=int(user_id), text=f"♈ {sign} — Today's Horoscope:\n\n{horoscope}")
        except Exception as e:
            logging.error(f"Error sending to {user_id}: {e}")

def main():
    TOKEN = "8123872131:AAFFzyXB5EllpdXm5Gs1Y_L306Idh30ByQo"
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={ASK_DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dob)]},
        fallbacks=[]
    )

    app.add_handler(conv_handler)

    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: app.create_task(send_daily_horoscopes(app)), 'cron', hour=8, minute=0)
    scheduler.start()

    app.run_polling()

if __name__ == "__main__":
    main()
