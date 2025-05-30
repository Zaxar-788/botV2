#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Демонстрация отправки профессиональных торговых сигналов в Telegram
Примеры использования функции send_professional_signal
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.telegram.bot import TelegramNotifier
from src.utils.logger import setup_logger

# Настройка логгера
logger = setup_logger("telegram_demo")

def demo_professional_signals():
    """Демонстрация отправки различных типов профессиональных сигналов"""
    
    # Инициализируем уведомитель
    notifier = TelegramNotifier()
    
    # ВАЖНО: Для реальной отправки замените на ваши реальные данные
    DEMO_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
    DEMO_CHAT_ID = "YOUR_CHAT_ID_HERE"
    
    print("🚀 Демонстрация профессиональных Telegram сигналов\n")
    
    # Пример 1: PUMP сигнал
    print("📤 Отправляем PUMP сигнал...")
    success = notifier.send_professional_signal(
        token=DEMO_BOT_TOKEN,
        chat_id=DEMO_CHAT_ID,
        coin="BTC_USDT",
        timeframe="1m",
        signal_type="pump",
        price=45250.75,
        volume=1250000,
        oi=875000000,
        change_percent=8.45,
        comment="Мощный прорыв уровня сопротивления с высоким объёмом!"
    )
    logger.info(f"PUMP сигнал отправлен: {'✅' if success else '❌'}")
    
    # Пример 2: DUMP сигнал  
    print("📤 Отправляем DUMP сигнал...")
    success = notifier.send_professional_signal(
        token=DEMO_BOT_TOKEN,
        chat_id=DEMO_CHAT_ID,
        coin="ETH_USDT", 
        timeframe="5m",
        signal_type="dump",
        price=3180.25,
        volume=980000,
        oi=420000000,
        change_percent=-6.78,
        comment="Пробой поддержки, возможно дальнейшее снижение"
    )
    logger.info(f"DUMP сигнал отправлен: {'✅' if success else '❌'}")
    
    # Пример 3: LONG сигнал
    print("📤 Отправляем LONG сигнал...")
    success = notifier.send_professional_signal(
        token=DEMO_BOT_TOKEN,
        chat_id=DEMO_CHAT_ID,
        coin="SOL_USDT",
        timeframe="15m", 
        signal_type="long",
        price=125.68,
        volume=750000,
        oi=180000000,
        change_percent=3.22,
        coin_url="https://futures.mexc.com/exchange/SOL_USDT",
        comment="Отскок от ключевой поддержки, хорошая точка входа в лонг"
    )
    logger.info(f"LONG сигнал отправлен: {'✅' if success else '❌'}")
    
    # Пример 4: SHORT сигнал
    print("📤 Отправляем SHORT сигнал...")
    success = notifier.send_professional_signal(
        token=DEMO_BOT_TOKEN,
        chat_id=DEMO_CHAT_ID,
        coin="BNB_USDT",
        timeframe="1h",
        signal_type="short", 
        price=315.45,
        volume=425000,
        change_percent=-2.15,
        comment="Формирование медвежьего паттерна, рассмотреть шорт позицию"
    )
    logger.info(f"SHORT сигнал отправлен: {'✅' if success else '❌'}")
    
    # Пример 5: ALERT сигнал
    print("📤 Отправляем ALERT сигнал...")
    success = notifier.send_professional_signal(
        token=DEMO_BOT_TOKEN,
        chat_id=DEMO_CHAT_ID,
        coin="ADA_USDT",
        timeframe="5m",
        signal_type="alert",
        price=0.4825,
        volume=2100000,
        oi=95000000,
        change_percent=1.08,
        comment="Необычная активность, следите за развитием ситуации"
    )
    logger.info(f"ALERT сигнал отправлен: {'✅' if success else '❌'}")
    
    # Пример 6: Минимальный сигнал (только обязательные параметры)
    print("📤 Отправляем минимальный сигнал...")
    success = notifier.send_professional_signal(
        token=DEMO_BOT_TOKEN,
        chat_id=DEMO_CHAT_ID,
        coin="DOGE_USDT",
        timeframe="1m",
        signal_type="pump",
        price=0.08756,
        volume=5600000
    )
    logger.info(f"Минимальный сигнал отправлен: {'✅' if success else '❌'}")


def demo_integration_example():
    """Пример интеграции с детектором сигналов"""
    
    print("\n🔧 Пример интеграции с реальными данными")
    
    # Имитируем данные от детектора аномалий
    detected_data = {
        'pair': 'BTC_USDT',
        'timeframe': '1m',
        'price': 45678.90,
        'volume': 1850000,
        'volume_spike_ratio': 3.5,
        'oi_change': 2.1,
        'price_change_percent': 4.2
    }
    
    notifier = TelegramNotifier()
    
    # Определяем тип сигнала на основе данных
    if detected_data['price_change_percent'] > 3:
        signal_type = "pump"
    elif detected_data['price_change_percent'] < -3:
        signal_type = "dump"
    else:
        signal_type = "alert"
    
    # Формируем комментарий на основе аналитики
    comment = f"Спайк объёма в {detected_data['volume_spike_ratio']:.1f}x раз от среднего. "
    comment += f"OI изменился на {detected_data['oi_change']:+.1f}%"
    
    # Отправляем сигнал
    success = notifier.send_professional_signal(
        token="YOUR_BOT_TOKEN_HERE",
        chat_id="YOUR_CHAT_ID_HERE",
        coin=detected_data['pair'],
        timeframe=detected_data['timeframe'],
        signal_type=signal_type,
        price=detected_data['price'],
        volume=detected_data['volume'],
        change_percent=detected_data['price_change_percent'],
        comment=comment
    )
    
    logger.info(f"Интегрированный сигнал отправлен: {'✅' if success else '❌'}")


if __name__ == "__main__":
    print("🤖 Демонстрация профессиональных Telegram уведомлений MEXC Bot")
    print("=" * 70)
    
    print("\n⚠️  ВНИМАНИЕ: Для реальной отправки замените YOUR_BOT_TOKEN_HERE и YOUR_CHAT_ID_HERE")
    print("    на ваши реальные данные в коде выше\n")
    
    # Запускаем демонстрацию
    demo_professional_signals()
    demo_integration_example()
    
    print("\n✅ Демонстрация завершена!")
    print("📖 Проверьте логи для деталей отправки")
