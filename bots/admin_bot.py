import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    MessageHandler,
    Filters
)
import os
from dotenv import load_dotenv
from gsheets import get_worksheet
from datetime import datetime
import pytz

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для изменения статуса
WAITING_FOR_STATUS = 1

def start(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start для админа"""
    if str(update.effective_user.id) != os.getenv('ADMIN_CHAT_ID'):
        update.message.reply_text("⛔ Доступ запрещен")
        return
    
    keyboard = [
        [InlineKeyboardButton("🔄 Проверить новые заявки", callback_data='check_new')],
        [InlineKeyboardButton("📋 Все заявки", callback_data='list_all')]
    ]
    update.message.reply_text(
        "👨‍💻 Админ-панель управления заявками",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def button_handler(update: Update, context: CallbackContext) -> None:
    """Обработчик inline кнопок"""
    query = update.callback_query
    query.answer()
    
    if query.data == 'check_new':
        check_new_requests(update, context)
    elif query.data == 'list_all':
        list_all_requests(update, context)
    elif query.data.startswith('request_'):
        show_request_details(update, context)
    elif query.data.startswith('status_'):
        process_status_change(update, context)

def check_new_requests(update: Update, context: CallbackContext) -> None:
    """Проверить новые заявки"""
    try:
        worksheet = get_worksheet()
        records = worksheet.get_all_records()
        new_requests = [r for r in records if r['Статус'] == 'Новая']
        
        if not new_requests:
            update.callback_query.edit_message_text(
                text="🔄 Новых заявок нет.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 Назад", callback_data='back')]]
                )
            )
            return
        
        for request in new_requests:
            send_request_notification(update, context, request)
        
    except Exception as e:
        logger.error(f"Error checking new requests: {e}")
        update.callback_query.edit_message_text(
            text="⚠️ Произошла ошибка при проверке заявок.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Назад", callback_data='back')]]
            )
        )

def list_all_requests(update: Update, context: CallbackContext) -> None:
    """Список всех заявок"""
    try:
        worksheet = get_worksheet()
        records = worksheet.get_all_records()
        
        if not records:
            update.callback_query.edit_message_text(
                text="📋 Заявок пока нет.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 Назад", callback_data='back')]]
                )
            )
            return
        
        # Группируем по статусам
        status_groups = {}
        for request in records:
            status = request['Статус']
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(request)
        
        text = "📋 Все заявки:\n\n"
        for status, requests in status_groups.items():
            text += f"<b>{status}</b> ({len(requests)}):\n"
            for req in requests[:3]:  # Показываем только первые 3 для краткости
                text += f"- ID: {req['ID']}, 📞 {req['Телефон']}\n"
            if len(requests) > 3:
                text += f"... и еще {len(requests)-3}\n"
            text += "\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data='list_all')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back')]
        ]
        update.callback_query.edit_message_text(
            text=text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"Error listing requests: {e}")
        update.callback_query.edit_message_text(
            text="⚠️ Произошла ошибка при получении списка заявок.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Назад", callback_data='back')]]
            )
        )

def send_request_notification(update: Update, context: CallbackContext, request: dict) -> None:
    """Отправить уведомление о новой заявке"""
    # Формируем текст сообщения
    text = (
        f"🚀 <b>Новая заявка #{request['ID']}</b>\n\n"
        f"📍 <b>Адрес:</b> {request['Адрес']}\n"
        f"📞 <b>Телефон:</b> <a href='tel:{request['Телефон']}'>{request['Телефон']}</a>\n"
        f"📅 <b>Дата:</b> {request['Дата']}\n"
        f"🔄 <b>Статус:</b> {request['Статус']}\n\n"
        "Выберите действие:"
    )
    
    # Формируем клавиатуру
    keyboard = [
        [
            InlineKeyboardButton("📞 Позвонить", callback_data=f'call_{request["Телефон"]}'),
            InlineKeyboardButton("✏️ Изменить статус", callback_data=f'status_{request["ID"]}')
        ],
        [InlineKeyboardButton("📋 Все заявки", callback_data='list_all')]
    ]
    
    # Отправляем сообщение
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_request_details(update: Update, context: CallbackContext) -> None:
    """Показать детали заявки"""
    request_id = update.callback_query.data.split('_')[1]
    
    try:
        worksheet = get_worksheet()
        records = worksheet.get_all_records()
        request = next((r for r in records if str(r['ID']) == request_id), None)
        
        if not request:
            update.callback_query.edit_message_text(
                text="⚠️ Заявка не найдена.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 Назад", callback_data='list_all')]]
                )
            )
            return
        
        text = (
            f"📋 <b>Заявка #{request['ID']}</b>\n\n"
            f"📍 <b>Адрес:</b> {request['Адрес']}\n"
            f"📞 <b>Телефон:</b> <a href='tel:{request['Телефон']}'>{request['Телефон']}</a>\n"
            f"📅 <b>Дата:</b> {request['Дата']}\n"
            f"🔄 <b>Статус:</b> {request['Статус']}\n\n"
            "Выберите действие:"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("📞 Позвонить", callback_data=f'call_{request["Телефон"]}'),
                InlineKeyboardButton("✏️ Изменить статус", callback_data=f'status_{request["ID"]}')
            ],
            [InlineKeyboardButton("🔙 Назад", callback_data='list_all')]
        ]
        
        update.callback_query.edit_message_text(
            text=text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"Error showing request details: {e}")
        update.callback_query.edit_message_text(
            text="⚠️ Произошла ошибка при получении данных заявки.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Назад", callback_data='list_all')]]
            )
        )

def process_status_change(update: Update, context: CallbackContext) -> None:
    """Изменить статус заявки"""
    request_id = update.callback_query.data.split('_')[1]
    context.user_data['editing_request'] = request_id
    
    keyboard = [
        [
            InlineKeyboardButton("✅ В работе", callback_data='setstatus_В работе'),
            InlineKeyboardButton("✔️ Завершено", callback_data='setstatus_Завершено')
        ],
        [
            InlineKeyboardButton("❌ Отменено", callback_data='setstatus_Отменено'),
            InlineKeyboardButton("🔙 Назад", callback_data=f'request_{request_id}')
        ]
    ]
    
    update.callback_query.edit_message_text(
        text="Выберите новый статус для заявки:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def set_status(update: Update, context: CallbackContext) -> None:
    """Установить новый статус"""
    query = update.callback_query
    status = query.data.split('_')[1]
    request_id = context.user_data.get('editing_request')
    
    if not request_id:
        query.edit_message_text(
            text="⚠️ Не удалось определить заявку.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Назад", callback_data='list_all')]]
            )
        )
        return
    
    try:
        worksheet = get_worksheet()
        records = worksheet.get_all_records()
        row_num = next((i+2 for i, r in enumerate(records) if str(r['ID']) == request_id), None)
        
        if not row_num:
            query.edit_message_text(
                text="⚠️ Заявка не найдена.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 Назад", callback_data='list_all')]]
                )
            )
            return
        
        # Обновляем статус
        worksheet.update_cell(row_num, 5, status)
        
        query.edit_message_text(
            text=f"✅ Статус заявки #{request_id} изменен на: {status}",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Назад", callback_data=f'request_{request_id}')]]
            )
        )
        
    except Exception as e:
        logger.error(f"Error updating status: {e}")
        query.edit_message_text(
            text="⚠️ Произошла ошибка при изменении статуса.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Назад", callback_data=f'request_{request_id}')]]
            )
        )

def call_client(update: Update, context: CallbackContext) -> None:
    """Обработчик кнопки звонка"""
    phone = update.callback_query.data.split('_')[1]
    
    update.callback_query.edit_message_text(
        text=f"📞 Наберите номер: <code>{phone}</code>",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Назад", callback_data='list_all')]]
        )
    )

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
    """Запуск админ-бота"""
    load_dotenv()
    updater = Updater(os.getenv('ADMIN_BOT_TOKEN'))
    
    dp = updater.dispatcher
    
    # Обработчики команд
    dp.add_handler(CommandHandler('start', start))
    
    # Обработчики кнопок
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(CallbackQueryHandler(process_status_change, pattern='^status_'))
    dp.add_handler(CallbackQueryHandler(set_status, pattern='^setstatus_'))
    dp.add_handler(CallbackQueryHandler(call_client, pattern='^call_'))
    
    # Обработчик ошибок
    dp.add_error_handler(error_handler)
    
    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()