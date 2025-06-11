# main.py — обновлённая версия
import os
from dotenv import load_dotenv
from telebot import TeleBot, types
from datetime import datetime
from openai import OpenAI
import csv

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Инициализация клиентов
bot = TeleBot(BOT_TOKEN)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Пользователи и отзывы
user_data = {}
feedback_file = "feedback.csv"

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

# Главное меню
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👶 Профиль", "🍽️ Рецепт", "🤖 Вопрос", "📝 Отзыв")
    bot.send_message(message.chat.id, "Привет! Я NutriKid — бот по детскому питанию. Что хотите сделать?", reply_markup=markup)

# Профиль
@bot.message_handler(func=lambda m: "Профиль" in m.text)
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

# Рецепт
@bot.message_handler(func=lambda m: "Рецепт" in m.text)
def get_recipe(message):
    user = get_user(message.from_user.id)
    if not user.child_age:
        bot.send_message(message.chat.id, "Сначала настройте профиль 👶")
        return

    prompt = f"{BABY_FOOD_KNOWLEDGE}\nВозраст ребёнка: {user.child_age} месяцев\nСгенерируй 3 рецепта на русском."
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )
        reply = response.choices[0].message.content
        bot.send_message(message.chat.id, reply)
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Ошибка при генерации рецепта: {str(e)}")

# Вопрос
@bot.message_handler(func=lambda m: "Вопрос" in m.text)
def ask_question(message):
    msg = bot.send_message(message.chat.id, "Введите вопрос по детскому питанию:")
    bot.register_next_step_handler(msg, process_question)

def process_question(message):
    prompt = f"{BABY_FOOD_KNOWLEDGE}\nВопрос: {message.text}"
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )
        reply = response.choices[0].message.content
        bot.send_message(message.chat.id, reply)
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Ошибка при ответе: {str(e)}")

# Отзыв
@bot.message_handler(func=lambda m: "Отзыв" in m.text)
def get_feedback(message):
    msg = bot.send_message(message.chat.id, "Пожалуйста, оставьте ваш отзыв о боте:")
    bot.register_next_step_handler(msg, save_feedback)

def save_feedback(message):
    user = message.from_user.username or "аноним"
    feedback = message.text
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(feedback_file, "a", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        writer.writerow([user, feedback, timestamp])
    bot.send_message(message.chat.id, "Спасибо за ваш отзыв! 🙏")

# Запуск
bot.infinity_polling()
