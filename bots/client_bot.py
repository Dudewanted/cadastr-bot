"""
🤖 КЛИЕНТСКИЙ БОТ ДЛЯ ГЕОДЕЗИЧЕСКИХ УСЛУГ

▌ Функционал:
- Главное меню: Заявка, Частые вопросы, Контакты, О нас
- Заявка: пошаговый ввод геолокации или адреса → телефона
- Интеграция с Google Sheets (append_to_sheet)

"""

import logging
from datetime import datetime
import pytz
from typing import Dict, Any

from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from services.gsheets import append_to_sheet

# 📌 Константы состояний диалога
CHOOSING, LOCATION, PHONE = range(3)

# ⏰ Временная зона
TIMEZONE = pytz.timezone("Europe/Moscow")

# 🤖 Главное меню
main_keyboard = ReplyKeyboardMarkup([
    ["📨 Отправить заявку"],
    ["❓ Частые вопросы", "📞 Контакты", "ℹ️ О нас"]
], resize_keyboard=True)

# 🚀 Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Здравствуйте! Я бот для подачи заявок на геодезические услуги.\n\n"
        "Выберите нужный пункт в меню:",
        reply_markup=main_keyboard
    )
    return CHOOSING

# 📨 Отправка заявки: выбор геолокации или адреса
async def send_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("📍 Отправить геолокацию", request_location=True)],
        [KeyboardButton("🏠 Ввести адрес вручную")]
    ]
    await update.message.reply_text(
        "Пожалуйста, отправьте адрес объекта или поделитесь геолокацией:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return LOCATION

# 📍 Обработка геолокации
async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.location:
        lat = update.message.location.latitude
        lon = update.message.location.longitude
        context.user_data["address"] = f"Геолокация: {lat}, {lon}"
    else:
        context.user_data["address"] = update.message.text.strip()
    await update.message.reply_text(
        "Теперь отправьте ваш номер телефона:",
        reply_markup=ReplyKeyboardRemove()
    )
    return PHONE

# ☎️ Обработка телефона и отправка заявки
async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    context.user_data["phone"] = phone
    address = context.user_data.get("address", "Не указано")

    timestamp = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
    append_to_sheet([
        address,
        phone,
        timestamp,
        "Новая"
    ])

    await update.message.reply_text(
        "✅ Заявка успешно отправлена!\nМы свяжемся с вами в ближайшее время.",
        reply_markup=main_keyboard
    )
    return CHOOSING

# ❓ Частые вопросы
async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❓ Часто задаваемые вопросы:\n"
        "- Сколько стоит услуга?\n"
        "- Какие документы нужны?\n"
        "- Сроки выполнения работ?\n\n"
        "📞 Мы готовы ответить на ваши вопросы в чате или по телефону!"
    )

# 📞 Контакты
async def contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 Наши контакты:\n"
        "Телефон: +7-XXX-XXX-XX-XX\n"
        "Email: example@mail.com\n"
        "Адрес: г. Пример, ул. Улица, д. 1"
    )

# ℹ️ О нас
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏗 Мы оказываем кадастровые и геодезические услуги:\n"
        "- Межевание\n"
        "- Съемка участка\n"
        "- Подготовка кадастровых планов и схем\n"
        "Работаем по всей области."
    )

# ❌ Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Выход из режима ввода.",
        reply_markup=main_keyboard
    )
    return ConversationHandler.END

# 🚀 Запуск бота
async def run_client_bot():
    from config import TELEGRAM_CLIENT_TOKEN

    app = Application.builder().token(TELEGRAM_CLIENT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("📨 Отправить заявку"), send_request)],
        states={
            LOCATION: [MessageHandler(filters.LOCATION | filters.TEXT & ~filters.COMMAND, handle_location)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.Regex("❓ Частые вопросы"), faq))
    app.add_handler(MessageHandler(filters.Regex("📞 Контакты"), contacts))
    app.add_handler(MessageHandler(filters.Regex("ℹ️ О нас"), about))

    await app.run_polling()
