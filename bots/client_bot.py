import json
import logging
from telegram import (
    ReplyKeyboardRemove,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    Updater,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler
)
import os
from dotenv import load_dotenv
from gsheets import append_to_sheet, get_worksheet
from datetime import datetime
import pytz

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для конечного автомата
(
    SEND_LOCATION,
    SEND_PHONE,
    FAQ,
    CONTACTS,
    ABOUT
) = range(5)

# Кэш частых вопросов
faq_cache = None

def start(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start"""
    keyboard = [
        [
            InlineKeyboardButton("📍 Отправить заявку", callback_data='send_request'),
            InlineKeyboardButton("❓ Частые вопросы", callback_data='faq')
        ],
        [
            InlineKeyboardButton("📌 Контакты", callback_data='contacts'),
            InlineKeyboardButton("ℹ️ О нас", callback_data='about')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        "👋 Добро пожаловать в бот для геодезических работ!\n"
        "Выберите нужный вариант:",
        reply_markup=reply_markup
    )

def button_handler(update: Update, context: CallbackContext) -> None:
    """Обработчик inline кнопок"""
    query = update.callback_query
    query.answer()

    if query.data == 'send_request':
        request_menu(update, context)
    elif query.data == 'faq':
        show_faq_menu(update, context)
    elif query.data == 'contacts':
        show_contacts(update, context)
    elif query.data == 'about':
        show_about(update, context)
    elif query.data.startswith('faq_'):
        show_faq_answer(update, context)

def request_menu(update: Update, context: CallbackContext) -> None:
    """Меню отправки заявки"""
    keyboard = [
        [
            KeyboardButton("📍 Отправить геолокацию", request_location=True),
            KeyboardButton("📝 Ввести адрес вручную")
        ],
        [KeyboardButton("📞 Отправить телефон", request_contact=True)],
        [KeyboardButton("🔙 Назад")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    query = update.callback_query
    if query:
        query.edit_message_text(
            text="📋 Для оформления заявки нам потребуется:\n"
                 "1. Местоположение объекта (геолокация или адрес)\n"
                 "2. Ваш контактный телефон\n\n"
                 "Выберите действие:",
            reply_markup=reply_markup
        )
    else:
        update.message.reply_text(
            "📋 Для оформления заявки нам потребуется:\n"
            "1. Местоположение объекта (геолокация или адрес)\n"
            "2. Ваш контактный телефон\n\n"
            "Выберите действие:",
            reply_markup=reply_markup
        )
    
    return SEND_LOCATION

def handle_location(update: Update, context: CallbackContext) -> None:
    """Обработчик геолокации"""
    location = update.message.location
    context.user_data['location'] = f"{location.latitude},{location.longitude}"
    
    update.message.reply_text(
        "✅ Геолокация получена! Теперь отправьте ваш телефон "
        "или нажмите кнопку ниже.",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📞 Отправить телефон", request_contact=True)]],
            resize_keyboard=True
        )
    )
    
    return SEND_PHONE

def handle_address(update: Update, context: CallbackContext) -> None:
    """Обработчик ручного ввода адреса"""
    address = update.message.text
    context.user_data['address'] = address
    
    update.message.reply_text(
        "✅ Адрес сохранен! Теперь отправьте ваш телефон "
        "или нажмите кнопку ниже.",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📞 Отправить телефон", request_contact=True)]],
            resize_keyboard=True
        )
    )
    
    return SEND_PHONE

def handle_phone(update: Update, context: CallbackContext) -> None:
    """Обработчик телефона"""
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text
    
    context.user_data['phone'] = phone
    
    # Получаем адрес/геолокацию
    location = context.user_data.get('location', context.user_data.get('address', 'Не указано'))
    
    # Подготавливаем данные для Google Sheets
    data = [
        str(update.effective_user.id),
        location,
        phone,
        datetime.now(pytz.timezone('Europe/Moscow')).strftime('%Y-%m-%d %H:%M:%S'),
        "Новая"
    ]
    
    try:
        append_to_sheet(data)
        update.message.reply_text(
            "✅ Ваша заявка успешно отправлена!\n"
            "Мы свяжемся с вами в ближайшее время.",
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception as e:
        logger.error(f"Error saving to Google Sheets: {e}")
        update.message.reply_text(
            "⚠️ Произошла ошибка при отправке заявки. Пожалуйста, попробуйте позже."
        )
    
    # Возвращаемся в главное меню
    start(update, context)
    return ConversationHandler.END

def load_faq():
    """Загрузка FAQ из файла с кэшированием"""
    global faq_cache
    if faq_cache is None:
        try:
            with open('data/faq.json', 'r', encoding='utf-8') as f:
                faq_cache = json.load(f)
        except Exception as e:
            logger.error(f"Error loading FAQ: {e}")
            faq_cache = {}
    return faq_cache

def show_faq_menu(update: Update, context: CallbackContext) -> None:
    """Показать меню FAQ"""
    faq = load_faq()
    keyboard = [
        [InlineKeyboardButton(q, callback_data=f'faq_{i}')]
        for i, q in enumerate(faq.keys())
    ]
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='back')])
    
    query = update.callback_query
    if query:
        query.edit_message_text(
            text="❓ Выберите интересующий вопрос:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        update.message.reply_text(
            text="❓ Выберите интересующий вопрос:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

def show_faq_answer(update: Update, context: CallbackContext) -> None:
    """Показать ответ на вопрос FAQ"""
    query = update.callback_query
    faq_id = int(query.data.split('_')[1])
    faq = load_faq()
    
    questions = list(faq.keys())
    if 0 <= faq_id < len(questions):
        question = questions[faq_id]
        answer = faq[question]
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='faq')]]
        query.edit_message_text(
            text=f"❓ <b>{question}</b>\n\n{answer}",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

def show_contacts(update: Update, context: CallbackContext) -> None:
    """Показать контакты"""
    contacts_text = (
        "📌 <b>Наши контакты:</b>\n\n"
        "📍 Адрес: г. Москва, ул. Геодезическая, д. 42\n"
        "📞 Телефон: +7 (495) 123-45-67\n"
        "📧 Email: geodetic@example.com\n\n"
        "⏰ Часы работы: Пн-Пт с 9:00 до 18:00"
    )
    
    query = update.callback_query
    if query:
        query.edit_message_text(
            text=contacts_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Назад", callback_data='back')]]
            )
        )
    else:
        update.message.reply_text(
            text=contacts_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Назад", callback_data='back')]]
            )
        )

def show_about(update: Update, context: CallbackContext) -> None:
    """Показать информацию о компании"""
    about_text = (
        "ℹ️ <b>О нашей компании:</b>\n\n"
        "Мы занимаемся полным комплексом геодезических работ:\n"
        "- Межевание земельных участков\n"
        "- Кадастровые работы\n"
        "- Топографическая съемка\n"
        "- Вынос границ в натуру\n\n"
        "Опыт работы более 10 лет!"
    )
    
    query = update.callback_query
    if query:
        query.edit_message_text(
            text=about_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Назад", callback_data='back')]]
            )
        )
    else:
        update.message.reply_text(
            text=about_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Назад", callback_data='back')]]
            )
        )

def cancel(update: Update, context: CallbackContext) -> None:
    """Отмена текущего действия"""
    update.message.reply_text(
        'Действие отменено.',
        reply_markup=ReplyKeyboardRemove()
    )
    start(update, context)
    return ConversationHandler.END

def error_handler(update: Update, context: CallbackContext) -> None:
    """Обработчик ошибок"""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    try:
        update.message.reply_text(
            '⚠️ Произошла ошибка. Пожалуйста, попробуйте позже.'
        )
    except:
        pass

def main() -> None:
    """Запуск бота"""
    load_dotenv()
    updater = Updater(os.getenv('CLIENT_BOT_TOKEN'))
    
    dp = updater.dispatcher
    
    # Обработчики команд
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('cancel', cancel))
    
    # Обработчики кнопок
    dp.add_handler(CallbackQueryHandler(button_handler))
    
    # Обработчики сообщений
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(request_menu, pattern='^send_request$')],
        states={
            SEND_LOCATION: [
                MessageHandler(Filters.location, handle_location),
                MessageHandler(Filters.text & ~Filters.command, handle_address)
            ],
            SEND_PHONE: [
                MessageHandler(Filters.contact | Filters.text & ~Filters.command, handle_phone)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(conv_handler)
    
    # Обработчик ошибок
    dp.add_error_handler(error_handler)
    
    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()