#!/usr/bin/env python3
"""
Быстрый тест интеграции главного бота с WebSocket
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.logger import setup_main_logger
from src.main import AsyncMexcAnalysisBot

logger = setup_main_logger()

async def test_main_bot_initialization():
    """Тест инициализации главного бота с WebSocket"""
    try:
        logger.info("🧪 Тест инициализации AsyncMexcAnalysisBot с WebSocket")
        
        # Создаем бота с WebSocket поддержкой
        bot = AsyncMexcAnalysisBot(
            timeframes=['Min1'],  # Только один таймфрейм для теста
            analysis_interval=300,  # 5 минут
            pairs_update_interval=3600,  # 1 час
            enable_websocket=True  # Включаем WebSocket
        )
        
        logger.info("✅ AsyncMexcAnalysisBot успешно инициализирован")
        
        # Тестируем инициализацию WebSocket клиента
        await bot._init_websocket_client()
        
        if bot.ws_client:
            logger.info("✅ WebSocket клиент успешно инициализирован")
        else:
            logger.warning("⚠️ WebSocket клиент не инициализирован")
        
        # Тестируем получение пар
        pairs = await bot.get_dynamic_pairs()
        logger.info(f"📊 Получено {len(pairs)} торговых пар")
        
        logger.info("✅ Основные компоненты бота работают корректно")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка в тесте инициализации: {e}")
        return False

async def test_websocket_message_handling():
    """Тест обработки WebSocket сообщений"""
    try:
        logger.info("🧪 Тест обработки WebSocket сообщений")
        
        from src.data.ws_client import WSMessage
        from datetime import datetime
        
        # Создаем бота
        bot = AsyncMexcAnalysisBot(enable_websocket=True)
        
        # Создаем тестовое сообщение
        test_message = WSMessage(
            channel="kline_Min1",
            symbol="BTC_USDT", 
            data={
                "c": "43500.0",  # close price
                "v": "1250.5",   # volume
                "t": "1699000000000"  # timestamp
            },
            timestamp=datetime.now()
        )
        
        # Тестируем обработку сообщения
        await bot._handle_websocket_message(test_message)
        
        logger.info("✅ WebSocket сообщение успешно обработано")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка в тесте обработки сообщений: {e}")
        return False

async def main():
    """Главная функция тестирования"""
    logger.info("🧪 === ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ ГЛАВНОГО БОТА ===")
    logger.info("🎯 Цель: Проверка работы AsyncMexcAnalysisBot с WebSocket")
    
    results = []
    
    # Тест 1: Инициализация бота
    result1 = await test_main_bot_initialization()
    results.append(("Инициализация бота", result1))
    
    await asyncio.sleep(1)
    
    # Тест 2: Обработка сообщений
    result2 = await test_websocket_message_handling()
    results.append(("Обработка WebSocket сообщений", result2))
    
    # Подведение итогов
    logger.info("📊 === РЕЗУЛЬТАТЫ ТЕСТОВ ИНТЕГРАЦИИ ===")
    passed = 0
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        logger.info(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"📈 Пройдено тестов: {passed}/{len(results)}")
    
    if passed == len(results):
        logger.info("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Интеграция работает корректно!")
        return 0
    else:
        logger.error("❌ Некоторые тесты провалены. Требуется доработка.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("⏹️ Тестирование прервано пользователем")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Критическая ошибка в тестах: {e}")
        sys.exit(1)
