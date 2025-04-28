import os
import telebot
from telebot import types
from dotenv import load_dotenv
from google_sheets import get_pending_requests, update_status
import time

load_dotenv()

bot = telebot.TeleBot(os.getenv('ADMIN_BOT_TOKEN'))

def create_admin_keyboard(request_id, phone):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton(
            text="📞 Позвонить",
            callback_data=f"call_{phone}"),
        types.InlineKeyboardButton(
            text="🗺️ Показать на карте",
            url=f"https://www.google.com/maps?q={phone}")
    )
    keyboard.row(
        types.InlineKeyboardButton(
            text="✅ Выполнено",
            callback_data=f"done_{request_id}"),
        types.InlineKeyboardButton(
            text="🔄 В работе",
            callback_data=f"progress_{request_id}")
    )
    return keyboard

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, 
                    "Админ-панель управления заявками")

@bot.callback_query_handler(func=lambda call: call.data.startswith(('call_', 'done_', 'progress_')))
def handle_callbacks(call):
    if call.data.startswith('call_'):
        phone = call.data[5:]
        bot.answer_callback_query(call.id, f"Звоним на номер: {phone}")
    else:
        action, request_id = call.data.split('_')
        new_status = "Выполнено" if action == "done" else "В работе"
        
        if update_status(request_id, new_status):
            bot.answer_callback_query(call.id, f"Статус изменен на: {new_status}")
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=None)
        else:
            bot.answer_callback_query(call.id, "Ошибка обновления статуса")

def check_new_requests():
    while True:
        pending = get_pending_requests()
        for req in pending:
            message = (f"Новая заявка #{req['id']}\n"
                      f"📌 Адрес: {req['address']}\n"
                      f"📞 Телефон: {req['phone']}\n"
                      f"📅 Дата: {req['date']}")
            
            bot.send_message(
                os.getenv('ADMIN_CHAT_ID'),
                message,
                reply_markup=create_admin_keyboard(req['id'], req['phone']))
        
        time.sleep(60)  # Проверка каждую минуту

if __name__ == '__main__':
    import threading
    threading.Thread(target=check_new_requests, daemon=True).start()
    bot.polling(none_stop=True)