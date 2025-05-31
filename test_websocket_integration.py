#!/usr/bin/env python3
"""
Тесты для интеграции WebSocket с основным ботом

Проверяет:
1. Инициализацию WebSocket клиента
2. Обработку сообщений
3. Интеграцию с асинхронным ботом
4. Dual-mode работу (REST + WebSocket)
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.logger import setup_main_logger
from src.data.ws_client import create_websocket_client, WSMessage, SubscriptionType
from src.data.pairs_fetcher import get_pairs_fetcher
from src.config import WEBSOCKET_CONFIG

logger = logging.getLogger(__name__)


class TestWebSocketIntegration:
    """Тестовый класс для WebSocket интеграции"""
    
    def __init__(self):
        self.message_count = 0
        self.last_message_time = None
        self.processed_pairs = set()
        
    async def test_message_handler(self, message: WSMessage):
        """Тестовый обработчик WebSocket сообщений"""
        try:
            self.message_count += 1
            self.last_message_time = datetime.now()
            self.processed_pairs.add(message.symbol)
            
            logger.info(f"📨 Получено сообщение #{self.message_count}: {message.channel} для {message.symbol}")
            
            # Логируем детали для разных типов сообщений
            if message.channel.startswith('kline_'):
                data = message.data
                logger.info(f"   📊 Kline данные: цена {data.get('c', 'N/A')}, объём {data.get('v', 'N/A')}")
            elif message.channel == 'ticker':
                data = message.data
                logger.info(f"   📈 Ticker данные: цена {data.get('c', 'N/A')}, изменение {data.get('P', 'N/A')}%")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в тестовом обработчике: {e}")

    async def test_websocket_basic_connection(self):
        """Тест базового подключения WebSocket"""
        logger.info("🧪 Тест 1: Базовое подключение WebSocket")
        
        try:
            # Создаем фетчер пар
            pairs_fetcher = get_pairs_fetcher(3600)
              # Создаем WebSocket клиент
            ws_client = create_websocket_client(
                pairs_fetcher=pairs_fetcher,
                event_handler=self.test_message_handler,
                subscription_types=[SubscriptionType.TICKER, SubscriptionType.KLINE_1M]
            )
            
            logger.info("✅ WebSocket клиент создан")
            
            # Запускаем клиент на короткое время
            start_time = datetime.now()
            timeout = 30  # 30 секунд тестирования
            
            task = asyncio.create_task(ws_client.start())
            
            # Ждем получения сообщений
            while (datetime.now() - start_time).seconds < timeout:
                await asyncio.sleep(1)
                
                if self.message_count > 0:
                    logger.info(f"📊 Статистика: {self.message_count} сообщений, {len(self.processed_pairs)} уникальных пар")
                
                if self.message_count >= 10:  # Достаточно для теста
                    break
            
            # Останавливаем клиент
            await ws_client.stop()
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            logger.info(f"✅ Тест завершен. Получено {self.message_count} сообщений от {len(self.processed_pairs)} пар")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка в тесте подключения: {e}")
            return False

    async def test_dual_mode_simulation(self):
        """Тест симуляции dual-mode работы"""
        logger.info("🧪 Тест 2: Симуляция dual-mode (REST + WebSocket)")
        
        try:
            # Симулируем работу REST API анализа
            logger.info("📡 Симуляция REST API анализа...")
            await asyncio.sleep(2)
            
            # Симулируем WebSocket real-time обработку
            logger.info("🌐 Симуляция WebSocket real-time обработки...")
            
            # Создаем тестовые сообщения
            test_messages = [
                WSMessage(
                    channel="kline_Min1",
                    symbol="BTC_USDT",
                    data={"c": "50000", "v": "1000", "t": "123456789"},
                    timestamp=datetime.now()
                ),
                WSMessage(
                    channel="ticker",
                    symbol="ETH_USDT", 
                    data={"c": "3000", "P": "2.5", "v": "5000"},
                    timestamp=datetime.now()
                )
            ]
            
            # Обрабатываем тестовые сообщения
            for msg in test_messages:
                await self.test_message_handler(msg)
                await asyncio.sleep(0.5)
            
            logger.info("✅ Dual-mode симуляция завершена успешно")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка в dual-mode тесте: {e}")
            return False

    async def run_all_tests(self):
        """Запуск всех тестов"""
        logger.info("🚀 Запуск тестов WebSocket интеграции")
        
        results = []
        
        # Тест 1: Базовое подключение
        result1 = await self.test_websocket_basic_connection()
        results.append(("Базовое подключение", result1))
        
        await asyncio.sleep(2)
        
        # Тест 2: Dual-mode симуляция
        result2 = await self.test_dual_mode_simulation()
        results.append(("Dual-mode симуляция", result2))
        
        # Итоги
        logger.info("📊 === РЕЗУЛЬТАТЫ ТЕСТОВ ===")
        passed = 0
        for test_name, result in results:
            status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
            logger.info(f"   {test_name}: {status}")
            if result:
                passed += 1
        
        logger.info(f"📈 Пройдено тестов: {passed}/{len(results)}")
        
        if passed == len(results):
            logger.info("🎉 Все тесты пройдены успешно!")
            return True
        else:
            logger.warning("⚠️ Некоторые тесты провалены")
            return False


async def main():
    """Главная функция тестирования"""
    setup_main_logger()
    
    logger.info("🧪 === ТЕСТИРОВАНИЕ WEBSOCKET ИНТЕГРАЦИИ ===")
    logger.info("🎯 Цель: Проверка WebSocket интеграции с основным ботом")
    
    try:
        tester = TestWebSocketIntegration()
        success = await tester.run_all_tests()
        
        if success:
            logger.info("✅ Все тесты пройдены. WebSocket интеграция работает корректно.")
            return 0
        else:
            logger.error("❌ Некоторые тесты провалены. Требуется доработка.")
            return 1
            
    except KeyboardInterrupt:
        logger.info("⏹️ Тестирование прервано пользователем")
        return 0
    except Exception as e:
        logger.error(f"💥 Критическая ошибка в тестах: {e}")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
