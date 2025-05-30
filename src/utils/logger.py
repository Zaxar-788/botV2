"""
Система логирования для проекта анализа MEXC Futures
"""

import logging
import sys
from datetime import datetime
from src.config import LOG_LEVEL, LOG_FORMAT


def setup_logger(name: str = None, level: str = LOG_LEVEL) -> logging.Logger:
    """
    Настройка логгера для модуля
    
    Args:
        name (str): Имя логгера (обычно __name__ модуля)
        level (str): Уровень логирования (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    logger = logging.getLogger(name or __name__)
    
    # Если логгер уже настроен, возвращаем его
    if logger.handlers:
        return logger
    
    # Устанавливаем уровень логирования
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Создаём форматтер
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Создаём handler для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    
    # Добавляем handler к логгеру
    logger.addHandler(console_handler)
    
    return logger


def setup_main_logger() -> logging.Logger:
    """
    Настройка основного логгера приложения
    
    Returns:
        logging.Logger: Основной логгер
    """
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    
    # Очищаем существующие handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Создаём форматтер
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Консольный handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Файловый handler (опционально)
    try:
        file_handler = logging.FileHandler(f"bot_{datetime.now().strftime('%Y%m%d')}.log", encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Не удалось создать лог-файл: {e}")
    
    logger = logging.getLogger(__name__)
    logger.info("Система логирования инициализирована")
    
    return root_logger


# Глобальный логгер для быстрого использования
main_logger = setup_main_logger()
