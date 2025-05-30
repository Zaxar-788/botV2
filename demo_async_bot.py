#!/usr/bin/env python3
"""
Демонстрация новой асинхронной архитектуры бота анализа аномалий MEXC Futures

НОВЫЕ ВОЗМОЖНОСТИ:
🚀 Динамический список пар из pairs_fetcher (750+ пар)
⚡ Полная асинхронность с asyncio/TaskGroup
🔄 Автоматическое обновление списка пар
⚙️ Graceful worker management для добавленных/удаленных пар
🛡️ Изоляция ошибок - сбой одной пары не влияет на остальные
🚫 Никаких блокирующих операций

Этот скрипт демонстрирует:
1. Запуск асинхронного бота с динамическим списком пар
2. Мониторинг статистики в реальном времени
3. Graceful shutdown при Ctrl+C
4. Обработку изменений в списке пар
"""

import asyncio
import signal
import sys
import os
from datetime import datetime
import time

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import AsyncMexcAnalysisBot
from src.utils.logger import setup_main_logger
from src.config import TIMEFRAMES

# Настройка логирования
logger = setup_main_logger()


class AsyncBotDemo:
    """
    Демонстрационная обертка для асинхронного бота
    """
    
    def __init__(self):
        self.bot = None
        self.stats_task = None
        self.demo_start_time = None
        
    async def run_demo(self):
        """
        Основная демонстрация асинхронной архитектуры
        """
        self.demo_start_time = datetime.now()
        
        logger.info("🎯 === ДЕМОНСТРАЦИЯ АСИНХРОННОЙ АРХИТЕКТУРЫ ===")
        logger.info("🚀 MEXC Futures Anomaly Analysis Bot - Async Version 2.0")
        logger.info("💡 Нажмите Ctrl+C для graceful shutdown")
        logger.info("📊 Статистика будет обновляться каждые 30 секунд")
        logger.info("")
        
        try:
            # Создаем асинхронного бота с настройками для демо
            self.bot = AsyncMexcAnalysisBot(
                timeframes=["Min1", "Min5"],  # Ограничиваем для демо
                analysis_interval=30,        # Ускоренный анализ для демо
                pairs_update_interval=120    # Обновление пар каждые 2 минуты для демо
            )
            
            # Запускаем задачу мониторинга статистики
            self.stats_task = asyncio.create_task(self.monitor_statistics())
            
            # Запускаем основной бот
            logger.info("▶️ Запуск асинхронного мультипарного анализа...")
            await self.bot.run_async()
            
        except KeyboardInterrupt:
            logger.info("\n⏹️ Получен сигнал остановки (Ctrl+C)")
            await self.graceful_shutdown()
        except Exception as e:
            logger.error(f"💥 Критическая ошибка в демо: {e}")
            raise
    
    async def monitor_statistics(self):
        """
        Мониторинг и вывод статистики работы бота
        """
        iteration = 0
        
        while True:
            try:
                await asyncio.sleep(30)  # Статистика каждые 30 секунд
                iteration += 1
                
                if self.bot:
                    self.print_demo_statistics(iteration)
                
            except asyncio.CancelledError:
                logger.info("📊 Мониторинг статистики остановлен")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в мониторинге статистики: {e}")
    
    def print_demo_statistics(self, iteration: int):
        """
        Красивый вывод статистики демонстрации
        """
        if not self.bot:
            return
            
        # Получаем статус системы
        status = self.bot.get_system_status()
        
        # Вычисляем время работы
        uptime = datetime.now() - self.demo_start_time
        uptime_str = str(uptime).split('.')[0]  # Убираем микросекунды
        
        logger.info("")
        logger.info(f"📊 === СТАТИСТИКА ДЕМО #{iteration} ===")
        logger.info(f"⏰ Время работы: {uptime_str}")
        logger.info(f"🏃 Статус: {'РАБОТАЕТ' if status['running'] else 'ОСТАНОВЛЕН'}")
        logger.info("")
        logger.info("🔢 ОСНОВНЫЕ МЕТРИКИ:")
        logger.info(f"  📈 Торговых пар: {status['total_pairs']}")
        logger.info(f"  ⚙️ Активных задач: {status['total_tasks']}")
        logger.info(f"  🔍 Всего анализов: {status['total_analyses']}")
        logger.info(f"  🎯 Найдено сигналов: {status['total_signals']}")
        logger.info("")
        logger.info("⚙️ КОНФИГУРАЦИЯ:")
        logger.info(f"  ⏱️ Интервал анализа: {status['analysis_interval']}с")
        logger.info(f"  🔄 Интервал обновления пар: {status['pairs_update_interval']}с")
        logger.info(f"  📅 Таймфреймы: {', '.join(status['timeframes'])}")
        
        # Статистика по эффективности
        if status['total_analyses'] > 0:
            signal_rate = (status['total_signals'] / status['total_analyses']) * 100
            logger.info("")
            logger.info("📈 ЭФФЕКТИВНОСТЬ:")
            logger.info(f"  🎯 Процент сигналов: {signal_rate:.2f}%")
            
            # Анализов в минуту
            uptime_minutes = uptime.total_seconds() / 60
            if uptime_minutes > 0:
                analyses_per_minute = status['total_analyses'] / uptime_minutes
                logger.info(f"  ⚡ Анализов в минуту: {analyses_per_minute:.1f}")
        
        logger.info("─" * 50)
    
    async def graceful_shutdown(self):
        """
        Graceful shutdown демонстрации
        """
        logger.info("🛑 Начинаю graceful shutdown...")
        
        # Останавливаем мониторинг статистики
        if self.stats_task and not self.stats_task.done():
            self.stats_task.cancel()
            try:
                await self.stats_task
            except asyncio.CancelledError:
                pass
        
        # Останавливаем бота
        if self.bot:
            self.bot.stop()
            # Даем время на graceful shutdown
            await asyncio.sleep(2)
        
        # Финальная статистика
        if self.bot:
            logger.info("")
            logger.info("📊 === ФИНАЛЬНАЯ СТАТИСТИКА ДЕМО ===")
            status = self.bot.get_system_status()
            uptime = datetime.now() - self.demo_start_time
            
            logger.info(f"⏰ Общее время работы: {str(uptime).split('.')[0]}")
            logger.info(f"🔍 Всего анализов: {status['total_analyses']}")
            logger.info(f"🎯 Найдено сигналов: {status['total_signals']}")
            logger.info(f"📈 Обработано пар: {status['total_pairs']}")
            
            if status['total_analyses'] > 0:
                signal_rate = (status['total_signals'] / status['total_analyses']) * 100
                logger.info(f"📊 Процент сигналов: {signal_rate:.2f}%")
        
        logger.info("✅ Демонстрация завершена")


async def run_simple_test():
    """
    Простой тест асинхронной архитектуры (без полного запуска)
    """
    logger.info("🧪 === ПРОСТОЙ ТЕСТ АСИНХРОННОЙ АРХИТЕКТУРЫ ===")
    
    try:
        # Создаем бота для тестирования
        bot = AsyncMexcAnalysisBot(
            timeframes=["Min1"],
            analysis_interval=60,
            pairs_update_interval=300
        )
        
        # Тестируем получение пар
        logger.info("📡 Тестирование получения динамических пар...")
        pairs = await bot.get_dynamic_pairs()
        logger.info(f"✅ Получено {len(pairs)} торговых пар")
        
        if pairs:
            logger.info(f"📋 Примеры пар: {', '.join(pairs[:5])}...")
        
        # Тестируем асинхронный клиент
        logger.info("🔌 Тестирование асинхронного REST клиента...")
        
        test_pair = pairs[0] if pairs else "BTC_USDT"
        klines = await bot.async_client.get_klines_async(test_pair, "Min1", 10)
        
        if klines:
            logger.info(f"✅ Получено {len(klines)} свечей для {test_pair}")
            logger.info(f"📊 Последняя свеча: цена {klines[-1].get('c', 'N/A')}")
        else:
            logger.warning(f"⚠️ Не удалось получить данные для {test_pair}")
        
        # Закрываем ресурсы
        await bot.async_client.close()
        
        logger.info("✅ Простой тест завершен успешно")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в простом тесте: {e}")
        raise


def setup_signal_handlers():
    """
    Настройка обработчиков сигналов для Windows
    """
    if os.name == 'nt':  # Windows
        # На Windows используем signal.signal для SIGINT (Ctrl+C)
        def signal_handler(signum, frame):
            logger.info("🛑 Получен сигнал прерывания")
            raise KeyboardInterrupt()
        
        signal.signal(signal.SIGINT, signal_handler)


async def main():
    """
    Главная функция демонстрации
    """
    print("🎯 MEXC Futures Async Bot Demo")
    print("=" * 50)
    print("Выберите режим демонстрации:")
    print("1. Полная демонстрация (с мониторингом)")
    print("2. Простой тест архитектуры")
    print("3. Выход")
    print("=" * 50)
    
    try:
        choice = input("Введите номер (1-3): ").strip()
        
        if choice == "1":
            setup_signal_handlers()
            demo = AsyncBotDemo()
            await demo.run_demo()
            
        elif choice == "2":
            await run_simple_test()
            
        elif choice == "3":
            logger.info("👋 Выход из демонстрации")
            return
            
        else:
            print("❌ Неверный выбор")
            return
            
    except KeyboardInterrupt:
        logger.info("👋 Демонстрация прервана пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"💥 Ошибка запуска демо: {e}")
        sys.exit(1)
