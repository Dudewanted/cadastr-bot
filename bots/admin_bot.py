"""
🛠 АДМИНИСТРАТИВНЫЙ БОТ ДЛЯ УПРАВЛЕНИЯ ЗАЯВКАМИ

▌ Основной функционал:
├── 📋 Просмотр новых заявок
├── ✏️ Изменение статусов (Новая/В работе/Завершена)
├── 📞 Быстрый контакт с клиентом
└── 📊 Статистика обработки

▌ Особенности реализации:
✔ Полная интеграция с Google Sheets
✔ Интерактивные inline-кнопки
✔ Подробное логирование действий
✔ Поддержка временной зоны (Europe/Moscow)
"""

import logging
import sys
import pytz
from datetime import datetime
from typing import Dict, Any

# ====================
# ⚙️ НАСТРОЙКА СИСТЕМЫ
# ====================

# Конфигурация временной зоны
TIMEZONE = pytz.timezone('Europe/Moscow')

# Настройка логирования
logging.basicConfig(
    format='🛠 [%(asctime)s] %(name)s │ %(levelname)-8s │ %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('admin_bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ====================
# 📦 ИМПОРТ КОМПОНЕНТОВ
# ====================

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from services.gsheets import get_worksheet

# ====================
# 🏷 СИСТЕМА СТАТУСОВ
# ====================

STATUSES = {
    'new': {'text': '🆕 Новая', 'column': 'Статус'},
    'progress': {'text': '🔄 В работе', 'column': 'Статус'},
    'completed': {'text': '✅ Завершена', 'column': 'Статус'}
}

# ====================
# 📝 ТЕКСТОВЫЕ ШАБЛОНЫ
# ====================

TEXTS = {
    'welcome': 
        """
        🛠 <b>АДМИНИСТРАТИВНАЯ ПАНЕЛЬ</b>

        Выберите действие:
        """,
    
    'request': 
        """
        📋 <b>ЗАЯВКА #{id}</b>
        
        📍 Адрес: {address}
        📞 Телефон: <code>{phone}</code>
        📅 Дата: {date}
        🏷 Статус: {status}
        """,
    
    'no_requests': 
        "📭 Нет новых заявок",
    
    'status_updated':
        "🔄 Статус заявки #{id} изменен на: {status}"
}

# ====================
# 🖥 ОСНОВНЫЕ ОБРАБОТЧИКИ
# ====================

async def show_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает главное меню администратора"""
    menu_buttons = [
        ["🆕 Новые заявки"],
        ["📊 Статистика"],
        ["⚙️ Настройки"]
    ]
    
    await update.message.reply_text(
        text=TEXTS['welcome'],
        reply_markup=ReplyKeyboardMarkup(
            menu_buttons,
            resize_keyboard=True,
            input_field_placeholder="Выберите действие..."
        ),
        parse_mode='HTML'
    )

async def show_new_requests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отображает список новых заявок"""
    try:
        worksheet = get_worksheet()
        records = worksheet.get_all_records()
        new_requests = [r for r in records if r['Статус'] == STATUSES['new']['text']]
        
        if not new_requests:
            await update.message.reply_text(TEXTS['no_requests'])
            return
        
        for request in new_requests:
            keyboard = [
                [
                    InlineKeyboardButton(
                        "📞 Позвонить", 
                        callback_data=f"call_{request['Телефон']}"
                    ),
                    InlineKeyboardButton(
                        "🔄 В работу", 
                        callback_data=f"status_progress_{request['ID']}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "✅ Завершить", 
                        callback_data=f"status_completed_{request['ID']}"
                    )
                ]
            ]
            
            await update.message.reply_text(
                text=TEXTS['request'].format(
                    id=request['ID'],
                    address=request['Адрес'],
                    phone=request['Телефон'],
                    date=request['Дата'],
                    status=request['Статус']
                ),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            
    except Exception as e:
        logger.error(f"Ошибка загрузки заявок: {e}")
        await update.message.reply_text("⚠️ Ошибка загрузки данных")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает нажатия inline-кнопок"""
    query = update.callback_query
    await query.answer()
    
    try:
        if query.data.startswith('call_'):
            # Обработка кнопки звонка
            phone = query.data.split('_')[1]
            await query.edit_message_text(f"📞 Наберите номер: <code>{phone}</code>", parse_mode='HTML')
            
        elif query.data.startswith('status_'):
            # Обработка изменения статуса
            action, request_id = query.data.split('_')[1], query.data.split('_')[2]
            new_status = STATUSES[action]['text']
            
            # Обновляем статус в Google Sheets
            worksheet = get_worksheet()
            cell = worksheet.find(request_id)
            worksheet.update_cell(cell.row, 5, new_status)
            
            await query.edit_message_text(
                text=TEXTS['status_updated'].format(
                    id=request_id,
                    status=new_status
                )
            )
            logger.info(f"Обновлен статус заявки #{request_id} на '{new_status}'")
            
    except Exception as e:
        logger.error(f"Ошибка обработки callback: {e}")
        await query.edit_message_text("⚠️ Ошибка обработки запроса")

# ====================
# 📊 ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ
# ====================

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает статистику обработки заявок"""
    try:
        worksheet = get_worksheet()
        records = worksheet.get_all_records()
        
        stats = {
            'new': 0,
            'progress': 0,
            'completed': 0
        }
        
        for r in records:
            if STATUSES['new']['text'] in r['Статус']:
                stats['new'] += 1
            elif STATUSES['progress']['text'] in r['Статус']:
                stats['progress'] += 1
            elif STATUSES['completed']['text'] in r['Статус']:
                stats['completed'] += 1
                
        message = (
            "📊 <b>СТАТИСТИКА ОБРАБОТКИ</b>\n\n"
            f"🆕 Новые: {stats['new']}\n"
            f"🔄 В работе: {stats['progress']}\n"
            f"✅ Завершено: {stats['completed']}\n"
            f"📌 Всего: {len(records)}"
        )
        
        await update.message.reply_text(
            text=message,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Ошибка загрузки статистики: {e}")
        await update.message.reply_text("⚠️ Ошибка загрузки статистики")

# ====================
# 🚀 ЗАПУСК БОТА
# ====================

def run_admin_bot(token: str) -> None:
    """Запускает административного бота"""
    try:
        logger.info("Инициализация админ-панели...")
        
        application = Application.builder() \
            .token(token) \
            .build()
        
        # Регистрация обработчиков
        application.add_handler(CommandHandler("start", show_dashboard))
        application.add_handler(MessageHandler(filters.Regex("^🆕 Новые заявки$"), show_new_requests))
        application.add_handler(MessageHandler(filters.Regex("^📊 Статистика$"), show_stats))
        application.add_handler(CallbackQueryHandler(handle_callback))
        
        logger.info("Админ-панель запущена")
        application.run_polling()
        
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
        raise