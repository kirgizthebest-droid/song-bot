import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

user_data_store = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🎵 Создать песню", callback_data="create_song")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "🎵 Привет!\n\n"
        "Я создаю персональные песни.\n"
        "Первая песня бесплатно.\n\n"
        "Нажми кнопку ниже чтобы создать песню."
    )

    await update.message.reply_text(text, reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("❤️ Для любимого человека", callback_data="lover")],
        [InlineKeyboardButton("🎂 Для друга", callback_data="friend")],
        [InlineKeyboardButton("💍 Свадебная песня", callback_data="wedding")],
        [InlineKeyboardButton("🎉 Для компании", callback_data="company")],
        [InlineKeyboardButton("✨ Другое", callback_data="other")]
    ]

    await query.message.reply_text(
        "Для кого будет песня?",
        reply_markup=InlineKeyboardMarkup(keyboard)
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
        await update.message.reply_text("Расскажи немного о человеке / паре")
        return

    if "description" not in user_data_store[user_id]:

        user_data_store[user_id]["description"] = text
        await update.message.reply_text("Стиль песни? (Поп / Рэп / Рок)")
        return

    if "style" not in user_data_store[user_id]:

        user_data_store[user_id]["style"] = text
        await update.message.reply_text("Настроение песни?")
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
            "🎵 Песня создается...\n\nПромт для Suno:\n" + prompt
        )


async def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot started")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
if __name__ == "__main__":
    main()
