import os
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

API_TOKEN = os.environ.get("API_TOKEN")  # دریافت توکن از متغیر محیطی

# متغیرهای سراسری
user_state = {}
content_file = 'content_7th.json'
lesson_files = {
    "اعداد صحیح": "lesson_ch2_7th_v1.json",
    "عبارت‌های جبری": "lesson_ch3_7th_v2.json",
    "خط و زاویه": "lesson_ch4_7th.json",
    "اعداد اول": "lesson_ch5_7th_v1.json",
    "سطح و حجم": "lesson_ch6_7th.json",
    "توان و جذر": "lesson_ch7_7th_full.json",
    "بردار و مختصات": "lesson_ch8_7th.json",
    "آمار و احتمال": "lesson_ch9_7th.json"
}


def load_json(filename):
    with open(filename, encoding="utf-8") as f:
        return json.load(f)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state[update.effective_chat.id] = {}
    keyboard = [["آموزش"], ["حل تمرینات"], ["آزمون‌های آنلاین"]]
    await update.message.reply_text("🎓 به ربات آموزشی ریاضی خوش آمدید!\nیکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text

    state = user_state.get(chat_id, {})

    # مرحله اول: انتخاب گزینه‌ی اصلی
    if text == "آموزش":
        data = load_json(content_file)
        state["mode"] = "learning"
        user_state[chat_id] = state
        keyboard = [[f["title"]] for f in data["chapters"]]
        await update.message.reply_text("📚 فصل مورد نظر را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))

    # مرحله دوم: انتخاب فصل
    elif state.get("mode") == "learning" and "chapter" not in state:
        if text in lesson_files:
            state["chapter"] = text
            state["lesson_data"] = load_json(lesson_files[text])
            state["step"] = 0
            user_state[chat_id] = state
            await send_lesson(update, context)
        else:
            await update.message.reply_text("فصل معتبر نیست.")

    # مرحله سوم: پاسخ‌دهی به تمرین یا آزمون
    elif "quiz_mode" in state:
        correct_answer = state["quiz_data"][state["quiz_step"]]["answer"]
        if text.strip() == correct_answer.strip():
            state["score"] += 1
        state["quiz_step"] += 1
        if state["quiz_step"] < len(state["quiz_data"]):
            await send_quiz_question(update, context)
        else:
            await show_quiz_result(update, context)

    else:
        await update.message.reply_text("لطفاً یکی از گزینه‌ها را از منوی زیر انتخاب کنید.")


async def send_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    state = user_state[chat_id]
    lessons = state["lesson_data"]["lessons"]
    if state["step"] < len(lessons):
        lesson = lessons[state["step"]]
        await update.message.reply_text(f"📖 *درس {lesson['title']}*\n\n{lesson['text']}", parse_mode='Markdown')

        # سپس تمرین‌ها
        for i, ex in enumerate(lesson.get("exercises", []), 1):
            await update.message.reply_text(f"📝 تمرین {i}:\n{ex['question']}\n✅ پاسخ: {ex['answer']}\n📘 توضیح: {ex['explanation']}")

        # سپس آزمون
        state["quiz_data"] = lesson.get("quiz", [])
        state["quiz_step"] = 0
        state["score"] = 0
        state["quiz_mode"] = True
        user_state[chat_id] = state
        await update.message.reply_text("🧪 حالا آزمون درس را شروع می‌کنیم:")
        await send_quiz_question(update, context)
    else:
        await update.message.reply_text("🎉 آموزش این فصل به پایان رسید. برای ادامه، یکی از گزینه‌ها را انتخاب کنید.")
        user_state[chat_id] = {}


async def send_quiz_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    state = user_state[chat_id]
    question_data = state["quiz_data"][state["quiz_step"]]
    await update.message.reply_text(f"❓ سوال {state['quiz_step']+1}: {question_data['question']}")


async def show_quiz_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    state = user_state[chat_id]
    score = state["score"]
    total = len(state["quiz_data"])
    state.pop("quiz_mode", None)

    if score >= 3:
        await update.message.reply_text(f"✅ آزمون با موفقیت انجام شد.\nنمره شما: {score}/{total}")
        state["step"] += 1
        user_state[chat_id] = state
        await send_lesson(update, context)
    else:
        await update.message.reply_text(f"❌ نمره شما: {score}/{total}\nبرای موفقیت باید حداقل ۳ سوال درست پاسخ دهید.\nلطفاً دوباره این درس را بخوانید.")
        # درس را تکرار می‌کند
        await send_lesson(update, context)


if __name__ == '__main__':
    app = ApplicationBuilder().token(API_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.run_polling()
