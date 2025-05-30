#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Демонстрация мультипарного бота MEXC Futures с анализом множественных таймфреймов
Показывает возможности анализа нескольких торговых пар одновременно
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import MexcAnalysisBot
from src.utils.logger import setup_logger

def main():
    """Демонстрация мультипарного анализа"""
    
    print("🎯 Демонстрация мультипарного бота MEXC Futures")
    print("=" * 60)
    
    # Настройка логирования
    logger = setup_logger(__name__)
    
    print("\n📊 Конфигурация:")
    print("   • Торговые пары: BTC_USDT, ETH_USDT, BNB_USDT, ADA_USDT, SOL_USDT")
    print("   • Таймфреймы: Min1, Min5, Min15, Min60")
    print("   • Общий анализов: 5 пар × 4 таймфрейма = 20 комбинаций")
    
    try:
        # Создаем бота с полной конфигурацией
        logger.info("🚀 Инициализация мультипарного бота...")
        bot = MexcAnalysisBot()
        
        print("\n🔄 Запуск анализа...")
        print("   Это может занять несколько секунд...")
        
        # Запускаем одиночный анализ всех пар/таймфреймов
        bot.run_single_analysis()
        
        print("\n✅ Демонстрация завершена!")
        print("=" * 60)
        print("🎉 Мультипарный бот готов к продуктивному использованию!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Демонстрация прервана пользователем")
    except Exception as e:
        logger.error(f"Ошибка во время демонстрации: {e}")
        print(f"\n❌ Ошибка: {e}")
    
    print("\n📚 Для запуска непрерывного анализа используйте:")
    print("   python run_bot.py")

if __name__ == "__main__":
    main()
