import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    filters, ContextTypes
)

TOKEN = os.getenv("BOT_TOKEN")

# хранилище данных пользователей
users = {}

# старт бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🎵 Создать песню", callback_data="create_song")]]
    text = """🎵 Привет!
Я создаю персональные песни.
Первая песня — бесплатно.
Нажми кнопку ниже чтобы начать."""
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


# обработка кнопок
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in users:
        users[user_id] = {}

    # кнопка Создать песню
    if query.data == "create_song":
        keyboard = [
            [InlineKeyboardButton("❤️ Для любимого человека", callback_data="lover")],
            [InlineKeyboardButton("🎂 Для друга", callback_data="friend")],
            [InlineKeyboardButton("💍 Свадебная песня", callback_data="wedding")],
            [InlineKeyboardButton("🎉 Для компании / команды", callback_data="company")],
            [InlineKeyboardButton("✨ Другое", callback_data="other")]
        ]
        await query.message.reply_text(
            "Для кого будет песня?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # кнопки типа получателя
    if query.data in ["lover", "friend", "wedding", "company", "other"]:
        users[user_id]["recipient_type"] = query.data
        users[user_id]["step"] = "name"

        if query.data == "wedding":
            await query.message.reply_text("Как зовут пару?\nПример: Оля и Дима")
        elif query.data == "company":
            await query.message.reply_text("Название компании\nПример: Coffeelab")
        else:
            await query.message.reply_text("Как зовут человека?\nПример: Оля")


# обработка сообщений (текстовые ответы)
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in users:
        users[user_id] = {}

    step = users[user_id].get("step")
    text = update.message.text

    # шаг "имя"
    if step == "name":
        users[user_id]["name"] = text
        users[user_id]["step"] = "occasion"
        # вопрос о поводе
        keyboard = [
            [InlineKeyboardButton("🎂 День рождения", callback_data="birthday")],
            [InlineKeyboardButton("💍 Свадьба", callback_data="wedding_occasion")],
            [InlineKeyboardButton("❤️ Признание в любви", callback_data="love")],
            [InlineKeyboardButton("😂 Шуточная песня", callback_data="funny")],
            [InlineKeyboardButton("🙏 Благодарность", callback_data="thanks")],
            [InlineKeyboardButton("🎉 Праздник / событие", callback_data="event")],
        ]
        await update.message.reply_text(
            "Какой повод для песни?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # шаг "описание"
    if step == "description":
        users[user_id]["description"] = text
        users[user_id]["step"] = "style"
        # вопрос стиль
        keyboard = [
            [InlineKeyboardButton("Поп", callback_data="style_pop")],
            [InlineKeyboardButton("Рэп", callback_data="style_rap")],
            [InlineKeyboardButton("Рок", callback_data="style_rock")],
            [InlineKeyboardButton("Душевная баллада", callback_data="style_ballad")],
            [InlineKeyboardButton("Весёлая песня", callback_data="style_fun")],
            [InlineKeyboardButton("Современный хит", callback_data="style_hit")],
        ]
        await update.message.reply_text(
            "Выберите стиль песни",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

# обработка кнопок: повод, стиль, настроение
async def callback_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in users:
        users[user_id] = {}

    data = query.data

    # повод
    if data in ["birthday", "wedding_occasion", "love", "funny", "thanks", "event"]:
        users[user_id]["occasion"] = data
        users[user_id]["step"] = "description"
        await query.message.reply_text(
            "Расскажи немного о человеке / паре / компании"
        )
        return

    # стиль
    if data.startswith("style_"):
        users[user_id]["style"] = data.replace("style_", "")
        users[user_id]["step"] = "mood"
        keyboard = [
            [InlineKeyboardButton("❤️ Романтичная", callback_data="mood_romantic")],
            [InlineKeyboardButton("🥹 Трогательная", callback_data="mood_touching")],
            [InlineKeyboardButton("😂 Смешная", callback_data="mood_funny")],
            [InlineKeyboardButton("🔥 Энергичная", callback_data="mood_energy")],
            [InlineKeyboardButton("✨ Другое", callback_data="mood_other")],
        ]
        await query.message.reply_text(
            "Настроение песни?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # настроение
    if data.startswith("mood_"):
        mood = data.replace("mood_", "")
        users[user_id]["mood"] = mood
        # соберём промт
        u = users[user_id]
        prompt = f"""
Создай песню:

Для: {u.get('name')}
Повод: {u.get('occasion')}
Описание: {u.get('description')}
Стиль: {u.get('style')}
Настроение: {u.get('mood')}
"""
        await query.message.reply_text("🎵 Песня создается...\n\nПромт для Suno:\n" + prompt)
        # сброс для нового трека
        users[user_id]["step"] = None

# основной запуск
async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons, pattern="^(create_song|lover|friend|wedding|company|other)$"))
    app.add_handler(CallbackQueryHandler(callback_details, pattern="^(birthday|wedding_occasion|love|funny|thanks|event|style_|mood_)"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))

    print("Bot started")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
