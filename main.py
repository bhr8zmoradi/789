import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# Load config
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

# Load content
with open("content_7th.json", "r", encoding="utf-8") as f:
    content_7th = json.load(f)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for i, chapter in enumerate(content_7th["فصل‌ها"]):
        keyboard.append([
            InlineKeyboardButton(chapter["عنوان"], callback_data=f"chapter_{i}")
        ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("یکی از فصل‌های زیر را انتخاب کن:", reply_markup=reply_markup)

# Callback handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("chapter_"):
        chapter_index = int(query.data.split("_")[1])
        chapter = content_7th["فصل‌ها"][chapter_index]
        keyboard = [
            [InlineKeyboardButton(sub, callback_data=f"ignore_{i}")]
            for i, sub in enumerate(chapter["زیرمباحث"])
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=f"زیرمباحث فصل «{chapter['عنوان']}»:", reply_markup=reply_markup
        )

# Ignore handler to avoid errors for subtopics (can be extended later)
async def ignore_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("این بخش هنوز فعال نشده است.", show_alert=True)

if __name__ == '__main__':
    app = ApplicationBuilder().token(config["TOKEN"]).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler, pattern=r"^chapter_"))
    app.add_handler(CallbackQueryHandler(ignore_handler, pattern=r"^ignore_"))

    app.run_polling()
