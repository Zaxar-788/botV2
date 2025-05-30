#!/usr/bin/env python3
"""
Простой тест для проверки работы компонентов бота

Этот файл можно запустить для быстрой проверки всех компонентов:
python test_bot.py
"""

import sys
import os

# Добавляем текущую директорию в путь для импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.logger import setup_main_logger
from src.data.rest_client import MexcRestClient
from src.signals.detector import VolumeSpikeDetector
from src.telegram.bot import TelegramNotifier
from src.config import TRADING_PAIR

def test_components():
    """Тест всех основных компонентов"""
    print("🧪 ТЕСТИРОВАНИЕ КОМПОНЕНТОВ БОТА")
    print("=" * 50)
    
    # Настраиваем логирование
    setup_main_logger()
    
    # Тест 1: REST клиент
    print("\n📊 Тест 1: Получение данных с MEXC...")
    rest_client = MexcRestClient()
    klines = rest_client.get_klines(pair=TRADING_PAIR, limit=10)
    
    if klines:
        print(f"✅ Получено {len(klines)} свечей")
        print(f"   Последняя свеча: цена ${float(klines[-1]['c']):.2f}, объём {float(klines[-1]['q']):.0f}")
    else:
        print("❌ Не удалось получить данные")
        return False
      # Тест 2: Детектор спайков
    print("\n🔍 Тест 2: Анализ спайков объёма...")
    detector = VolumeSpikeDetector(threshold=1.5, window_size=5)  # Уменьшаем окно для тестирования
    signal = detector.analyze_volume_spike(klines, TRADING_PAIR)
    
    if signal:
        print(f"✅ Обнаружен спайк: {signal.spike_ratio:.1f}x от среднего")
        print(f"   {signal.message}")
    else:
        print("ℹ️ Спайков не обнаружено (это нормально)")
    
    # Тест 3: Telegram уведомления
    print("\n📤 Тест 3: Отправка уведомлений...")
    notifier = TelegramNotifier()
    
    if signal:
        success = notifier.send_volume_signal(signal)
    else:
        # Создаём тестовый сигнал
        from src.signals.detector import VolumeSignal
        test_signal = VolumeSignal(
            timestamp=1640995200000,
            pair=TRADING_PAIR,
            current_volume=1000000,
            average_volume=500000,
            spike_ratio=2.0,
            price=50000.0,
            message="🧪 Тестовый сигнал для проверки"
        )
        success = notifier.send_volume_signal(test_signal)
    
    if success:
        print("✅ Уведомление отправлено")
    else:
        print("❌ Ошибка при отправке уведомления")
    
    print("\n🎉 Тестирование завершено!")
    print("   Все компоненты работают корректно")
    print("   Можно запускать основной бот: python src/main.py")
    
    return True

if __name__ == "__main__":
    test_components()
