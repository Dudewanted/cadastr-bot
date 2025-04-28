/**
 * Главный обработчик изменений в таблице и вебхуков
 */

// Импорт конфигурации (автоматически доступна через глобальную область)
function onEdit(e) {
  try {
    if (_isStatusColumn(e.range)) {
      const status = e.range.getValue();
      if (status === CONFIG.STATUSES.NEW) {
        _processNewRequest(e.range.getRow());
      }
    }
  } catch (error) {
    console.error("Ошибка в onEdit:", error);
  }
}

function doPost(e) {
  try {
    if (!_validateWebhook(e)) {
      return ContentService.createTextOutput("Unauthorized");
    }
    
    const update = JSON.parse(e.postData.contents);
    if (update.callback_query?.data.startsWith('called_')) {
      return _handleCallback(update.callback_query);
    }
    
    return ContentService.createTextOutput("OK");
  } catch (error) {
    console.error("Ошибка в doPost:", error);
    return ContentService.createTextOutput("Error");
  }
}

// Внутренние функции
function _processNewRequest(row) {
  const data = SheetsService.getRowData(row);
  TelegramAPI.sendNotification(data);
  SheetsService.updateStatus(row, CONFIG.STATUSES.PROCESSED);
}

function _handleCallback(callback) {
  const phone = callback.data.split('_')[1];
  SheetsService.updateStatusByPhone(phone, CONFIG.STATUSES.CALLED);
  return TelegramAPI.sendCallbackResponse(
    callback.id,
    `✅ Статус для ${phone} обновлен`
  );
}

function _isStatusColumn(range) {
  return range.getColumn() === CONFIG.COLUMNS.STATUS;
}

function _validateWebhook(e) {
  return e?.parameter?.token === CONFIG.SECRET_TOKEN;
}