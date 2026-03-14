import os
import asyncio
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUNO_API_KEY = os.getenv("SUNO_API_KEY")
ROBOKASSA_LOGIN = os.getenv("ROBOKASSA_LOGIN")
ROBOKASSA_PASS1 = os.getenv("ROBOKASSA_PASS1")

users = {}

PACKAGES = {
    "1": 249,
    "3": 699,
    "10": 1999,
    "50": 7999
}

# ----- Старт -----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in users:
        users[user_id] = {"remaining": 1}
    keyboard = [[InlineKeyboardButton("🎵 Создать песню", callback_data="create_song")]]
    text = f"""🎵 Привет!

Я создаю персональные песни.
У тебя {users[user_id]['remaining']} бесплатная генерация.

Нажми кнопку ниже чтобы начать."""
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ----- Выбор типа получателя -----
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id not in users:
        users[user_id] = {"remaining": 1}

    if query.data == "create_song":
        if users[user_id]["remaining"] <= 0:
            await offer_packages(query, user_id)
            return
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

    if query.data in ["lover","friend","wedding","company","other"]:
        users[user_id]["recipient_type"] = query.data
        users[user_id]["step"] = "name"
        if query.data == "wedding":
            await query.message.reply_text("Как зовут пару?\nПример: Оля и Дима")
        elif query.data == "company":
            await query.message.reply_text("Название компании\nПример: Coffeelab")
        else:
            await query.message.reply_text("Как зовут человека?\nПример: Оля")

# ----- Обработка текстовых ответов -----
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in users:
        users[user_id] = {"remaining":1}
    step = users[user_id].get("step")
    text = update.message.text

    if step == "name":
        users[user_id]["name"] = text
        users[user_id]["step"] = "occasion"
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
        return

    if step == "description":
        users[user_id]["description"] = text
        users[user_id]["step"] = "style"
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

# ----- Подробности: повод, стиль, настроение -----
async def callback_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id not in users:
        users[user_id] = {"remaining":1}

    data = query.data

    # повод
    if data in ["birthday","wedding_occasion","love","funny","thanks","event"]:
        users[user_id]["occasion"] = data
        users[user_id]["step"] = "description"
        await query.message.reply_text("Расскажи немного о человеке / паре / компании")
        return

    # стиль
    if data.startswith("style_"):
        users[user_id]["style"] = data.replace("style_","")
        users[user_id]["step"] = "mood"
        keyboard = [
            [InlineKeyboardButton("❤️ Романтичная", callback_data="mood_romantic")],
            [InlineKeyboardButton("🥹 Трогательная", callback_data="mood_touching")],
            [InlineKeyboardButton("😂 Смешная", callback_data="mood_funny")],
            [InlineKeyboardButton("🔥 Энергичная", callback_data="mood_energy")],
            [InlineKeyboardButton("✨ Другое", callback_data="mood_other")]
        ]
        await query.message.reply_text(
            "Настроение песни?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # настроение и генерация
    if data.startswith("mood_"):
        mood = data.replace("mood_","")
        users[user_id]["mood"] = mood

        if users[user_id]["remaining"] <= 0:
            await offer_packages(query,user_id)
            return
        users[user_id]["remaining"] -= 1

        # формируем промт
        u = users[user_id]
        prompt_text = f"""
Создай песню:

Для: {u.get('name')}
Повод: {u.get('occasion')}
Описание: {u.get('description')}
Стиль: {u.get('style')}
Настроение: {u.get('mood')}
"""

        # ---- Suno API (новый endpoint) ----
        headers = {
            "Authorization": f"Bearer {SUNO_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "prompt": prompt_text,
            "voice": "default",
            "format": "mp3"
        }

        # ---- Попытка 3 раза если Suno недоступен ----
        for attempt in range(3):
            try:
                response = requests.post("https://api.sunoapi.org/api/v1/generate", json=payload, headers=headers, timeout=60)
                response.raise_for_status()
                data = response.json()
                audio_url = data.get("audio_url") or data.get("url")
                if audio_url:
                    await query.message.reply_audio(audio_url, caption="Вот твоя песня! 🎵")
                    break
                else:
                    if attempt < 2:
                        await query.message.reply_text("Сервис Suno временно недоступен. Повторная попытка...")
                        await asyncio.sleep(5)
                    else:
                        await query.message.reply_text("Сервис Suno временно недоступен. Попробуй позже.")
            except requests.exceptions.RequestException:
                if attempt < 2:
                    await query.message.reply_text("Сервис Suno временно недоступен. Повторная попытка...")
                    await asyncio.sleep(5)
                else:
                    await query.message.reply_text("Сервис Suno временно недоступен. Попробуй позже.")

        users[user_id]["step"] = None

# ----- Предложение купить пакет -----
async def offer_packages(query, user_id):
    keyboard = [
        [InlineKeyboardButton(f"1 песня – {PACKAGES['1']}₽", callback_data="buy_1")],
        [InlineKeyboardButton(f"3 песни – {PACKAGES['3']}₽", callback_data="buy_3")],
        [InlineKeyboardButton(f"10 песен – {PACKAGES['10']}₽", callback_data="buy_10")],
        [InlineKeyboardButton(f"50 песен – {PACKAGES['50']}₽", callback_data="buy_50")]
    ]
    await query.message.reply_text(
        "У тебя закончились бесплатные генерации. Выбери пакет:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ----- Robokassa -----
def get_robokassa_link(user_id, package):
    price = PACKAGES[package]
    invoice_id = f"{user_id}_{package}"
    return f"https://auth.robokassa.ru/Merchant/Index.aspx?MrchLogin={ROBOKASSA_LOGIN}&OutSum={price}&InvId={invoice_id}&Desc=Пакет песен {package}&SignatureValue={ROBOKASSA_PASS1}"

async def package_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if query.data.startswith("buy_"):
        package = query.data.split("_")[1]
        link = get_robokassa_link(user_id, package)
        await query.message.reply_text(f"Оплатите пакет здесь: {link}")

# ----- Запуск -----
async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons, pattern="^(create_song|lover|friend|wedding|company|other)$"))
    app.add_handler(CallbackQueryHandler(callback_details, pattern="^(birthday|wedding_occasion|love|funny|thanks|event|style_|mood_)"))
    app.add_handler(CallbackQueryHandler(package_purchase, pattern="^buy_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))
    print("Bot started")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(main())
