"""
Демонстрационный скрипт для WebSocket клиента MEXC Futures

Показывает:
- Настройку и запуск WebSocket клиента
- Обработку real-time данных от всех 750+ пар
- Интеграцию с анализатором аномалий
- Мониторинг состояния подключений

Автор: GitHub Copilot
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Dict, Any

# Настройка пути для импортов
sys.path.insert(0, 'g:/Project_VSC/BotV2')

from src.data.ws_client import (
    MexcWebSocketClient, 
    WSMessage, 
    SubscriptionType,
    create_websocket_client
)
from src.data.pairs_fetcher import get_pairs_fetcher
from src.signals.detector import VolumeSpikeDetector
from src.utils.logger import setup_main_logger

# Настройка логирования
logger = setup_main_logger("demo_ws_client", level=logging.INFO)


class RealTimeAnalyzer:
    """
    Демонстрационный анализатор real-time данных
    """
    
    def __init__(self):
        """Инициализация анализатора"""
        self.volume_detector = VolumeSpikeDetector(
            threshold=2.5,  # Более строгий порог для real-time
            window_size=20  # Больше данных для анализа
        )
        
        # Статистика
        self.message_count = 0
        self.ticker_count = 0
        self.kline_count = 0
        self.start_time = datetime.now()
        self.pairs_data: Dict[str, Dict[str, Any]] = {}
        
        logger.info("🎯 Real-time анализатор инициализирован")

    async def handle_realtime_message(self, message: WSMessage) -> None:
        """
        Обработчик real-time сообщений
        
        Args:
            message: Структурированное сообщение от WebSocket
        """
        try:
            self.message_count += 1
            
            # Обновляем данные по паре
            if message.symbol not in self.pairs_data:
                self.pairs_data[message.symbol] = {
                    "last_ticker": None,
                    "last_kline": None,
                    "volume_history": [],
                    "message_count": 0
                }
            
            pair_data = self.pairs_data[message.symbol]
            pair_data["message_count"] += 1
            
            # Обрабатываем разные типы сообщений
            if "ticker" in message.channel:
                await self._handle_ticker_message(message, pair_data)
            elif "kline" in message.channel:
                await self._handle_kline_message(message, pair_data)
            elif "depth" in message.channel:
                await self._handle_depth_message(message, pair_data)
            elif "deals" in message.channel:
                await self._handle_deals_message(message, pair_data)
            
            # Периодически выводим статистику
            if self.message_count % 1000 == 0:
                await self._print_statistics()
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки сообщения {message.symbol}: {e}")

    async def _handle_ticker_message(self, message: WSMessage, pair_data: Dict[str, Any]) -> None:
        """Обработка сообщений тикера"""
        self.ticker_count += 1
        pair_data["last_ticker"] = message.data
        
        # Логируем каждое 100-е сообщение тикера для отладки
        if self.ticker_count % 100 == 0:
            logger.debug(f"📊 Тикер {message.symbol}: {message.data}")

    async def _handle_kline_message(self, message: WSMessage, pair_data: Dict[str, Any]) -> None:
        """Обработка сообщений свечей (K-line)"""
        self.kline_count += 1
        pair_data["last_kline"] = message.data
        
        # Анализируем объём
        kline_data = message.data
        if isinstance(kline_data, dict) and "v" in kline_data:
            try:
                volume = float(kline_data["v"])
                pair_data["volume_history"].append(volume)
                
                # Ограничиваем историю объёмов
                if len(pair_data["volume_history"]) > 50:
                    pair_data["volume_history"] = pair_data["volume_history"][-50:]
                
                # Проверяем спайк объёма
                await self._check_volume_spike(message.symbol, pair_data["volume_history"])
                
            except (ValueError, TypeError) as e:
                logger.debug(f"⚠️ Ошибка обработки объёма для {message.symbol}: {e}")

    async def _handle_depth_message(self, message: WSMessage, pair_data: Dict[str, Any]) -> None:
        """Обработка сообщений стакана"""
        # Здесь можно добавить анализ глубины рынка
        logger.debug(f"📈 Стакан {message.symbol}: {len(message.data)} уровней")

    async def _handle_deals_message(self, message: WSMessage, pair_data: Dict[str, Any]) -> None:
        """Обработка сообщений сделок"""
        # Здесь можно добавить анализ потока сделок
        logger.debug(f"💰 Сделки {message.symbol}: {message.data}")

    async def _check_volume_spike(self, symbol: str, volume_history: list) -> None:
        """Проверка спайка объёма в real-time"""
        if len(volume_history) < 10:
            return
            
        try:
            # Используем простую логику: сравниваем последний объём со средним
            current_volume = volume_history[-1]
            avg_volume = sum(volume_history[:-1]) / len(volume_history[:-1])
            
            if avg_volume > 0 and current_volume / avg_volume > 3.0:
                logger.info(f"🚨 СПАЙК ОБЪЁМА: {symbol} - "
                           f"Текущий: {current_volume:.2f}, Средний: {avg_volume:.2f}, "
                           f"Отношение: {current_volume/avg_volume:.2f}x")
                
        except Exception as e:
            logger.error(f"❌ Ошибка анализа спайка объёма {symbol}: {e}")

    async def _print_statistics(self) -> None:
        """Вывод статистики обработки"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        msg_per_sec = self.message_count / uptime if uptime > 0 else 0
        
        logger.info(f"📊 СТАТИСТИКА REAL-TIME АНАЛИЗА:")
        logger.info(f"   ⏱️  Время работы: {uptime:.1f}s")
        logger.info(f"   📨 Всего сообщений: {self.message_count}")
        logger.info(f"   📈 Тикеры: {self.ticker_count}")
        logger.info(f"   🕯️  Свечи: {self.kline_count}")
        logger.info(f"   🏃 Сообщений/сек: {msg_per_sec:.1f}")
        logger.info(f"   🔗 Активных пар: {len(self.pairs_data)}")

    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики в виде словаря"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        msg_per_sec = self.message_count / uptime if uptime > 0 else 0
        
        return {
            "uptime_seconds": uptime,
            "total_messages": self.message_count,
            "ticker_messages": self.ticker_count,
            "kline_messages": self.kline_count,
            "messages_per_second": msg_per_sec,
            "active_pairs": len(self.pairs_data),
            "pairs_with_data": list(self.pairs_data.keys())[:10]  # Первые 10 для примера
        }


async def demo_websocket_analysis():
    """
    Демонстрация работы WebSocket клиента с real-time анализом
    """
    logger.info("🚀 Запуск демонстрации WebSocket анализа MEXC Futures...")
    
    # Создаем анализатор
    analyzer = RealTimeAnalyzer()
    
    # Создаем WebSocket клиент
    ws_client = create_websocket_client(
        subscription_types=[
            SubscriptionType.TICKER,      # Данные тикера
            SubscriptionType.KLINE_1M,    # 1-минутные свечи
            SubscriptionType.KLINE_5M,    # 5-минутные свечи
        ],
        event_handler=analyzer.handle_realtime_message
    )
    
    # Обработчик остановки
    shutdown_event = asyncio.Event()
    
    def signal_handler():
        logger.info("🛑 Получен сигнал остановки...")
        shutdown_event.set()
    
    # Регистрируем обработчики сигналов
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda s, f: signal_handler())
    
    try:
        # Запускаем WebSocket клиент
        client_task = asyncio.create_task(
            ws_client.start(),
            name="websocket_client"
        )
        
        # Задача для периодического вывода статистики
        async def periodic_stats():
            while not shutdown_event.is_set():
                await asyncio.sleep(30)  # Каждые 30 секунд
                
                if not shutdown_event.is_set():
                    logger.info("📈 СТАТУС WebSocket КЛИЕНТА:")
                    status = ws_client.get_status()
                    logger.info(f"   🔗 Подключений: {status['connections_count']}")
                    logger.info(f"   📊 Пар: {status['total_pairs']}")
                    logger.info(f"   📨 Обработано сообщений: {status['total_messages_processed']}")
                    logger.info(f"   ⏱️  Время работы: {status['uptime_seconds']:.1f}s")
                    
                    # Статистика анализатора
                    analyzer_stats = analyzer.get_statistics()
                    logger.info(f"   🎯 Анализатор: {analyzer_stats['messages_per_second']:.1f} msg/s")
        
        stats_task = asyncio.create_task(
            periodic_stats(),
            name="periodic_stats"
        )
        
        logger.info("✅ WebSocket демонстрация запущена!")
        logger.info("💡 Нажмите Ctrl+C для остановки...")
        
        # Ожидаем сигнал остановки
        await shutdown_event.wait()
        
    except KeyboardInterrupt:
        logger.info("⌨️ Получено прерывание с клавиатуры")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        logger.info("🛑 Остановка WebSocket клиента...")
        
        # Останавливаем клиент
        await ws_client.stop()
        
        # Отменяем задачи
        for task in [client_task, stats_task]:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        logger.info("✅ Демонстрация завершена")


async def demo_simple_websocket():
    """
    Простая демонстрация WebSocket подключения (для тестирования)
    """
    logger.info("🌐 Простая демонстрация WebSocket подключения...")
    
    message_count = 0
    
    async def simple_handler(message: WSMessage):
        nonlocal message_count
        message_count += 1
        
        if message_count <= 10:  # Выводим первые 10 сообщений
            logger.info(f"📨 Сообщение #{message_count}:")
            logger.info(f"   📡 Канал: {message.channel}")
            logger.info(f"   💱 Пара: {message.symbol}")
            logger.info(f"   📊 Данные: {message.data}")
        elif message_count % 100 == 0:  # Потом каждое 100-е
            logger.info(f"📊 Обработано {message_count} сообщений...")
    
    # Создаем клиент только с тикерами для начала
    ws_client = create_websocket_client(
        subscription_types=[SubscriptionType.TICKER],
        event_handler=simple_handler
    )
    
    try:
        # Запускаем на 60 секунд
        logger.info("⏰ Запуск на 60 секунд...")
        await asyncio.wait_for(ws_client.start(), timeout=60)
        
    except asyncio.TimeoutError:
        logger.info("⏰ Тайм-аут демонстрации")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
    finally:
        await ws_client.stop()
        logger.info(f"✅ Получено {message_count} сообщений")


async def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Демонстрация WebSocket клиента MEXC")
    parser.add_argument(
        "--mode", 
        choices=["simple", "full"], 
        default="full",
        help="Режим демонстрации: simple - простой тест, full - полный анализ"
    )
    
    args = parser.parse_args()
    
    if args.mode == "simple":
        await demo_simple_websocket()
    else:
        await demo_websocket_analysis()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 До свидания!")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
