"""
Тестовый скрипт для проверки мультипарного бота
"""

import sys
import os

# Добавляем путь к проекту для импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.logger import setup_main_logger
from src.main import MexcAnalysisBot
import logging

def test_multiframe_bot():
    """
    Тестирование мультипарного бота с ограниченным набором пар и таймфреймов
    """
    # Настраиваем логирование
    setup_main_logger()
    logger = logging.getLogger(__name__)
    
    logger.info("🧪 Запуск тестирования мультипарного бота")
    
    # Тестируем с ограниченным набором для быстрой проверки
    test_pairs = ["BTC_USDT", "ETH_USDT"]
    test_timeframes = ["Min1", "Min5"]
    
    logger.info(f"📊 Тестовые пары: {test_pairs}")
    logger.info(f"⏰ Тестовые таймфреймы: {test_timeframes}")
    
    try:
        # Создаём бота с тестовыми настройками
        bot = MexcAnalysisBot(pairs=test_pairs, timeframes=test_timeframes)
        
        # Выполняем одиночный анализ
        signals = bot.run_single_analysis()
        
        logger.info(f"✅ Тест завершён успешно!")
        logger.info(f"📊 Проанализировано комбинаций: {len(test_pairs) * len(test_timeframes)}")
        logger.info(f"🎯 Найдено сигналов: {len(signals) if signals else 0}")
        
        # Выводим статистику
        bot._print_detailed_statistics()
        
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании: {e}")
        return False
    
    return True

def test_full_config_bot():
    """
    Тестирование бота с полным конфигом из config.py
    """
    logger = logging.getLogger(__name__)
    
    logger.info("🧪 Запуск тестирования с полным конфигом")
    
    try:
        # Создаём бота с дефолтными настройками из конфига
        bot = MexcAnalysisBot()
        
        # Выполняем одиночный анализ
        signals = bot.run_single_analysis()
        
        logger.info(f"✅ Полный тест завершён успешно!")
        logger.info(f"🎯 Найдено сигналов: {len(signals) if signals else 0}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при полном тестировании: {e}")
        return False

if __name__ == "__main__":
    print("🎯 Тестирование мультипарного бота MEXC Futures")
    print("=" * 60)
    
    # Сначала быстрый тест
    success1 = test_multiframe_bot()
    
    print("\n" + "=" * 60)
    
    # Затем полный тест
    success2 = test_full_config_bot()
    
    print("\n" + "=" * 60)
    print(f"📊 Результаты тестирования:")
    print(f"   • Быстрый тест: {'✅ ПРОШЁЛ' if success1 else '❌ ПРОВАЛЕН'}")
    print(f"   • Полный тест: {'✅ ПРОШЁЛ' if success2 else '❌ ПРОВАЛЕН'}")
    
    if success1 and success2:
        print("🎉 Все тесты прошли успешно! Мультипарный бот готов к работе.")
    else:
        print("⚠️ Некоторые тесты провалены. Требуется доработка.")
