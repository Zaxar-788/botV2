#!/usr/bin/env python3
"""
Полный пример использования профессиональной функции отправки сигналов в Telegram
Демонстрирует все возможности и типы сигналов для реального использования
"""

import sys
import os

# Добавляем путь к модулям проекта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.telegram.bot import TelegramNotifier
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from src.utils.logger import setup_logger

def show_usage_examples():
    """Демонстрация всех возможностей функции send_professional_signal"""
    
    logger = setup_logger("telegram_examples")
    
    print("📚 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ПРОФЕССИОНАЛЬНОЙ ФУНКЦИИ ОТПРАВКИ СИГНАЛОВ")
    print("=" * 80)
    
    # Создаем уведомитель
    notifier = TelegramNotifier()
    
    if not notifier.is_enabled:
        print("❌ Telegram уведомления не настроены!")
        print("💡 Убедитесь, что в .env файле указаны TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID")
        return
    
    print("✅ TelegramNotifier готов к работе")
    print()
    
    # Пример 1: Минимальный вызов
    print("📝 Пример 1: Минимальный вызов (только обязательные параметры)")
    print("-" * 60)
    print("notifier.send_professional_signal(")
    print("    token=TELEGRAM_BOT_TOKEN,")
    print("    chat_id=TELEGRAM_CHAT_ID,")
    print("    coin='BTC_USDT',")
    print("    timeframe='1m',")
    print("    signal_type='alert',")
    print("    price=67000.0,")
    print("    volume=500000")
    print(")")
    print()
    
    # Пример 2: Полный вызов pump сигнала
    print("📝 Пример 2: Полный PUMP сигнал с всеми параметрами")
    print("-" * 60)
    print("notifier.send_professional_signal(")
    print("    token=TELEGRAM_BOT_TOKEN,")
    print("    chat_id=TELEGRAM_CHAT_ID,")
    print("    coin='ETH_USDT',")
    print("    timeframe='5m',")
    print("    signal_type='pump',")
    print("    price=3456.78,")
    print("    volume=1_200_000,")
    print("    oi=450_000_000,")
    print("    change_percent=15.67,")
    print("    coin_url='https://futures.mexc.com/exchange/ETH_USDT',")
    print("    comment='Мощный пробой ключевого уровня сопротивления с рекордным объёмом'")
    print(")")
    print()
    
    # Пример 3: Dump сигнал с отрицательным изменением
    print("📝 Пример 3: DUMP сигнал с отрицательным изменением")
    print("-" * 60)
    print("notifier.send_professional_signal(")
    print("    token=TELEGRAM_BOT_TOKEN,")
    print("    chat_id=TELEGRAM_CHAT_ID,")
    print("    coin='SOL_USDT',")
    print("    timeframe='15m',")
    print("    signal_type='dump',")
    print("    price=145.23,")
    print("    volume=890_000,")
    print("    oi=125_000_000,")
    print("    change_percent=-12.34,")
    print("    comment='Резкое падение на фоне массовых продаж'")
    print(")")
    print()
    
    # Пример 4: Long сигнал
    print("📝 Пример 4: LONG сигнал для входа в позицию")
    print("-" * 60)
    print("notifier.send_professional_signal(")
    print("    token=TELEGRAM_BOT_TOKEN,")
    print("    chat_id=TELEGRAM_CHAT_ID,")
    print("    coin='BNB_USDT',")
    print("    timeframe='1h',")
    print("    signal_type='long',")
    print("    price=612.45,")
    print("    volume=567_000,")
    print("    change_percent=7.89")
    print(")")
    print()
    
    # Пример 5: Short сигнал
    print("📝 Пример 5: SHORT сигнал для входа в позицию")
    print("-" * 60)
    print("notifier.send_professional_signal(")
    print("    token=TELEGRAM_BOT_TOKEN,")
    print("    chat_id=TELEGRAM_CHAT_ID,")
    print("    coin='ADA_USDT',")
    print("    timeframe='30m',")
    print("    signal_type='short',")
    print("    price=0.5123,")
    print("    volume=2_100_000,")
    print("    change_percent=-5.43,")
    print("    comment='Медвежья дивергенция на RSI, рекомендуется шорт'")
    print(")")
    print()
    
    # Пример 6: Интеграция с детектором объёмов
    print("📝 Пример 6: Интеграция с детектором спайков объёма")
    print("-" * 60)
    print("# Использование в классе TelegramNotifier:")
    print("def send_volume_signal(self, signal: VolumeSignal) -> bool:")
    print("    # Определяем тип сигнала")
    print("    if signal.spike_ratio >= 5.0:")
    print("        signal_type = 'pump'")
    print("    elif signal.spike_ratio >= 3.0:")
    print("        signal_type = 'alert'")
    print("    else:")
    print("        signal_type = 'alert'")
    print("    ")
    print("    # Формируем комментарий")
    print("    comment = f'Спайк объёма {signal.spike_ratio:.1f}x'")
    print("    ")
    print("    # Отправляем сигнал")
    print("    return self.send_professional_signal(")
    print("        token=self.bot_token,")
    print("        chat_id=self.chat_id,")
    print("        coin=signal.pair,")
    print("        timeframe=signal.timeframe,")
    print("        signal_type=signal_type,")
    print("        price=signal.price,")
    print("        volume=signal.current_volume,")
    print("        comment=comment")
    print("    )")
    print()
    
    # Описание всех типов сигналов
    print("📊 ТИПЫ СИГНАЛОВ И ИХ EMOJI:")
    print("-" * 60)
    print("• 'pump'  → 🚀 ПАМП   (зелёная тема)")
    print("• 'dump'  → 💥 ДАМП   (красная тема)")
    print("• 'long'  → 🟢 ЛОНГ   (зелёная тема)")
    print("• 'short' → 🔴 ШОРТ   (красная тема)")
    print("• 'alert' → ⚡️ АЛЕРТ  (жёлтая тема)")
    print()
    
    print("🎯 ОСОБЕННОСТИ ФУНКЦИИ:")
    print("-" * 60)
    print("✅ Автоматическое форматирование чисел (запятые в больших числах)")
    print("✅ Кликабельные ссылки на монеты")
    print("✅ Inline-кнопка для быстрого перехода на MEXC")
    print("✅ HTML-разметка с жирным текстом и эмодзи")
    print("✅ Отключение превью ссылок")
    print("✅ Автоматическая временная метка")
    print("✅ Копируемый тег монеты")
    print("✅ Корректное логирование всех операций")
    print("✅ Обработка ошибок и timeout")
    print()
    
    print("🔒 БЕЗОПАСНОСТЬ:")
    print("-" * 60)
    print("✅ Токены хранятся в .env файле")
    print("✅ .env файл добавлен в .gitignore")
    print("✅ Валидация всех входных параметров")
    print("✅ Timeout для HTTP запросов (10 секунд)")
    print("✅ Обработка всех типов ошибок API")
    print()
    
    logger.info("Демонстрация примеров использования завершена")

if __name__ == "__main__":
    show_usage_examples()
