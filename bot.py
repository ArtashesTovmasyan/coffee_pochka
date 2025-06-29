import os
import logging
import json

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем токен из переменной окружения
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise RuntimeError("Не задана переменная окружения TELEGRAM_TOKEN")

# Загрузка рецептов из JSON

def load_recipes(path='recipes.json'):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

recipes = load_recipes()
categories = list(recipes.keys())

# /start и /help: показываем категории
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg is None:
        return
    buttons = [[InlineKeyboardButton(cat, callback_data=f"cat|{cat}")] for cat in categories]
    markup = InlineKeyboardMarkup(buttons)
    await msg.reply_text(
        "Привет! Я CoffeeBot ☕️\nВыбери категорию:",
        reply_markup=markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# Обработка нажатий inline-кнопок
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query is None or query.data is None or query.message is None:
        return
    await query.answer()

    action, key = query.data.split("|", 1)

    # Выбрана категория
    if action == "cat":
        drinks = list(recipes.get(key, {}))
        buttons = [[InlineKeyboardButton(dr, callback_data=f"drink|{key}|{dr}")] for dr in drinks]
        buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="back|categories")])
        markup = InlineKeyboardMarkup(buttons)
        await context.bot.edit_message_text(
            chat_id=query.message.chat.id,
            message_id=query.message.message_id,
            text=f"Категория «{key}». Выберите напиток:",
            reply_markup=markup
        )
        return

    # Выбран напиток
    if action == "drink":
        cat, dr = key.split("|", 1)
        data = recipes.get(cat, {}).get(dr)
        if data is None:
            return
        text = f"*{dr}*\n\n*Ингредиенты:*\n"
        text += "\n".join(f"- {ing}" for ing in data["ingredients"])
        text += f"\n\n*Инструкции:*\n{data['instructions']}"
        buttons = [
            [InlineKeyboardButton("◀️ Назад", callback_data=f"cat|{cat}")],
            [InlineKeyboardButton("🏠 В начало", callback_data="back|categories")],
        ]
        markup = InlineKeyboardMarkup(buttons)
        await context.bot.edit_message_text(
            chat_id=query.message.chat.id,
            message_id=query.message.message_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=markup
        )
        return

    # Назад к категориям
    if action == "back" and key == "categories":
        await start(update, context)
        return

# Ловим любые текстовые сообщения (приватный чат)
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg:
        await msg.reply_text("Напиши /start, чтобы начать.")

# Обработка ошибок
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Ошибка: %s", context.error)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler(["start", "help"], start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_error_handler(error_handler)

    print("Bot is running...")
    app.run_polling()
