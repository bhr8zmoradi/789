import json
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# بارگذاری توکن از فایل config.json
with open("config.json", "r", encoding="utf-8") as f:
    token = json.load(f)["TOKEN"]

# بارگذاری محتوای کلی پایه هفتم
with open("content_7th.json", "r", encoding="utf-8") as f:
    content = json.load(f)

# بارگذاری درسنامه فصل دوم (عددهای صحیح)
with open("lesson_ch2_7th_v3.json", "r", encoding="utf-8") as f:
    lessons_f2 = json.load(f)

# فعال‌سازی لاگ
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("پایه هفتم", callback_data="grade_7")]
    ]
    await update.message.reply_text("سلام! پایه مورد نظر رو انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    # انتخاب پایه هفتم
    if data == "grade_7":
        chapters = content["فصل‌ها"]
        keyboard = [[InlineKeyboardButton(ch["عنوان"], callback_data=f"chapter_{i}")] for i, ch in enumerate(chapters)]
        await query.edit_message_text("فصل مورد نظر را انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))

    # انتخاب یکی از فصل‌های هفتم
    elif data.startswith("chapter_"):
        index = int(data.split("_")[1])
        chapter_title = content["فصل‌ها"][index]["عنوان"]

        # اگر فصل دوم (عددهای صحیح) باشد، درسنامه‌ها را از فایل جداگانه لود کن
        if chapter_title == "عددهای صحیح":
            keyboard = [
                [InlineKeyboardButton(lesson["عنوان"], callback_data=f"lesson_f2_{i}")]
                for i, lesson in enumerate(lessons_f2["درسنامه‌ها"])
            ]
            await query.edit_message_text(f"درس‌های فصل «{chapter_title}» را انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text(f"محتوای فصل «{chapter_title}» هنوز بارگذاری نشده.")

    # نمایش محتوای درس‌ از فصل دوم
    elif data.startswith("lesson_f2_"):
        index = int(data.split("_")[-1])
        lesson = lessons_f2["درسنامه‌ها"][index]
        await query.edit_message_text(f"📘 {lesson['عنوان']}\n\n{lesson['متن']}")


if __name__ == "__main__":
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))

    print("ربات آماده است...")
    app.run_polling()
