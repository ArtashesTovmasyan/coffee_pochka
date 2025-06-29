import logging
import json
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load or define coffee recipes grouped by categories
def load_recipes(path='recipes.json'):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

recipes = load_recipes()
categories = list(recipes.keys())

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton(cat)] for cat in categories]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        'Привет! Я CoffeeBot ☕️. Выбери категорию напитков:',
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Команды:\n'
        '/start - начать\n'
        '/help - справка\n'
        'Или выберите категорию из меню.'
    )

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    # Если выбрана категория
    if text in recipes:
        context.user_data['category'] = text
        drinks = list(recipes[text].keys())
        keyboard = [[KeyboardButton(dr)] for dr in drinks]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(f'Категория "{text}". Выберите напиток:', reply_markup=reply_markup)
        return
    # Если выбрано название напитка
    category = context.user_data.get('category')
    if category and text in recipes.get(category, {}):
        data = recipes[category][text]
        text_resp = f"*{text}*\n\n*Ингредиенты:*\n"
        text_resp += '\n'.join(f"- {ing}" for ing in data['ingredients'])
        text_resp += f"\n\n*Инструкции:*\n{data['instructions']}"
        await update.message.reply_markdown(text_resp)
        return
    await update.message.reply_text('Не понял запрос. Введите /help для справки.')

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error('Error: %s', context.error)

if __name__ == '__main__':
    app = ApplicationBuilder().token('7977580822:AAFMJlHGozEwpUXS-xcZvTsWURBfey7nMg4').build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_error_handler(error_handler)

    print('Bot is running...')
    app.run_polling()
