# Здесь будет основной код, который мы позже вставим
import os
from dotenv import load_dotenv
load_dotenv()
import telebot
import openai
from telebot import types
from datetime import datetime

# Загрузка токенов из .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Отладочные сообщения
print("=== Debug Information ===")
print(f"Current working directory: {os.getcwd()}")
print(f"BOT_TOKEN: {BOT_TOKEN}")
print(f"OPENAI_API_KEY: {OPENAI_API_KEY}")
print("=======================")

openai.api_key = OPENAI_API_KEY

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)

# Простая база пользователей
user_data = {}
feedback_list = []

class User:
    def __init__(self, user_id):
        self.user_id = user_id
        self.child_age = None
        self.allergies = []
        self.last_consultation = None

def get_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = User(user_id)
    return user_data[user_id]

# База знаний
BABY_FOOD_KNOWLEDGE = """
Ты — эксперт по детскому питанию, следуешь российским стандартам.
Всегда уточняй: 'Проконсультируйтесь с педиатром перед введением новых продуктов'.

6м: овощи (кабачок, брокколи, цветная капуста)
7м: каши без глютена (рис, гречка, кукуруза)
8м: мясо (индейка, кролик)
9м: фрукты (яблоко, груша, банан)
10м: рыба (треска, хек)
12м: творог, кефир

НЕ рекомендовать до года: мед, орехи, цельное молоко, яйца до 8м.
"""

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    user = get_user(message.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👶 Профиль", "🍽️ Рецепт", "🤖 Вопрос", "📝 Отзыв")
    bot.send_message(message.chat.id, "Привет! Я NutriKid — бот по детскому питанию. Что хотите сделать?", reply_markup=markup)

# Профиль
@bot.message_handler(func=lambda m: m.text == "👶 Профиль")
def set_profile(message):
    msg = bot.send_message(message.chat.id, "Введите возраст ребёнка в месяцах (например: 6):")
    bot.register_next_step_handler(msg, process_age)

def process_age(message):
    try:
        age = int(message.text)
        if age < 4 or age > 60:
            bot.send_message(message.chat.id, "⚠️ Введите возраст от 4 до 60 месяцев.")
            return
        user = get_user(message.from_user.id)
        user.child_age = age
        bot.send_message(message.chat.id, f"✅ Возраст {age} мес сохранён.")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Пожалуйста, введите только число.")

# Получение рецепта
@bot.message_handler(func=lambda m: m.text == "🍽️ Рецепт")
def get_recipe(message):
    user = get_user(message.from_user.id)
    if not user.child_age:
        bot.send_message(message.chat.id, "Сначала настройте профиль 👶")
        return

    prompt = f"{BABY_FOOD_KNOWLEDGE}\nВозраст ребёнка: {user.child_age} месяцев\nСгенерируй 3 рецепта на русском."
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )
        reply = response.choices[0].message.content
        bot.send_message(message.chat.id, reply)
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Ошибка при генерации рецепта: {str(e)}")

# AI-консультация
@bot.message_handler(func=lambda m: m.text == "🤖 Вопрос")
def ask_question(message):
    msg = bot.send_message(message.chat.id, "Введите вопрос по детскому питанию:")
    bot.register_next_step_handler(msg, process_question)

def process_question(message):
    prompt = f"{BABY_FOOD_KNOWLEDGE}\nВопрос: {message.text}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )
        reply = response.choices[0].message.content
        bot.send_message(message.chat.id, reply)
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Ошибка при ответе: {str(e)}")

# Форма обратной связи
@bot.message_handler(func=lambda m: m.text == "📝 Отзыв")
def get_feedback(message):
    msg = bot.send_message(message.chat.id, "Пожалуйста, оставьте ваш отзыв о боте:")
    bot.register_next_step_handler(msg, save_feedback)

def save_feedback(message):
    feedback_list.append((message.from_user.username or "неизвестно", message.text, datetime.now()))
    bot.send_message(message.chat.id, "Спасибо за ваш отзыв! 🙏")

# Запуск
bot.infinity_polling()
