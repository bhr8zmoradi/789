import os
import json
import glob
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

API_TOKEN = os.environ.get("API_TOKEN")
if not API_TOKEN:
    raise ValueError("API_TOKEN not found in environment variables")

# متغیرهای سراسری
user_state = {}
content_file = 'content_7th.json'

def load_lesson_files():
    lesson_files = {}
    lesson_dir = "lessons/"
    for file_path in glob.glob(f"{lesson_dir}*.json"):
        file_name = os.path.basename(file_path)
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
                chapter_name = data.get("chapter_title", file_name.replace(".json", "").replace("_", " "))
                lesson_files[chapter_name] = file_path
        except (FileNotFoundError, json.JSONDecodeError):
            continue  # نادیده گرفتن فایل‌های نامعتبر
    return lesson_files

lesson_files = load_lesson_files()

def load_json(filename):
    try:
        with open(filename, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state[update.effective_chat.id] = {}
    keyboard = [["آموزش"], ["حل تمرینات"], ["آزمون‌های آنلاین"]]
    await update.message.reply_text("🎓 به ربات آموزشی ریاضی خوش آمدید!\nیکی از گزینه‌های زیر را انتخاب کنید:", 
                                   reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text
    state = user_state.get(chat_id, {})

    # بازگشت به منوی اصلی
    if text == "بازگشت":
        user_state[chat_id] = {}
        keyboard = [["آموزش"], ["حل تمرینات"], ["آزمون‌های آنلاین"]]
        await update.message.reply_text("🎓 به منوی اصلی بازگشتید:", 
                                       reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
        return

    # انتخاب گزینه اصلی
    if text == "آموزش":
        state["mode"] = "learning"
        user_state[chat_id] = state
        keyboard = [[chapter] for chapter in lesson_files.keys()] + [["بازگشت"]]
        await update.message.reply_text("📚 فصل مورد نظر را انتخاب کنید:", 
                                       reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    
    elif text == "حل تمرینات":
        state["mode"] = "exercises"
        user_state[chat_id] = state
        keyboard = [[chapter] for chapter in lesson_files.keys()] + [["بازگشت"]]
        await update.message.reply_text("📚 فصل مورد نظر را برای تمرین انتخاب کنید:", 
                                       reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    
    # انتخاب فصل برای آموزش
    elif state.get("mode") == "learning" and "chapter" not in state:
        if text in lesson_files:
            state["chapter"] = text
            state["lesson_data"] = load_json(lesson_files[text])
            if state["lesson_data"] is None:
                await update.message.reply_text("❌ مشکلی در بارگذاری فصل وجود دارد. لطفاً دوباره تلاش کنید.")
                user_state[chat_id] = {}
                return
            state["step"] = 0
            user_state[chat_id] = state
            await send_lesson(update, context)
        else:
            await update.message.reply_text("فصل معتبر نیست.")

    # انتخاب فصل برای تمرین‌ها
    elif state.get("mode") == "exercises" and "chapter" not in state:
        if text in lesson_files:
            state["chapter"] = text
            state["lesson_data"] = load_json(lesson_files[text])
            if state["lesson_data"] is None:
                await update.message.reply_text("❌ مشکلی در بارگذاری فصل وجود دارد. لطفاً دوباره تلاش کنید.")
                user_state[chat_id] = {}
                return
            lessons = state["lesson_data"]["lessons"]
            for lesson in lessons:
                for i, ex in enumerate(lesson.get("exercises", []), 1):
                    await update.message.reply_text(f"📝 تمرین {i} ({lesson['lesson_title']}):\n{ex['question']}\n✅ پاسخ: {ex['answer']}\n📘 توضیح: {ex['solution']}")
            await update.message.reply_text("🎉 تمرین‌های این فصل به پایان رسید.")
            user_state[chat_id] = {}
        else:
            await update.message.reply_text("فصل معتبر نیست.")

    # پاسخ به سوالات آزمون
    elif "quiz_mode" in state:
        correct_answer = state["quiz_data"]["questions"][state["quiz_step"]]["correct_answer"]
        if text.strip() == correct_answer.strip():
            state["score"] += 1
            state["quiz_step"] += 1
            if state["quiz_step"] < len(state["quiz_data"]["questions"]):
                await send_quiz_question(update, context)
            else:
                await show_quiz_result(update, context)
        else:
            explanation = state["quiz_data"]["questions"][state["quiz_step"]].get("explanation", "توضیحی موجود نیست.")
            await update.message.reply_text(f"❌ پاسخ اشتباه! جواب درست: {correct_answer}\n📘 توضیح: {explanation}")
            # کاربر می‌تونه دوباره سعی کنه
            await send_quiz_question(update, context)
    
    else:
        await update.message.reply_text("لطفاً یکی از گزینه‌ها را از منوی زیر انتخاب کنید.")

async def send_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    state = user_state[chat_id]
    lessons = state["lesson_data"]["lessons"]
    if state["step"] < len(lessons):
        lesson = lessons[state["step"]]
        await update.message.reply_text(f"📖 *درس {lesson['lesson_title']}*\n\n{lesson['summary']}", parse_mode='Markdown')
        for i, ex in enumerate(lesson.get("exercises", []), 1):
            await update.message.reply_text(f"📝 تمرین {i}:\n{ex['question']}\n✅ پاسخ: {ex['answer']}\n📘 توضیح: {ex['solution']}")
        state["quiz_data"] = lesson.get("quiz", {}).get("questions", [])
        state["quiz_step"] = 0
        state["score"] = 0
        state["quiz_mode"] = True
        user_state[chat_id] = state
        if state["quiz_data"]:
            await update.message.reply_text("🧪 حالا آزمون درس را شروع می‌کنیم:")
            await send_quiz_question(update, context)
        else:
            await update.message.reply_text("🎉 این درس آزمون ندارد. برای ادامه به درس بعدی می‌رویم.")
            state["step"] += 1
            user_state[chat_id] = state
            await send_lesson(update, context)
    else:
        await update.message.reply_text("🎉 آموزش این فصل به پایان رسید. برای ادامه، یکی از گزینه‌ها را انتخاب کنید.")
        user_state[chat_id] = {}

async def send_quiz_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    state = user_state[chat_id]
    question_data = state["quiz_data"][state["quiz_step"]]
    question_text = f"❓ سوال {state['quiz_step']+1}: {question_data['question']}"
    choices = question_data.get("choices", [])
    if choices:
        keyboard = [[choice] for choice in choices] + [["بازگشت"]]
        await update.message.reply_text(question_text, reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    else:
        await update.message.reply_text(question_text)

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
        await send_lesson(update, context)

if __name__ == '__main__':
    app = ApplicationBuilder().token(API_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.run_polling()
