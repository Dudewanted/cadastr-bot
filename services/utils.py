import re
from services.logger import logger

class Validator:
    """Класс для валидации вводимых данных"""
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """
        Проверяет валидность номера телефона
        :param phone: Номер телефона для проверки
        :return: True если номер валиден, иначе False
        """
        if not phone:
            logger.warning("Пустой номер телефона")
            return False
            
        # Удаляем все нецифровые символы
        cleaned_phone = re.sub(r'\D', '', phone)
        
        # Проверяем длину номера (минимум 10 цифр)
        if len(cleaned_phone) < 10:
            logger.warning(f"Неверная длина номера: {phone}")
            return False
            
        return True
    
    @staticmethod
    def validate_address(address: str) -> bool:
        """
        Проверяет валидность адреса
        :param address: Адрес для проверки
        :return: True если адрес валиден, иначе False
        """
        if not address or len(address.strip()) < 5:
            logger.warning(f"Неверный адрес: {address}")
            return False
            
        return True
    
    @staticmethod
    def validate_location(lat: float, lon: float) -> bool:
        """
        Проверяет валидность географических координат
        :param lat: Широта
        :param lon: Долгота
        :return: True если координаты валидны, иначе False
        """
        try:
            lat = float(lat)
            lon = float(lon)
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                logger.warning(f"Координаты вне допустимого диапазона: {lat}, {lon}")
                return False
            return True
        except (ValueError, TypeError):
            logger.warning(f"Неверный формат координат: {lat}, {lon}")
            return False