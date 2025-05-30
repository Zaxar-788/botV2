#!/usr/bin/env python3
"""
Тестирование реальной отправки сигналов в Telegram
Использует токены из .env файла для безопасности
"""

import sys
import os
from datetime import datetime

# Добавляем путь к модулям проекта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.telegram.bot import TelegramNotifier
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from src.utils.logger import setup_logger

def test_telegram_integration():
    """Тестирование интеграции с Telegram Bot API"""
    
    # Настройка логгера
    logger = setup_logger("telegram_test")
    
    print("🚀 Тестирование отправки профессиональных сигналов в Telegram")
    print("=" * 70)
    
    # Проверяем наличие токенов
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("❌ Токены Telegram не найдены в .env файле!")
        print("❌ Убедитесь, что .env файл содержит TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID")
        return False
    
    print(f"🔑 Токен найден: {TELEGRAM_BOT_TOKEN[:10]}...")
    print(f"💬 Chat ID: {TELEGRAM_CHAT_ID}")
    print()
    
    # Создаем notifier
    notifier = TelegramNotifier()
    
    if not notifier.is_enabled:
        logger.error("❌ Telegram уведомления не активированы!")
        return False
    
    print("✅ TelegramNotifier инициализирован")
    print()
    
    # Тест 1: Pump сигнал
    print("🚀 Тест 1: Отправка PUMP сигнала...")
    result1 = notifier.send_professional_signal(
        token=TELEGRAM_BOT_TOKEN,
        chat_id=TELEGRAM_CHAT_ID,
        coin="BTC_USDT",
        timeframe="1m",
        signal_type="pump",
        price=67432.50,
        volume=1_250_000,
        oi=850_000_000,
        change_percent=12.45,
        comment="Сильный пробой уровня сопротивления с высоким объёмом"
    )
    print(f"Результат: {'✅ Успешно' if result1 else '❌ Ошибка'}")
    print()
    
    # Тест 2: Dump сигнал
    print("💥 Тест 2: Отправка DUMP сигнала...")
    result2 = notifier.send_professional_signal(
        token=TELEGRAM_BOT_TOKEN,
        chat_id=TELEGRAM_CHAT_ID,
        coin="ETH_USDT",
        timeframe="5m",
        signal_type="dump",
        price=3456.78,
        volume=890_000,
        oi=420_000_000,
        change_percent=-8.92,
        comment="Резкое падение на фоне продаж крупных держателей"
    )
    print(f"Результат: {'✅ Успешно' if result2 else '❌ Ошибка'}")
    print()
    
    # Тест 3: Long сигнал
    print("🟢 Тест 3: Отправка LONG сигнала...")
    result3 = notifier.send_professional_signal(
        token=TELEGRAM_BOT_TOKEN,
        chat_id=TELEGRAM_CHAT_ID,
        coin="SOL_USDT",
        timeframe="15m",
        signal_type="long",
        price=156.89,
        volume=2_100_000,
        oi=125_000_000,
        change_percent=5.67
    )
    print(f"Результат: {'✅ Успешно' if result3 else '❌ Ошибка'}")
    print()
    
    # Тест 4: Alert сигнал
    print("⚡️ Тест 4: Отправка ALERT сигнала...")
    result4 = notifier.send_professional_signal(
        token=TELEGRAM_BOT_TOKEN,
        chat_id=TELEGRAM_CHAT_ID,
        coin="BNB_USDT",
        timeframe="1h",
        signal_type="alert",
        price=612.34,
        volume=567_000,
        comment="Необычная активность на рынке - следите за развитием"
    )
    print(f"Результат: {'✅ Успешно' if result4 else '❌ Ошибка'}")
    print()
    
    # Тест 5: Уведомление о запуске
    print("🤖 Тест 5: Отправка уведомления о запуске...")
    result5 = notifier.send_startup_notification()
    print(f"Результат: {'✅ Успешно' if result5 else '❌ Ошибка'}")
    print()
    
    # Подводим итоги
    successful_tests = sum([result1, result2, result3, result4, result5])
    total_tests = 5
    
    print("=" * 70)
    print(f"📊 ИТОГИ ТЕСТИРОВАНИЯ: {successful_tests}/{total_tests} тестов прошли успешно")
    
    if successful_tests == total_tests:
        print("🎉 Все тесты прошли успешно! Telegram интеграция работает корректно.")
        logger.info("Все тесты Telegram интеграции прошли успешно")
        return True
    else:
        print(f"⚠️  {total_tests - successful_tests} тестов завершились с ошибками")
        logger.warning(f"{total_tests - successful_tests} тестов Telegram завершились с ошибками")
        return False

if __name__ == "__main__":
    try:
        success = test_telegram_integration()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка при тестировании: {e}")
        sys.exit(1)
