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

# Загрузка рецептов из JSON
def load_recipes(path='recipes.json'):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

recipes = load_recipes()
categories = list(recipes.keys())

# /start и /help: одинаковая клавиатура категорий
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton(cat, callback_data=f"cat|{cat}")]
        for cat in categories
    ]
    markup = InlineKeyboardMarkup(buttons)
    await update.effective_message.reply_text(
        "Привет! Я CoffeeBot ☕️\nВыбери категорию:",
        reply_markup=markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# Обработка нажатий inline-кнопок
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # убираем «часики»

    data = query.data.split("|", 1)
    action, key = data if len(data) == 2 else (None, None)

    # Нажали на категорию
    if action == "cat":
        drinks = list(recipes.get(key, {}).keys())
        buttons = [
            [InlineKeyboardButton(dr, callback_data=f"drink|{key}|{dr}")]
            for dr in drinks
        ]
        # Добавим кнопку «Назад» в категории
        buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="back|categories")])
        markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(f"Категория «{key}». Выберите напиток:", reply_markup=markup)
        return

    # Нажали на напиток
    if action == "drink":
        category, drink = key.split("|", 1)
        data = recipes[category][drink]
        text = f"*{drink}*\n\n*Ингредиенты:*\n"
        text += "\n".join(f"- {ing}" for ing in data["ingredients"])
        text += f"\n\n*Инструкции:*\n{data['instructions']}"

        # Кнопка «Назад к списку напитков»
        buttons = [
            [InlineKeyboardButton("◀️ Назад", callback_data=f"cat|{category}")],
            [InlineKeyboardButton("🏠 В начало", callback_data="back|categories")],
        ]
        markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
        return

    # Вернуться в категории
    if action == "back" and key == "categories":
        await start(update, context)
        return

# Ловим любые текстовые сообщения (для приватного чата)
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("Напиши /start, чтобы начать.")

# Логируем ошибки
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Ошибка: %s", context.error)

if __name__ == "__main__":
    # Замените на ваш токен или возьмите из окружения
    TOKEN = "YOUR_TOKEN_HERE"

    app = ApplicationBuilder().token(TOKEN).build()

    # Регистрация хэндлеров
    app.add_handler(CommandHandler(["start", "help"], start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_error_handler(error_handler)

    print("Bot is running...")
    app.run_polling()
