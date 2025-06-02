import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# تابع بارگذاری محتوا از فایل JSON
def load_lessons(filename='lesson_ch2_7th_v3.json'):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# فرمان /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! من ربات آموزشی ریاضی هستم.\n"
        "برای دیدن درسنامه این فصل، دستور /lesson را بزن."
    )

# فرمان /lesson
async def lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_lessons()
    lessons = data.get("درسنامه‌ها", [])

    response = f"فصل: {data.get('فصل', '')}\n\n"

    for lesson in lessons:
        title = lesson.get("عنوان", "")
        text = lesson.get("متن", "")
        response += f"📚 {title}\n{text}\n\n"

    # محدود کردن طول پیام اگر طولانی بود (تلگرام محدودیت داره)
    if len(response) > 4000:
        response = response[:3990] + "\n..."

    await update.message.reply_text(response)

if __name__ == "__main__":
    # جایگزین کن با توکن ربات تلگرامت
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("lesson", lesson))

    print("ربات اجرا شد...")
    app.run_polling()
