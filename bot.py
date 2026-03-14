import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

user_data_store = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🎵 Создать песню", callback_data="create_song")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "🎵 Привет!\n\n"
        "Я создаю персональные песни.\n\n"
        "Первая песня бесплатно.\n"
        "Ответь на несколько вопросов и я создам песню."
    )

    await update.message.reply_text(text, reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "create_song":

        keyboard = [
            [InlineKeyboardButton("❤️ Для любимого человека", callback_data="lover")],
            [InlineKeyboardButton("🎂 Для друга", callback_data="friend")],
            [InlineKeyboardButton("💍 Свадебная песня", callback_data="wedding")],
            [InlineKeyboardButton("🎉 Для компании", callback_data="company")],
            [InlineKeyboardButton("✨ Другое", callback_data="other")],
        ]

        await query.message.reply_text(
            "Для кого будет песня?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in user_data_store:
        user_data_store[user_id] = {}

    text = update.message.text

    if "name" not in user_data_store[user_id]:
        user_data_store[user_id]["name"] = text
        await update.message.reply_text("Какой повод для песни?")
        return

    if "occasion" not in user_data_store[user_id]:
        user_data_store[user_id]["occasion"] = text
        await update.message.reply_text("Расскажи немного о человеке")
        return

    if "description" not in user_data_store[user_id]:
        user_data_store[user_id]["description"] = text
        await update.message.reply_text("Выбери стиль песни: Поп / Рэп / Рок")
        return

    if "style" not in user_data_store[user_id]:
        user_data_store[user_id]["style"] = text
        await update.message.reply_text("Какое настроение песни?")
        return

    if "mood" not in user_data_store[user_id]:
        user_data_store[user_id]["mood"] = text

        data = user_data_store[user_id]

        prompt = f"""
Create a song.

Name: {data['name']}
Occasion: {data['occasion']}
Description: {data['description']}
Style: {data['style']}
Mood: {data['mood']}
"""

        await update.message.reply_text(
            "🎵 Песня создается...\n\nВот промт для Suno:\n\n" + prompt
        )


def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot started")

    app.run_polling()


if __name__ == "__main__":
    main()
