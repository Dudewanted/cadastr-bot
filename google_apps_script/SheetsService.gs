/**
 * Сервис для работы с Google Sheets
 */

function getRowData(row) {
  const sheet = _getSheet();
  return {
    id: sheet.getRange(row, CONFIG.COLUMNS.ID).getValue(),
    address: sheet.getRange(row, CONFIG.COLUMNS.ADDRESS).getValue(),
    phone: _formatPhone(sheet.getRange(row, CONFIG.COLUMNS.PHONE).getValue()),
    date: sheet.getRange(row, CONFIG.COLUMNS.DATE).getValue()
  };
}

function updateStatus(row, status) {
  _getSheet().getRange(row, CONFIG.COLUMNS.STATUS).setValue(status);
}

function updateStatusByPhone(phone, status) {
  const data = _getSheet().getDataRange().getValues();
  const phoneCol = CONFIG.COLUMNS.PHONE - 1;
  
  for (let i = 1; i < data.length; i++) {
    if (_formatPhone(data[i][phoneCol]) === _formatPhone(phone)) {
      updateStatus(i + 1, status);
      return true;
    }
  }
  return false;
}

// Приватные функции
function _getSheet() {
  return SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID)
    .getSheetByName(CONFIG.SHEET_NAME);
}

function _formatPhone(phone) {
  return phone.toString().replace(/\D/g, '');
}