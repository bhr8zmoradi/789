import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# بارگذاری توکن ربات
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)
TOKEN = config["TOKEN"]

# بارگذاری فهرست فصل‌ها
with open("content_7th.json", "r", encoding="utf-8") as f:
    content_7th = json.load(f)

# تعریف مسیر فایل‌های درسنامه به تفکیک فصل
LESSON_FILES = {
    "عددهای صحیح": "lesson_ch2_7th_v3.json"
    # سایر فصل‌ها را در آینده اضافه کن
}

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for فصل in content_7th["فصل‌ها"]:
        keyboard.append([InlineKeyboardButton(فصل["عنوان"], callback_data=f"فصل:{فصل['عنوان']}")])
    await update.message.reply_text("یکی از فصل‌های زیر را انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("فصل:"):
        selected_chapter = data.split(":")[1]
        filename = LESSON_FILES.get(selected_chapter)

        if not filename:
            await query.edit_message_text("برای این فصل هنوز درسنامه‌ای ثبت نشده است.")
            return

        with open(filename, "r", encoding="utf-8") as f:
            lesson_data = json.load(f)

        keyboard = [
            [InlineKeyboardButton(lesson["عنوان"], callback_data=f"درس:{selected_chapter}:{lesson['عنوان']}")]
            for lesson in lesson_data["درسنامه‌ها"]
        ]
        await query.edit_message_text(f"مباحث فصل «{selected_chapter}» را انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("درس:"):
        _, chapter, lesson_title = data.split(":", 2)
        filename = LESSON_FILES.get(chapter)
        if filename:
            with open(filename, "r", encoding="utf-8") as f:
                lesson_data = json.load(f)
                for lesson in lesson_data["درسنامه‌ها"]:
                    if lesson["عنوان"] == lesson_title:
                        await query.edit_message_text(f"📘 {lesson['عنوان']}\n\n{lesson['متن']}")
                        return
        await query.edit_message_text("خطایی در بارگذاری درس پیش آمده.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()
