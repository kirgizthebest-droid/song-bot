import os
import asyncio
import aiohttp
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")
SUNO_API_KEY = os.getenv("SUNO_API_KEY")

users = {}

# ---------------- HTTP SERVER (для Render) ----------------

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_web():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

Thread(target=run_web).start()

# ---------------- SUNO GENERATION ----------------

async def generate_song(prompt):

    url = "https://api.sunoapi.org/api/v1/generate"

    headers = {
        "Authorization": f"Bearer {SUNO_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "prompt": prompt,
        "style": "pop"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as r:
            result = await r.json()
            return result

# ---------------- BOT ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("🎵 Создать песню", callback_data="create")],
        [InlineKeyboardButton("💳 Купить пакет", callback_data="buy")]
    ]

    await update.message.reply_text(
        "🎶 Добро пожаловать в AI Song Bot\n\nСоздай свою уникальную песню!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("1 песня — 249₽", callback_data="p1")],
        [InlineKeyboardButton("3 песни — 599₽", callback_data="p3")],
        [InlineKeyboardButton("10 песен — 1490₽", callback_data="p10")],
        [InlineKeyboardButton("50 песен — 4990₽", callback_data="p50")]
    ]

    await update.callback_query.edit_message_text(
        "Выбери пакет:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def create(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.callback_query.message.reply_text(
        "Напиши описание песни\n\nНапример:\nпесня для девушки в стиле романтический поп"
    )

    context.user_data["wait_prompt"] = True


async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if context.user_data.get("wait_prompt"):

        prompt = update.message.text

        await update.message.reply_text("⏳ Генерирую песню...")

        result = await generate_song(prompt)

        if "audio_url" in result:
            await update.message.reply_audio(result["audio_url"])
        else:
            await update.message.reply_text("❌ Ошибка генерации")

        context.user_data["wait_prompt"] = False


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.data == "create":
        await create(update, context)

    elif query.data == "buy":
        await buy(update, context)


def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(CommandHandler("create", create))

    app.add_handler(
        telegram.ext.MessageHandler(
            telegram.ext.filters.TEXT,
            message
        )
    )

    print("Bot started")

    app.run_polling()


if __name__ == "__main__":
    main()
