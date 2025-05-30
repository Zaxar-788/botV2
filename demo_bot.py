#!/usr/bin/env python3
"""
Демонстрационный скрипт для показа работы бота в непрерывном режиме
Запускается на короткое время для демонстрации
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

def demo_continuous_mode():
    """Демонстрация работы бота в непрерывном режиме (3 итерации)"""
    print("🎬 ДЕМОНСТРАЦИЯ НЕПРЕРЫВНОГО РЕЖИМА АНАЛИЗА")
    print("=" * 60)
    print("⏱️  Будет выполнено 3 итерации с интервалом 10 секунд")
    print("🛑 Нажмите Ctrl+C для досрочной остановки")
    print("=" * 60)
    
    # Настраиваем логирование
    setup_main_logger()
    
    # Инициализируем компоненты
    rest_client = MexcRestClient()
    detector = VolumeSpikeDetector(threshold=1.3, window_size=8)  # Более чувствительные настройки для демо
    notifier = TelegramNotifier()
    
    import time
    
    try:
        for iteration in range(1, 4):  # 3 итерации
            print(f"\n🔄 === ИТЕРАЦИЯ {iteration}/3 ===")
            
            # Получаем данные
            print(f"📊 Получение данных для {TRADING_PAIR}...")
            klines = rest_client.get_klines(pair=TRADING_PAIR, limit=30)
            
            if klines:
                latest_price = klines[-1]['c']
                latest_volume = klines[-1]['q']
                print(f"✅ Получено {len(klines)} свечей")
                print(f"   📈 Текущая цена: ${latest_price:.2f}")
                print(f"   📊 Текущий объём: {latest_volume:.0f}")
                
                # Анализируем спайки
                print("🔍 Анализ спайков объёма...")
                signal = detector.analyze_volume_spike(klines, TRADING_PAIR)
                
                if signal:
                    print("🎯 СИГНАЛ ОБНАРУЖЕН!")
                    notifier.send_volume_signal(signal)
                else:
                    print("✅ Аномалий не обнаружено")
            else:
                print("❌ Не удалось получить данные")
            
            # Ждём до следующей итерации (кроме последней)
            if iteration < 3:
                print(f"😴 Ожидание 10 секунд до следующей проверки...")
                time.sleep(10)
        
        print("\n🏁 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
        print("   💡 Для реального использования запустите: python run_bot.py")
        
    except KeyboardInterrupt:
        print("\n⏹️  Демонстрация остановлена пользователем")
    except Exception as e:
        print(f"\n💥 Ошибка: {e}")

if __name__ == "__main__":
    demo_continuous_mode()
