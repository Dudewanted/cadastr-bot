import os
import telebot
from telebot import types
from dotenv import load_dotenv
from google_sheets import add_request
import uuid
from datetime import datetime

load_dotenv()

bot = telebot.TeleBot(os.getenv('CLIENT_BOT_TOKEN'))
user_data = {}

# Клавиатуры
main_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.row("📍 Отправить заявку")
main_menu.row("❓ Частые вопросы", "📞 Контакты", "ℹ️ О нас")

request_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
request_menu.row("🌍 Отправить геолокацию", "🏠 Указать адрес")
request_menu.row("📱 Отправить телефон")
request_menu.row("🔙 Назад")

phone_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
phone_menu.add(types.KeyboardButton("📱 Поделиться телефоном", request_contact=True))
phone_menu.row("🔙 Назад")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, 
                    "Добро пожаловать в бот для кадастровых работ!",
                    reply_markup=main_menu)

@bot.message_handler(func=lambda m: m.text == "📍 Отправить заявку")
def start_request(message):
    bot.send_message(message.chat.id, 
                    "Укажите месторасположение объекта:",
                    reply_markup=request_menu)

@bot.message_handler(func=lambda m: m.text in ["🌍 Отправить геолокацию", "🏠 Указать адрес"])
def ask_location(message):
    if message.text == "🌍 Отправить геолокацию":
        bot.send_message(message.chat.id, 
                        "Пожалуйста, отправьте вашу геолокацию:",
                        reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(message.chat.id,
                        "Введите адрес вручную:",
                        reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(content_types=['location'])
def handle_location(message):
    lat = message.location.latitude
    lon = message.location.longitude
    user_data[message.chat.id] = {'address': f"Геолокация: {lat}, {lon}"}
    bot.send_message(message.chat.id, 
                    "Адрес сохранен. Теперь отправьте ваш телефон:",
                    reply_markup=phone_menu)

@bot.message_handler(func=lambda m: m.text == "📱 Отправить телефон" or m.text == "🔙 Назад")
def handle_navigation(message):
    if message.text == "📱 Отправить телефон":
        bot.send_message(message.chat.id,
                        "Нажмите кнопку ниже, чтобы поделиться телефоном:",
                        reply_markup=phone_menu)
    else:
        bot.send_message(message.chat.id,
                        "Главное меню:",
                        reply_markup=main_menu)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    if message.chat.id not in user_data:
        bot.send_message(message.chat.id,
                        "Сначала укажите адрес объекта",
                        reply_markup=request_menu)
        return
    
    phone = message.contact.phone_number
    address = user_data[message.chat.id]['address']
    
    if add_request(address, phone):
        bot.send_message(message.chat.id,
                        "✅ Заявка отправлена! Мы свяжемся с вами в ближайшее время.",
                        reply_markup=main_menu)
        del user_data[message.chat.id]
    else:
        bot.send_message(message.chat.id,
                        "⚠️ Ошибка при отправке заявки. Пожалуйста, попробуйте позже.",
                        reply_markup=main_menu)

@bot.message_handler(func=lambda m: m.text == "❓ Частые вопросы")
def show_faq(message):
    faq = {
        "Сроки выполнения": "Обычно 5-10 рабочих дней",
        "Стоимость услуг": "Зависит от сложности работ",
        "Необходимые документы": "Паспорт, правоустанавливающие документы"
    }
    
    keyboard = types.InlineKeyboardMarkup()
    for question in faq:
        keyboard.add(types.InlineKeyboardButton(
            text=question,
            callback_data=f"faq_{question}"))
    
    bot.send_message(message.chat.id,
                    "Выберите вопрос:",
                    reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith('faq_'))
def answer_faq(call):
    question = call.data[4:]
    answers = {
        "Сроки выполнения": "Обычно 5-10 рабочих дней",
        "Стоимость услуг": "Зависит от сложности работ",
        "Необходимые документы": "Паспорт, правоустанавливающие документы"
    }
    bot.answer_callback_query(call.id, answers.get(question, "Информация уточняется"))

@bot.message_handler(func=lambda m: m.text in ["📞 Контакты", "ℹ️ О нас"])
def show_info(message):
    if message.text == "📞 Контакты":
        text = ("📞 Телефон: +7 (XXX) XXX-XX-XX\n"
               "📧 Email: example@mail.com\n"
               "🏢 Адрес: г. Москва, ул. Примерная, 123")
    else:
        text = ("Мы оказываем полный спектр кадастровых услуг:\n"
               "- Межевание земельных участков\n"
               "- Постановка на кадастровый учет\n"
               "- Подготовка технических планов")
    
    bot.send_message(message.chat.id, text, reply_markup=main_menu)

if __name__ == '__main__':
    bot.polling(none_stop=True)