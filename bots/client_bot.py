"""
Telegram бот для клиентов кадастровых услуг.
Основные функции:
- Прием заявок с геолокацией/адресом и контактными данными
- Ответы на частые вопросы
- Предоставление контактной информации
"""

import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
)
from services.gsheets import append_to_sheet

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename="client_bot.log"  # Логи будут сохраняться в файл
)
logger = logging.getLogger(__name__)

# =============================================
# КОНСТАНТЫ И НАСТРОЙКИ
# =============================================

# Состояния для ConversationHandler
LOCATION, PHONE = range(2)

# Текстовые шаблоны
TEXTS = {
    "welcome": "🏠 <b>Геодезические и кадастровые услуги</b>\n\n"
               "Выберите действие из меню ниже:",
    "request": "📍 <b>Отправка заявки</b>\n\n"
               "Пожалуйста, укажите местоположение объекта:",
    "location_received": "✅ <b>Местоположение получено</b>\n\n"
                        "Теперь укажите ваш телефон:",
    "phone_received": "📝 <b>Спасибо за заявку!</b>\n\n"
                      "Наш специалист свяжется с вами в течение 24 часов.",
    "cancel": "🚫 Действие отменено. Возврат в главное меню."
}

# =============================================
# ОСНОВНЫЕ ФУНКЦИИ БОТА
# =============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start и главного меню"""
    buttons = [
        ["📨 Отправить заявку"],
        ["❓ Частые вопросы", "📞 Контакты"],
        ["ℹ️ О нас"],
    ]
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    
    await update.message.reply_html(
        text=TEXTS["welcome"],
        reply_markup=reply_markup
    )

async def handle_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Отправить заявку'"""
    buttons = [
        [KeyboardButton("📍 Отправить геолокацию", request_location=True)],
        ["🏠 Ввести адрес вручную"],
        ["🔙 Назад"],
    ]
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    
    await update.message.reply_html(
        text=TEXTS["request"],
        reply_markup=reply_markup
    )
    return LOCATION

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик получения местоположения (геолокация или адрес)"""
    if update.message.location:
        # Если пользователь отправил геолокацию
        lat = update.message.location.latitude
        lon = update.message.location.longitude
        context.user_data["location"] = f"Геолокация: {lat},{lon}"
        logger.info(f"Получена геолокация: {lat},{lon}")
    else:
        # Если пользователь ввел адрес вручную
        context.user_data["location"] = f"Адрес: {update.message.text}"
        logger.info(f"Получен адрес: {update.message.text}")
    
    # Предлагаем отправить телефон
    buttons = [
        [KeyboardButton("📱 Отправить телефон", request_contact=True)],
        ["🔙 Назад"],
    ]
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    
    await update.message.reply_html(
        text=TEXTS["location_received"],
        reply_markup=reply_markup
    )
    return PHONE

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик получения телефона"""
    if update.message.contact:
        # Если пользователь отправил контакт
        phone = update.message.contact.phone_number
        logger.info(f"Получен контакт: {phone}")
    else:
        # Если пользователь ввел телефон вручную
        phone = update.message.text
        logger.info(f"Получен телефон: {phone}")
    
    # Сохраняем данные в Google Sheets
    try:
        append_to_sheet(
            address=context.user_data["location"],
            phone=phone
        )
        logger.info("Данные успешно сохранены в Google Sheets")
    except Exception as e:
        logger.error(f"Ошибка при сохранении в Google Sheets: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка при сохранении заявки. Пожалуйста, попробуйте позже.")
        return ConversationHandler.END
    
    # Отправляем подтверждение
    await update.message.reply_html(
        text=TEXTS["phone_received"],
        reply_markup=ReplyKeyboardMarkup([["🏠 Главное меню"]], resize_keyboard=True)
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена текущего действия и возврат в главное меню"""
    logger.info("Действие отменено пользователем")
    await update.message.reply_html(
        text=TEXTS["cancel"],
        reply_markup=ReplyKeyboardMarkup([["🏠 Главное меню"]], resize_keyboard=True)
    )
    return ConversationHandler.END

# =============================================
# ЗАПУСК БОТА
# =============================================

def run_client_bot(token: str):
    """Запуск клиентского бота"""
    try:
        logger.info("Запуск клиентского бота...")
        
        # Создаем приложение бота
        application = ApplicationBuilder().token(token).build()
        
        # Настройка ConversationHandler для обработки заявок
        conv_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^📨 Отправить заявку$"), handle_request)],
            states={
                LOCATION: [
                    MessageHandler(filters.LOCATION, handle_location),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_location)
                ],
                PHONE: [
                    MessageHandler(filters.CONTACT, handle_phone),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)
                ],
            },
            fallbacks=[MessageHandler(filters.Regex("^🔙 Назад$"), cancel)],
        )
        
        # Регистрируем обработчики
        application.add_handler(conv_handler)
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.Regex("^🏠 Главное меню$"), start))
        
        # Запускаем бота
        application.run_polling()
        logger.info("Бот успешно запущен")
        
    except Exception as e:
        logger.critical(f"Ошибка при запуске бота: {e}")
        raise