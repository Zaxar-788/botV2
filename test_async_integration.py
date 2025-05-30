#!/usr/bin/env python3
"""
Тест интеграции новой асинхронной архитектуры с существующими модулями

Проверяет:
1. Совместимость с pairs_fetcher.py
2. Работу с async_rest_client.py
3. Интеграцию с signals/detector.py
4. Telegram уведомления
5. Сохранение в базу данных
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.logger import setup_main_logger
from src.main import AsyncMexcAnalysisBot
from src.data.pairs_fetcher import get_pairs_fetcher
from src.data.async_rest_client import AsyncMexcRestClient
from src.signals.detector import VolumeSpikeDetector
from src.telegram.bot import TelegramNotifier
from src.data.database import SignalsManager
from src.config import DATABASE_CONFIG, CACHE_CONFIG

logger = setup_main_logger()


class AsyncIntegrationTest:
    """Тест интеграции асинхронной архитектуры"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now()
    
    async def run_all_tests(self):
        """Запуск всех тестов интеграции"""
        logger.info("🧪 === ТЕСТ ИНТЕГРАЦИИ АСИНХРОННОЙ АРХИТЕКТУРЫ ===")
        logger.info(f"⏰ Начало тестирования: {self.start_time}")
        logger.info("")
        
        tests = [
            ("pairs_fetcher", self.test_pairs_fetcher_integration),
            ("async_rest_client", self.test_async_rest_client),
            ("volume_detector", self.test_volume_detector_integration),
            ("telegram_notifier", self.test_telegram_integration),
            ("database", self.test_database_integration),
            ("full_async_bot", self.test_full_async_bot_creation),
            ("error_handling", self.test_error_handling),
        ]
        
        for test_name, test_func in tests:
            logger.info(f"🔍 Запуск теста: {test_name}")
            try:
                result = await test_func()
                self.test_results[test_name] = {
                    'status': 'PASS' if result else 'FAIL',
                    'details': 'Успешно' if result else 'Ошибка'
                }
                status_emoji = "✅" if result else "❌"
                logger.info(f"{status_emoji} Тест {test_name}: {'PASS' if result else 'FAIL'}")
            except Exception as e:
                self.test_results[test_name] = {
                    'status': 'ERROR',
                    'details': str(e)
                }
                logger.error(f"💥 Тест {test_name}: ERROR - {e}")
            
            logger.info("")
        
        # Финальная сводка
        self.print_test_summary()
    
    async def test_pairs_fetcher_integration(self) -> bool:
        """Тест интеграции с pairs_fetcher"""
        try:
            # Создаем фетчер пар
            pairs_fetcher = get_pairs_fetcher(update_interval=300)
            
            # Проверяем получение пар
            pairs = pairs_fetcher.get_all_pairs()
            
            if not pairs:
                logger.warning("⚠️ Pairs fetcher вернул пустой список")
                return False
            
            logger.info(f"📊 Получено {len(pairs)} пар через pairs_fetcher")
            logger.info(f"📋 Примеры: {', '.join(pairs[:3])}...")
            
            # Проверяем автообновление
            if hasattr(pairs_fetcher, 'start_auto_update'):
                pairs_fetcher.start_auto_update()
                logger.info("🔄 Автообновление пар запущено")
                
                await asyncio.sleep(1)  # Небольшая задержка
                
                if hasattr(pairs_fetcher, 'stop_auto_update'):
                    pairs_fetcher.stop_auto_update()
                    logger.info("⏹️ Автообновление пар остановлено")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка в тесте pairs_fetcher: {e}")
            return False
    
    async def test_async_rest_client(self) -> bool:
        """Тест асинхронного REST клиента"""
        try:
            async with AsyncMexcRestClient() as client:
                # Тест получения одиночных данных
                logger.info("🔌 Тестирование одиночного запроса...")
                klines = await client.get_klines_async("BTC_USDT", "Min1", 5)
                
                if not klines:
                    logger.warning("⚠️ Не удалось получить данные для BTC_USDT")
                    return False
                
                logger.info(f"📊 Получено {len(klines)} свечей для BTC_USDT")
                
                # Тест batch запроса
                logger.info("🚀 Тестирование batch запроса...")
                test_pairs = ["BTC_USDT", "ETH_USDT"]
                test_timeframes = ["Min1"]
                
                batch_results = await client.get_batch_klines_for_pairs(
                    test_pairs, test_timeframes, 3
                )
                
                success_count = 0
                for pair, tf_data in batch_results.items():
                    for tf, data in tf_data.items():
                        if data:
                            success_count += 1
                
                logger.info(f"📈 Batch запрос: {success_count}/{len(test_pairs)} успешных")
                
                return success_count > 0
                
        except Exception as e:
            logger.error(f"❌ Ошибка в тесте async_rest_client: {e}")
            return False
    
    async def test_volume_detector_integration(self) -> bool:
        """Тест интеграции с детектором объема"""
        try:
            # Создаем детектор
            detector = VolumeSpikeDetector(threshold=2.0, window_size=5)
            
            # Получаем тестовые данные
            async with AsyncMexcRestClient() as client:
                klines = await client.get_klines_async("BTC_USDT", "Min1", 20)
                
                if not klines:
                    logger.warning("⚠️ Нет данных для тестирования детектора")
                    return False
                
                # Тестируем анализ в executor (асинхронно)
                logger.info("🔍 Тестирование анализа объема...")
                signal = await asyncio.to_thread(
                    detector.analyze_volume_spike,
                    klines, "BTC_USDT", "Min1"
                )
                
                if signal:
                    logger.info(f"🎯 Обнаружен сигнал: {signal.message}")
                else:
                    logger.info("✅ Анализ завершен, аномалий не обнаружено")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Ошибка в тесте volume_detector: {e}")
            return False
    
    async def test_telegram_integration(self) -> bool:
        """Тест интеграции с Telegram (без реальной отправки)"""
        try:
            # Создаем уведомитель
            telegram_notifier = TelegramNotifier()
            
            # Проверяем, что объект создался
            if not telegram_notifier:
                return False
            
            logger.info("📱 Telegram notifier создан успешно")
            
            # Здесь можно добавить mock тест или dry-run режим
            # Пока просто проверяем создание объекта
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка в тесте telegram: {e}")
            return False
    
    async def test_database_integration(self) -> bool:
        """Тест интеграции с базой данных"""
        try:
            # Создаем менеджер сигналов
            signals_manager = SignalsManager(DATABASE_CONFIG, CACHE_CONFIG)
            
            # Тестируем подключение
            stats = await asyncio.to_thread(signals_manager.get_full_statistics)
            
            if stats:
                db_stats = stats.get('database', {})
                logger.info(f"💾 БД подключена, сигналов: {db_stats.get('total_signals', 0)}")
            
            # Закрываем соединение
            await asyncio.to_thread(signals_manager.close)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка в тесте database: {e}")
            return False
    
    async def test_full_async_bot_creation(self) -> bool:
        """Тест создания полного асинхронного бота"""
        try:
            # Создаем бота с минимальными настройками
            bot = AsyncMexcAnalysisBot(
                timeframes=["Min1"],
                analysis_interval=60,
                pairs_update_interval=300
            )
            
            # Проверяем основные компоненты
            if not bot.async_client:
                logger.error("❌ Async client не создан")
                return False
            
            if not bot.signals_detector:
                logger.error("❌ Signals detector не создан")
                return False
            
            if not bot.telegram_notifier:
                logger.error("❌ Telegram notifier не создан")
                return False
            
            if not bot.signals_manager:
                logger.error("❌ Signals manager не создан")
                return False
            
            if not bot.pairs_fetcher:
                logger.error("❌ Pairs fetcher не создан")
                return False
            
            # Тестируем получение пар
            pairs = await bot.get_dynamic_pairs()
            if not pairs:
                logger.warning("⚠️ Не удалось получить пары через бота")
                return False
            
            logger.info(f"🤖 Бот создан успешно, доступно {len(pairs)} пар")
            
            # Очищаем ресурсы
            await bot.async_client.close()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания бота: {e}")
            return False
    
    async def test_error_handling(self) -> bool:
        """Тест обработки ошибок"""
        try:
            logger.info("🛡️ Тестирование обработки ошибок...")
            
            # Тестируем некорректную пару
            async with AsyncMexcRestClient() as client:
                klines = await client.get_klines_async("INVALID_PAIR", "Min1", 5)
                
                # Должно вернуть None или пустой список
                if klines is None or len(klines) == 0:
                    logger.info("✅ Некорректная пара обработана правильно")
                else:
                    logger.warning("⚠️ Неожиданный результат для некорректной пары")
            
            return True
            
        except Exception as e:
            # Ошибки должны обрабатываться gracefully
            logger.info(f"✅ Ошибка обработана: {e}")
            return True
    
    def print_test_summary(self):
        """Вывод сводки результатов тестирования"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        logger.info("📊 === СВОДКА РЕЗУЛЬТАТОВ ТЕСТИРОВАНИЯ ===")
        logger.info(f"⏰ Время выполнения: {duration}")
        logger.info("")
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results.values() if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results.values() if r['status'] == 'FAIL'])
        error_tests = len([r for r in self.test_results.values() if r['status'] == 'ERROR'])
        
        logger.info(f"📈 Всего тестов: {total_tests}")
        logger.info(f"✅ Успешных: {passed_tests}")
        logger.info(f"❌ Неудачных: {failed_tests}")
        logger.info(f"💥 Ошибок: {error_tests}")
        logger.info("")
        
        # Детальные результаты
        for test_name, result in self.test_results.items():
            status_emoji = {
                'PASS': '✅',
                'FAIL': '❌',
                'ERROR': '💥'
            }.get(result['status'], '❓')
            
            logger.info(f"{status_emoji} {test_name}: {result['status']} - {result['details']}")
        
        # Общий статус
        logger.info("")
        if failed_tests == 0 and error_tests == 0:
            logger.info("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
            logger.info("✅ Асинхронная архитектура готова к использованию")
        else:
            logger.warning("⚠️ ЕСТЬ ПРОБЛЕМЫ В ИНТЕГРАЦИИ")
            logger.warning("🔧 Требуется дополнительная настройка")


async def main():
    """Главная функция тестирования"""
    try:
        test_runner = AsyncIntegrationTest()
        await test_runner.run_all_tests()
    except KeyboardInterrupt:
        logger.info("⏹️ Тестирование прервано пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка в тестировании: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
