# main.py
import logging
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

logging.basicConfig(level=logging.INFO)

START, CHAPTER_SELECT, LESSON_FLOW = range(3)

MAIN_MENU = [
    ["📘 آموزش", "📝 حل تمرینات", "📊 آزمون‌های آنلاین"]
]

CHAPTER_FILES = {
    "فصل ۲: اعداد صحیح": "lesson_ch2_7th_v1.json",
    "فصل ۳: عبارت‌های جبری": "lesson_ch3_7th_v2.json",
    "فصل ۴: خط و زاویه": "lesson_ch4_7th.json",
    "فصل ۵: اعداد اول": "lesson_ch5_7th_v1.json",
    "فصل ۶: سطح و حجم": "lesson_ch6_7th.json",
    "فصل ۷: توان": "lesson_ch7_7th_full.json",
    "فصل ۸: بردار و مختصات": "lesson_ch8_7th.json",
    "فصل ۹: آمار و احتمال": "lesson_ch9_7th.json"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 خوش آمدید! یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    )
    return START

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice == "📘 آموزش":
        await update.message.reply_text("لطفاً یک فصل را انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup([[k] for k in CHAPTER_FILES.keys()], resize_keyboard=True))
        return CHAPTER_SELECT
    else:
        await update.message.reply_text("این بخش هنوز فعال نشده است.")
        return START

async def chapter_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chapter = update.message.text
    if chapter not in CHAPTER_FILES:
        await update.message.reply_text("لطفاً یکی از فصل‌های لیست را انتخاب کنید.")
        return CHAPTER_SELECT

    context.user_data["current_chapter_file"] = CHAPTER_FILES[chapter]
    context.user_data["current_lesson_index"] = 0
    return await show_lesson_content(update, context)

async def show_lesson_content(update, context):
    chapter_file = context.user_data["current_chapter_file"]
    lesson_index = context.user_data["current_lesson_index"]
    with open(chapter_file, encoding="utf-8") as f:
        data = json.load(f)

    lesson = data["lessons"][lesson_index]
    context.user_data["current_lesson"] = lesson
    context.user_data["state"] = "showing_practice"
    context.user_data["practice_index"] = 0
    context.user_data["quiz_index"] = 0
    context.user_data["correct_quiz_answers"] = 0

    await update.message.reply_text(f"📖 {lesson['title']}\n\n{lesson['content']}")
    return await send_next_practice(update, context)

async def send_next_practice(update, context):
    lesson = context.user_data["current_lesson"]
    idx = context.user_data["practice_index"]

    if idx >= len(lesson["practices"]):
        context.user_data["state"] = "doing_quiz"
        return await start_quiz(update, context)

    question = lesson["practices"][idx]["question"]
    await update.message.reply_text(f"✏️ تمرین {idx+1}:\n{question}")
    return LESSON_FLOW

async def handle_practice_response(update, context):
    lesson = context.user_data["current_lesson"]
    idx = context.user_data["practice_index"]
    exercise = lesson["practices"][idx]

    await update.message.reply_text(f"✅ پاسخ درست: {exercise['answer']}\n🧠 توضیح: {exercise['explanation']}")
    context.user_data["practice_index"] += 1
    return await send_next_practice(update, context)

async def start_quiz(update, context):
    lesson = context.user_data["current_lesson"]
    idx = context.user_data["quiz_index"]

    if idx >= len(lesson["quiz"]):
        correct = context.user_data["correct_quiz_answers"]
        if correct >= 3:
            await update.message.reply_text(f"🎉 تبریک! شما با موفقیت این درس را گذراندید. (نمره: {correct}/5)")
            return await chapter_select(update, context)
        else:
            await update.message.reply_text(f"🔁 شما تنها به {correct} سوال پاسخ درست دادید. لطفاً دوباره درس را مرور کنید.")
            return await show_lesson_content(update, context)

    question = lesson["quiz"][idx]["question"]
    context.user_data["current_question"] = lesson["quiz"][idx]
    await update.message.reply_text(f"📝 سوال {idx+1}:\n{question}")
    return LESSON_FLOW

async def handle_quiz_response(update, context):
    user_answer = update.message.text.strip()
    question = context.user_data["current_question"]
    if user_answer == question["answer"]:
        context.user_data["correct_quiz_answers"] += 1
        await update.message.reply_text("✅ درست!")
    else:
        await update.message.reply_text(f"❌ نادرست. جواب صحیح: {question['answer']}")

    context.user_data["quiz_index"] += 1
    return await start_quiz(update, context)

if __name__ == '__main__':
    app = ApplicationBuilder().token("YOUR_BOT_TOKEN").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START: [MessageHandler(filters.TEXT, main_menu_handler)],
            CHAPTER_SELECT: [MessageHandler(filters.TEXT, chapter_select)],
            LESSON_FLOW: [MessageHandler(filters.TEXT, handle_practice_response),
                          MessageHandler(filters.TEXT, handle_quiz_response)],
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.run_polling()
