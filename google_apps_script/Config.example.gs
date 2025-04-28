/**
 * Глобальная конфигурация проекта
 */

var CONFIG = {
  // Настройки таблицы
  SPREADSHEET_ID: 'YOUR_SPREADSHEET_ID',
  SHEET_NAME: 'Кадастровые заявки',
  
  // Безопасность
  SECRET_TOKEN: 'YOUR_SECRET_TOKEN',
  
  // Telegram
  BOT_TOKEN: 'YOUR_BOT_TOKEN',
  CHAT_ID: 'YOUR_CHAT_ID',
  
  // Колонки
  COLUMNS: {
    ID: 1,
    ADDRESS: 2,
    PHONE: 3,
    DATE: 4,
    STATUS: 5
  },
  
  // Статусы
  STATUSES: {
    NEW: 'Новая',
    PROCESSED: 'Обработана',
    CALLED: 'Прозвонен',
    ERROR: 'Ошибка'
  }
};