"""
🛠 АДМИНИСТРАТИВНЫЙ БОТ ДЛЯ УПРАВЛЕНИЯ ЗАЯВКАМИ

▌ Основной функционал:
├── 📊 Просмотр новых заявок
├── ✏️ Изменение статусов
├── 📞 Быстрый контакт с клиентом
└── 📊 Статистика обработки

▌ Особенности реализации:
✔ Поддержка python-telegram-bot 20.x
✔ Интеграция с Google Sheets
✔ Логирование всех действий
✔ Гибкая система команд
"""

import logging
import pytz
from datetime import datetime
from typing import Dict, Any

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton
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
# ⚙️ НАСТРОЙКИ СИСТЕМЫ
# ====================

# Логирование
logging.basicConfig(
    format='🛠 [%(asctime)s] %(levelname)s - %(name)s: %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('admin_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Временная зона
MOSCOW_TZ = pytz.timezone('Europe/Moscow')

# ====================
# 🗂 КОНСТАНТЫ И ТЕКСТЫ
# ====================

# Статусы заявок
STATUSES = {
    'new': '🆕 Новая',
    'in_progress': '🔄 В работе',
    'completed': '✅ Завершена'
}

# Текстовые шаблоны
TEXTS = {
    'welcome': 
        """
        🛠 <b>АДМИНИСТРАТИВНАЯ ПАНЕЛЬ</b>

        Выберите действие:
        """,
    
    'request_details': 
        """
        📋 <b>ЗАЯВКА #{id}</b>
        
        📍 Адрес: {address}
        📞 Телефон: {phone}
        📅 Дата: {date}
        🏷 Статус: {status}
        """
}

# ====================
# 🖥 ОСНОВНЫЕ ФУНКЦИИ
# ====================

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает главное меню администратора"""
    buttons = [
        ["🆕 Новые заявки"],
        ["📊 Статистика"],
        ["⚙️ Настройки"]
    ]
    
    await update.message.reply_text(
        text=TEXTS['welcome'],
        reply_markup=ReplyKeyboardMarkup(
            buttons,
            resize_keyboard=True,
            input_field_placeholder="Выберите действие..."
        ),
        parse_mode='HTML'
    )

async def show_new_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отображает список новых заявок"""
    try:
        worksheet = get_worksheet()
        records = worksheet.get_all_records()
        new_requests = [r for r in records if r['Статус'] == 'Новая']
        
        if not new_requests:
            await update.message.reply_text("📭 Нет новых заявок")
            return
        
        for request in new_requests:
            keyboard = [
                [
                    InlineKeyboardButton("📞 Позвонить", callback_data=f"call_{request['Телефон']}"),
                    InlineKeyboardButton("🔄 В работу", callback_data=f"progress_{request['ID']}")
                ],
                [
                    InlineKeyboardButton("✅ Завершить", callback_data=f"complete_{request['ID']}")
                ]
            ]
            
            await update.message.reply_text(
                text=TEXTS['request_details'].format(
                    id=request['ID'],
                    address=request['Адрес'],
                    phone=request['Телефон'],
                    date=request['Дата'],
                    status=STATUSES['new']
                ),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            
    except Exception as e:
        logger.error(f"Ошибка при загрузке заявок: {e}")
        await update.message.reply_text("⚠️ Ошибка загрузки данных")

async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия inline-кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('call_'):
        phone = query.data.split('_')[1]
        await query.edit_message_text(f"📞 Наберите номер: {phone}")
        
    elif query.data.startswith('progress_'):
        request_id = query.data.split('_')[1]
        await _update_request_status(request_id, 'in_progress', query)
        
    elif query.data.startswith('complete_'):
        request_id = query.data.split('_')[1]
        await _update_request_status(request_id, 'completed', query)

async def _update_request_status(request_id: str, status: str, query):
    """Обновляет статус заявки в таблице"""
    try:
        worksheet = get_worksheet()
        cell = worksheet.find(request_id)
        worksheet.update_cell(cell.row, 5, STATUSES[status])
        
        await query.edit_message_text(
            text=f"🔄 Статус заявки #{request_id} изменен на '{STATUSES[status]}'"
        )
        logger.info(f"Обновлен статус заявки #{request_id}")
        
    except Exception as e:
        logger.error(f"Ошибка обновления статуса: {e}")
        await query.edit_message_text("⚠️ Ошибка обновления статуса")

# ====================
# 🚀 ЗАПУСК БОТА
# ====================

def run_admin_bot(token: str):
    """Запускает административного бота"""
    try:
        logger.info("🔄 Инициализация админского бота...")
        
        application = Application.builder().token(token).build()
        
        # Регистрация обработчиков
        application.add_handler(CommandHandler("start", show_main_menu))
        application.add_handler(MessageHandler(filters.Regex("^🆕 Новые заявки$"), show_new_requests))
        application.add_handler(CallbackQueryHandler(handle_button_click))
        
        logger.info("🤖 Админский бот запущен и готов к работе")
        application.run_polling()
        
    except Exception as e:
        logger.critical(f"💥 Критическая ошибка: {e}")
        raise