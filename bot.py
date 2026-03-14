import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

users = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [[InlineKeyboardButton("🎵 Создать песню", callback_data="create_song")]]

    text = """
🎵 Привет!

Я создаю персональные песни.

Первая песня — бесплатно.

Ответь на несколько вопросов и я создам песню для тебя.
"""

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if user_id not in users:
        users[user_id] = {}

    if query.data == "create_song":

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

    elif query.data in ["lover","friend","wedding","company","other"]:

        users[user_id]["recipient_type"] = query.data

        if query.data == "wedding":

            await query.message.reply_text(
                "Как зовут пару?\n\nПример: Оля и Дима"
            )

        elif query.data == "company":

            await query.message.reply_text(
                "Название компании\n\nПример: Coffeelab"
            )

        else:

            await query.message.reply_text(
                "Как зовут человека?\n\nПример: Оля"
            )

        users[user_id]["step"] = "name"

    elif query.data == "birthday":

        users[user_id]["occasion"] = "День рождения"
        users[user_id]["step"] = "description"

        await query.message.reply_text(
            "Расскажи немного о человеке / паре / компании"
        )

    elif query.data == "style_pop":

        users[user_id]["style"] = "Поп"
        users[user_id]["step"] = "mood"

        await send_mood(query)

    elif query.data == "mood_romantic":

        users[user_id]["mood"] = "Романтичная"
        await generate_prompt(query, user_id)


async def send_occasion(update):

    keyboard = [
        [InlineKeyboardButton("🎂 День рождения", callback_data="birthday")],
        [InlineKeyboardButton("💍 Свадьба", callback_data="wedding_occasion")],
        [InlineKeyboardButton("❤️ Признание в любви", callback_data="love")],
        [InlineKeyboardButton("😂 Шуточная песня", callback_data="funny")],
        [InlineKeyboardButton("🙏 Благодарность", callback_data="thanks")],
        [InlineKeyboardButton("🎉 Праздник / событие", callback_data="event")]
    ]

    await update.message.reply_text(
        "Какой повод для песни?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def send_style(update):

    keyboard = [
        [InlineKeyboardButton("Поп", callback_data="style_pop")],
        [InlineKeyboardButton("Рэп", callback_data="style_rap")],
        [InlineKeyboardButton("Рок", callback_data="style_rock")],
        [InlineKeyboardButton("Душевная баллада", callback_data="style_ballad")],
        [InlineKeyboardButton("Весёлая песня", callback_data="style_fun")],
        [InlineKeyboardButton("Современный хит", callback_data="style_hit")]
    ]

    await update.message.reply_text(
        "Выберите стиль песни",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def send_mood(query):

    keyboard = [
        [InlineKeyboardButton("❤️ Романтичная", callback_data="mood_romantic")],
        [InlineKeyboardButton("🥹 Трогательная", callback_data="mood_touching")],
        [InlineKeyboardButton("😂 Смешная", callback_data="mood_funny")],
        [InlineKeyboardButton("🔥 Энергичная", callback_data="mood_energy")]
    ]

    await query.message.reply_text(
        "Настроение песни?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def generate_prompt(query, user_id):

    data = users[user_id]

    prompt = f"""
Create a song.

Name: {data['name']}
Occasion: {data['occasion']}
Description: {data['description']}
Style: {data['style']}
Mood: {data['mood']}
"""

    await query.message.reply_text(
        "🎵 Песня создается...\n\nПромт для Suno:\n\n" + prompt
    )


async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    if user_id not in users:
        users[user_id] = {}

    text = update.message.text

    step = users[user_id].get("step")

    if step == "name":

        users[user_id]["name"] = text
        users[user_id]["step"] = "occasion"

        await send_occasion(update)

    elif step == "description":

        users[user_id]["description"] = text
        users[user_id]["step"] = "style"

        await send_style(update)


def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))

    print("Bot started")

    app.run_polling()


if __name__ == "__main__":
    main()
