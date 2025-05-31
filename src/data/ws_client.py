"""
WebSocket клиент для real-time анализа всех контрактных пар MEXC Futures

Архитектурно грамотное решение для:
- Подключения к wss://contract.mexc.com/ws
- Подписки на все 750+ контрактных пар
- Автоматической балансировки подключений при лимитах
- Fault-tolerance и автопереподключения
- Изоляции ошибок между парами
- Интеграции с AsyncMexcAnalysisBot

Автор: GitHub Copilot
Версия: 2.0 - Real-time WebSocket архитектура
"""

import asyncio
import json
import logging
import time
import weakref
from asyncio import Queue, Event, TaskGroup
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Callable, Any, Tuple, Union
from urllib.parse import urljoin

import aiohttp
from aiohttp import WSMsgType, ClientWebSocketResponse, ClientSession

from src.data.pairs_fetcher import MexcPairsFetcher, get_pairs_fetcher
from src.utils.logger import setup_main_logger

logger = logging.getLogger(__name__)


class SubscriptionType(Enum):
    """Типы подписок WebSocket"""
    TICKER = "ticker"           # Данные тикера
    KLINE_1M = "kline_Min1"     # 1-минутные свечи
    KLINE_5M = "kline_Min5"     # 5-минутные свечи
    KLINE_15M = "kline_Min15"   # 15-минутные свечи
    KLINE_1H = "kline_Min60"    # 1-часовые свечи
    DEPTH = "depth"             # Стакан заявок
    DEALS = "deals"             # Торговые сделки


class ConnectionState(Enum):
    """Состояния WebSocket подключения"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class WSMessage:
    """Структура для входящих WebSocket сообщений"""
    channel: str
    symbol: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    raw_message: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectionMetrics:
    """Метрики для мониторинга подключения"""
    connection_id: str
    connected_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None
    messages_received: int = 0
    reconnect_count: int = 0
    subscriptions_count: int = 0
    error_count: int = 0
    is_healthy: bool = True


class MexcWebSocketClient:
    """
    Основной WebSocket клиент для MEXC Futures
    
    Особенности:
    - Автоматическая балансировка нагрузки между соединениями
    - Поддержка до 100 подписок на соединение (лимит MEXC)
    - Автопереподключение и обработка ошибок
    - Изоляция событий между парами
    - Real-time обновление подписок при изменении списка пар
    """
    
    WS_BASE_URL = "wss://contract.mexc.com/ws"
    MAX_SUBSCRIPTIONS_PER_CONNECTION = 100  # Лимит MEXC
    PING_INTERVAL = 30  # Интервал ping в секундах
    RECONNECT_DELAY = 5  # Базовая задержка переподключения
    MAX_RECONNECT_ATTEMPTS = 10
    MESSAGE_TIMEOUT = 60  # Таймаут ожидания сообщений
    
    def __init__(self, 
                 pairs_fetcher: Optional[MexcPairsFetcher] = None,
                 subscription_types: List[SubscriptionType] = None,
                 event_handler: Optional[Callable[[WSMessage], None]] = None,
                 error_handler: Optional[Callable[[Exception, str], None]] = None):
        """
        Инициализация WebSocket клиента
        
        Args:
            pairs_fetcher: Фетчер для получения списка пар
            subscription_types: Типы подписок для каждой пары
            event_handler: Обработчик входящих событий
            error_handler: Обработчик ошибок
        """
        logger.info("🌐 Инициализация MEXC Futures WebSocket клиента...")
        
        # Конфигурация
        self.pairs_fetcher = pairs_fetcher or get_pairs_fetcher()
        self.subscription_types = subscription_types or [
            SubscriptionType.TICKER,
            SubscriptionType.KLINE_1M,
            SubscriptionType.KLINE_5M
        ]
        
        # Обработчики событий
        self.event_handler = event_handler
        self.error_handler = error_handler or self._default_error_handler
        
        # Состояние системы
        self.is_running = False
        self.shutdown_event = Event()
        self.message_queue: Queue[WSMessage] = Queue(maxsize=10000)
        
        # Управление соединениями
        self.connections: Dict[str, 'WSConnection'] = {}
        self.connection_tasks: Dict[str, asyncio.Task] = {}
        self.current_pairs: Set[str] = set()
        self.pair_to_connection: Dict[str, str] = {}  # mapping: pair -> connection_id
        
        # Мониторинг
        self.metrics: Dict[str, ConnectionMetrics] = {}
        self.start_time = datetime.now()
        self.total_messages_processed = 0
        
        # Служебные задачи
        self.pairs_monitor_task: Optional[asyncio.Task] = None
        self.message_processor_task: Optional[asyncio.Task] = None
        self.health_monitor_task: Optional[asyncio.Task] = None
        
        logger.info(f"✅ WebSocket клиент инициализирован")
        logger.info(f"📡 Типы подписок: {[t.value for t in self.subscription_types]}")

    async def start(self) -> None:
        """Запуск WebSocket клиента"""
        if self.is_running:
            logger.warning("⚠️ WebSocket клиент уже запущен")
            return
            
        logger.info("🚀 Запуск WebSocket клиента...")
        self.is_running = True
        self.shutdown_event.clear()
        
        try:
            async with TaskGroup() as tg:
                # Запускаем основные задачи
                self.pairs_monitor_task = tg.create_task(
                    self._monitor_pairs_changes(),
                    name="pairs_monitor"
                )
                
                self.message_processor_task = tg.create_task(
                    self._process_messages(),
                    name="message_processor"
                )
                
                self.health_monitor_task = tg.create_task(
                    self._monitor_health(),
                    name="health_monitor"
                )
                
                # Инициальная настройка подключений
                await self._initialize_connections()
                
                logger.info("✅ WebSocket клиент успешно запущен")
                
                # Ожидаем сигнал остановки
                await self.shutdown_event.wait()
                
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в WebSocket клиенте: {e}")
            raise
        finally:
            await self._cleanup()

    async def stop(self) -> None:
        """Остановка WebSocket клиента"""
        if not self.is_running:
            return
            
        logger.info("🛑 Остановка WebSocket клиента...")
        self.is_running = False
        self.shutdown_event.set()

    async def _initialize_connections(self) -> None:
        """Инициальная настройка подключений для всех пар"""
        try:
            # Получаем актуальный список пар
            pairs = self.pairs_fetcher.get_all_pairs()
            if not pairs:
                logger.error("❌ Не удалось получить список пар для инициализации")
                return
                
            logger.info(f"📊 Инициализация подключений для {len(pairs)} пар...")
            
            # Группируем пары по подключениям
            connection_groups = self._distribute_pairs_across_connections(pairs)
            
            # Создаем подключения
            for connection_id, pair_group in connection_groups.items():
                await self._create_connection(connection_id, pair_group)
                
            self.current_pairs = set(pairs)
            logger.info(f"✅ Инициализировано {len(self.connections)} подключений")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при инициализации подключений: {e}")
            raise

    def _distribute_pairs_across_connections(self, pairs: List[str]) -> Dict[str, List[str]]:
        """
        Распределение пар по подключениям с учетом лимитов
        
        Returns:
            Dict[connection_id, pairs_list]
        """
        connections = {}
        total_subscriptions_per_pair = len(self.subscription_types)
        max_pairs_per_connection = self.MAX_SUBSCRIPTIONS_PER_CONNECTION // total_subscriptions_per_pair
        
        logger.debug(f"📊 Максимум {max_pairs_per_connection} пар на соединение "
                    f"({total_subscriptions_per_pair} подписок на пару)")
        
        for i, pair in enumerate(pairs):
            connection_id = f"ws_conn_{i // max_pairs_per_connection}"
            
            if connection_id not in connections:
                connections[connection_id] = []
            
            connections[connection_id].append(pair)
            self.pair_to_connection[pair] = connection_id
        
        logger.info(f"📡 Пары распределены по {len(connections)} подключениям")
        return connections

    async def _create_connection(self, connection_id: str, pairs: List[str]) -> None:
        """Создание нового WebSocket подключения"""
        try:
            logger.info(f"🔗 Создание подключения {connection_id} для {len(pairs)} пар...")
            
            # Создаем объект подключения
            connection = WSConnection(
                connection_id=connection_id,
                client=weakref.ref(self),
                pairs=pairs,
                subscription_types=self.subscription_types
            )
            
            self.connections[connection_id] = connection
            self.metrics[connection_id] = ConnectionMetrics(connection_id=connection_id)
            
            # Запускаем подключение в отдельной задаче
            task = asyncio.create_task(
                connection.run(),
                name=f"connection_{connection_id}"
            )
            self.connection_tasks[connection_id] = task
            
            logger.info(f"✅ Подключение {connection_id} создано")
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания подключения {connection_id}: {e}")
            raise

    async def _monitor_pairs_changes(self) -> None:
        """Мониторинг изменений в списке пар"""
        logger.info("👀 Запуск мониторинга изменений списка пар...")
        
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Проверяем каждую минуту
                
                new_pairs = set(self.pairs_fetcher.get_all_pairs())
                
                if new_pairs != self.current_pairs:
                    logger.info("🔄 Обнаружены изменения в списке пар")
                    await self._handle_pairs_changes(new_pairs)
                    
            except Exception as e:
                await self._handle_error(e, "pairs_monitor")
                await asyncio.sleep(10)

    async def _handle_pairs_changes(self, new_pairs: Set[str]) -> None:
        """Обработка изменений в списке пар"""
        try:
            added_pairs = new_pairs - self.current_pairs
            removed_pairs = self.current_pairs - new_pairs
            
            if added_pairs:
                logger.info(f"➕ Добавлено {len(added_pairs)} новых пар")
                await self._add_pairs(list(added_pairs))
                
            if removed_pairs:
                logger.info(f"➖ Удалено {len(removed_pairs)} пар")
                await self._remove_pairs(list(removed_pairs))
                
            self.current_pairs = new_pairs
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке изменений пар: {e}")

    async def _add_pairs(self, pairs: List[str]) -> None:
        """Добавление новых пар к существующим подключениям"""
        for pair in pairs:
            # Находим подключение с минимальной нагрузкой
            target_connection_id = self._find_least_loaded_connection()
            
            if target_connection_id and target_connection_id in self.connections:
                connection = self.connections[target_connection_id]
                await connection.add_pair(pair)
                self.pair_to_connection[pair] = target_connection_id
            else:
                # Создаем новое подключение, если все заполнены
                new_connection_id = f"ws_conn_{len(self.connections)}"
                await self._create_connection(new_connection_id, [pair])

    async def _remove_pairs(self, pairs: List[str]) -> None:
        """Удаление пар из подключений"""
        for pair in pairs:
            connection_id = self.pair_to_connection.get(pair)
            if connection_id and connection_id in self.connections:
                connection = self.connections[connection_id]
                await connection.remove_pair(pair)
                del self.pair_to_connection[pair]

    def _find_least_loaded_connection(self) -> Optional[str]:
        """Поиск подключения с минимальной нагрузкой"""
        min_load = float('inf')
        target_connection = None
        
        for connection_id, connection in self.connections.items():
            current_load = len(connection.pairs) * len(self.subscription_types)
            if current_load < min_load and current_load < self.MAX_SUBSCRIPTIONS_PER_CONNECTION:
                min_load = current_load
                target_connection = connection_id
                
        return target_connection

    async def _process_messages(self) -> None:
        """Обработка входящих сообщений из очереди"""
        logger.info("📨 Запуск обработчика сообщений...")
        
        while self.is_running:
            try:
                # Получаем сообщение с таймаутом
                message = await asyncio.wait_for(
                    self.message_queue.get(), 
                    timeout=1.0
                )
                
                # Обрабатываем сообщение
                if self.event_handler:
                    await asyncio.create_task(
                        self._safe_handle_message(message),
                        name=f"handle_message_{message.symbol}"
                    )
                
                self.total_messages_processed += 1
                
            except asyncio.TimeoutError:
                continue  # Нормальная ситуация при отсутствии сообщений
            except Exception as e:
                await self._handle_error(e, "message_processor")

    async def _safe_handle_message(self, message: WSMessage) -> None:
        """Безопасная обработка сообщения с изоляцией ошибок"""
        try:
            if asyncio.iscoroutinefunction(self.event_handler):
                await self.event_handler(message)
            else:
                self.event_handler(message)
                
        except Exception as e:
            logger.error(f"❌ Ошибка в обработчике сообщения для {message.symbol}: {e}")

    async def _monitor_health(self) -> None:
        """Мониторинг здоровья всех подключений"""
        logger.info("🏥 Запуск мониторинга здоровья подключений...")
        
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Проверяем каждые 30 секунд
                
                for connection_id, metrics in self.metrics.items():
                    await self._check_connection_health(connection_id, metrics)
                    
            except Exception as e:
                await self._handle_error(e, "health_monitor")

    async def _check_connection_health(self, connection_id: str, metrics: ConnectionMetrics) -> None:
        """Проверка здоровья конкретного подключения"""
        now = datetime.now()
        
        # Проверяем, когда было последнее сообщение
        if metrics.last_message_at:
            silence_duration = (now - metrics.last_message_at).total_seconds()
            if silence_duration > self.MESSAGE_TIMEOUT:
                logger.warning(f"⚠️ Подключение {connection_id} молчит {silence_duration:.1f}s")
                metrics.is_healthy = False
                await self._restart_connection(connection_id)
        
        # Проверяем статус задачи подключения
        task = self.connection_tasks.get(connection_id)
        if task and task.done():
            logger.warning(f"⚠️ Задача подключения {connection_id} завершена")
            metrics.is_healthy = False
            await self._restart_connection(connection_id)

    async def _restart_connection(self, connection_id: str) -> None:
        """Перезапуск проблемного подключения"""
        try:
            logger.info(f"🔄 Перезапуск подключения {connection_id}...")
            
            # Останавливаем старое подключение
            if connection_id in self.connections:
                await self.connections[connection_id].close()
                del self.connections[connection_id]
                
            if connection_id in self.connection_tasks:
                task = self.connection_tasks[connection_id]
                if not task.done():
                    task.cancel()
                del self.connection_tasks[connection_id]
            
            # Получаем пары для этого подключения
            pairs_for_connection = [
                pair for pair, conn_id in self.pair_to_connection.items()
                if conn_id == connection_id
            ]
            
            if pairs_for_connection:
                # Создаем новое подключение
                await self._create_connection(connection_id, pairs_for_connection)
                logger.info(f"✅ Подключение {connection_id} успешно перезапущено")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при перезапуске подключения {connection_id}: {e}")

    async def _handle_error(self, error: Exception, context: str) -> None:
        """Централизованная обработка ошибок"""
        logger.error(f"❌ Ошибка в {context}: {error}")
        
        if self.error_handler:
            try:
                if asyncio.iscoroutinefunction(self.error_handler):
                    await self.error_handler(error, context)
                else:
                    self.error_handler(error, context)
            except Exception as e:
                logger.error(f"❌ Ошибка в обработчике ошибок: {e}")

    def _default_error_handler(self, error: Exception, context: str) -> None:
        """Обработчик ошибок по умолчанию"""
        logger.error(f"🚨 Необработанная ошибка в {context}: {error}")

    async def _cleanup(self) -> None:
        """Очистка ресурсов при остановке"""
        logger.info("🧹 Очистка ресурсов WebSocket клиента...")
        
        try:
            # Останавливаем все подключения
            for connection in self.connections.values():
                await connection.close()
            
            # Отменяем все задачи
            for task in self.connection_tasks.values():
                if not task.done():
                    task.cancel()
            
            # Очищаем состояние
            self.connections.clear()
            self.connection_tasks.clear()
            self.pair_to_connection.clear()
            
            logger.info("✅ Очистка завершена")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при очистке: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Получение статуса клиента"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "is_running": self.is_running,
            "uptime_seconds": uptime,
            "connections_count": len(self.connections),
            "total_pairs": len(self.current_pairs),
            "total_messages_processed": self.total_messages_processed,
            "queue_size": self.message_queue.qsize(),
            "connections": {
                conn_id: {
                    "pairs_count": len(conn.pairs),
                    "state": conn.state.value,
                    "metrics": {
                        "messages_received": metrics.messages_received,
                        "reconnect_count": metrics.reconnect_count,
                        "is_healthy": metrics.is_healthy,
                        "connected_at": metrics.connected_at.isoformat() if metrics.connected_at else None
                    }
                }
                for conn_id, conn in self.connections.items()
                for metrics in [self.metrics.get(conn_id)]
                if metrics
            }
        }


class WSConnection:
    """
    Класс для управления отдельным WebSocket подключением
    
    Отвечает за:
    - Подключение к WebSocket
    - Подписку на каналы для назначенных пар
    - Обработку входящих сообщений
    - Переподключение при сбоях
    - Управление подписками
    """
    
    def __init__(self, 
                 connection_id: str,
                 client: weakref.ref,
                 pairs: List[str],
                 subscription_types: List[SubscriptionType]):
        """
        Инициализация WebSocket подключения
        
        Args:
            connection_id: Уникальный идентификатор подключения
            client: Слабая ссылка на основной клиент
            pairs: Список пар для этого подключения
            subscription_types: Типы подписок
        """
        self.connection_id = connection_id
        self.client_ref = client
        self.pairs = list(pairs)
        self.subscription_types = subscription_types
        
        # Состояние подключения
        self.state = ConnectionState.DISCONNECTED
        self.websocket: Optional[ClientWebSocketResponse] = None
        self.session: Optional[ClientSession] = None
        
        # Управление переподключением
        self.reconnect_count = 0
        self.last_ping = datetime.now()
        self.should_run = True
        
        # Активные подписки
        self.active_subscriptions: Set[str] = set()
        
        logger.debug(f"📡 Инициализировано подключение {connection_id} для {len(pairs)} пар")

    async def run(self) -> None:
        """Основной цикл подключения"""
        logger.info(f"🔗 Запуск подключения {self.connection_id}...")
        
        while self.should_run:
            try:
                await self._connect_and_run()
            except Exception as e:
                logger.error(f"❌ Ошибка в подключении {self.connection_id}: {e}")
                await self._handle_reconnect()

    async def _connect_and_run(self) -> None:
        """Подключение и основной цикл обработки"""
        self.state = ConnectionState.CONNECTING
        
        try:
            # Создаем сессию и подключаемся
            self.session = aiohttp.ClientSession()
            self.websocket = await self.session.ws_connect(
                MexcWebSocketClient.WS_BASE_URL,
                heartbeat=MexcWebSocketClient.PING_INTERVAL
            )
            
            self.state = ConnectionState.CONNECTED
            self.reconnect_count = 0
            
            # Обновляем метрики
            client = self.client_ref()
            if client and self.connection_id in client.metrics:
                metrics = client.metrics[self.connection_id]
                metrics.connected_at = datetime.now()
                metrics.reconnect_count = self.reconnect_count
                metrics.is_healthy = True
            
            logger.info(f"✅ Подключение {self.connection_id} установлено")
            
            # Подписываемся на каналы
            await self._subscribe_to_channels()
            
            # Основной цикл обработки сообщений
            async for msg in self.websocket:
                if msg.type == WSMsgType.TEXT:
                    await self._handle_message(msg.data)
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"❌ WebSocket ошибка {self.connection_id}: {msg.data}")
                    break
                elif msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSED):
                    logger.warning(f"🔌 WebSocket {self.connection_id} закрыт")
                    break
                    
        except Exception as e:
            logger.error(f"❌ Ошибка подключения {self.connection_id}: {e}")
            raise
        finally:
            await self._cleanup_connection()

    async def _subscribe_to_channels(self) -> None:
        """Подписка на все необходимые каналы"""
        if not self.websocket:
            return
            
        logger.info(f"📺 Подписка на каналы для {len(self.pairs)} пар...")
        
        for pair in self.pairs:
            for sub_type in self.subscription_types:
                await self._subscribe_to_channel(pair, sub_type)
                
        logger.info(f"✅ Подписка на {len(self.active_subscriptions)} каналов завершена")

    async def _subscribe_to_channel(self, pair: str, sub_type: SubscriptionType) -> None:
        """Подписка на конкретный канал"""
        try:
            # Формируем имя канала в формате MEXC
            if sub_type == SubscriptionType.TICKER:
                channel = f"spot@public.market.ticker.v3.{pair.replace('_', '')}"
            elif sub_type.value.startswith("kline_"):
                interval = sub_type.value.replace("kline_", "")
                channel = f"spot@public.market.kline.{interval}.{pair.replace('_', '')}"
            elif sub_type == SubscriptionType.DEPTH:
                channel = f"spot@public.market.depth.v3.{pair.replace('_', '')}"
            elif sub_type == SubscriptionType.DEALS:
                channel = f"spot@public.market.deals.v3.{pair.replace('_', '')}"
            else:
                logger.warning(f"⚠️ Неизвестный тип подписки: {sub_type}")
                return
            
            # Отправляем команду подписки
            subscribe_msg = {
                "method": "SUBSCRIPTION",
                "params": [channel]
            }
            
            await self.websocket.send_str(json.dumps(subscribe_msg))
            self.active_subscriptions.add(channel)
            
            logger.debug(f"📺 Подписка на {channel}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка подписки на {pair} {sub_type.value}: {e}")

    async def _handle_message(self, raw_data: str) -> None:
        """Обработка входящего сообщения"""
        try:
            data = json.loads(raw_data)
            
            # Обновляем метрики
            client = self.client_ref()
            if client and self.connection_id in client.metrics:
                metrics = client.metrics[self.connection_id]
                metrics.last_message_at = datetime.now()
                metrics.messages_received += 1
            
            # Парсим сообщение
            message = self._parse_message(data)
            if message and client:
                # Отправляем в очередь обработки
                try:
                    client.message_queue.put_nowait(message)
                except asyncio.QueueFull:
                    logger.warning(f"⚠️ Очередь сообщений переполнена, пропускаем сообщение")
                    
        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка парсинга JSON {self.connection_id}: {e}")
        except Exception as e:
            logger.error(f"❌ Ошибка обработки сообщения {self.connection_id}: {e}")

    def _parse_message(self, data: Dict[str, Any]) -> Optional[WSMessage]:
        """Парсинг сообщения в структурированный формат"""
        try:
            # Определяем тип сообщения по каналу
            channel = data.get("c", "")
            if not channel:
                return None
            
            # Извлекаем символ из канала
            # Примеры каналов:
            # spot@public.market.ticker.v3.BTCUSDT
            # spot@public.market.kline.Min1.BTCUSDT
            parts = channel.split(".")
            if len(parts) < 2:
                return None
                
            symbol_raw = parts[-1]
            # Конвертируем BTCUSDT -> BTC_USDT
            if len(symbol_raw) >= 6:
                if symbol_raw.endswith("USDT"):
                    symbol = f"{symbol_raw[:-4]}_USDT"
                elif symbol_raw.endswith("USD"):
                    symbol = f"{symbol_raw[:-3]}_USD"
                else:
                    symbol = symbol_raw
            else:
                symbol = symbol_raw
            
            # Создаем структурированное сообщение
            return WSMessage(
                channel=channel,
                symbol=symbol,
                data=data.get("d", {}),
                raw_message=data
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга сообщения: {e}")
            return None

    async def _handle_reconnect(self) -> None:
        """Обработка переподключения"""
        if not self.should_run:
            return
            
        self.state = ConnectionState.RECONNECTING
        self.reconnect_count += 1
        
        if self.reconnect_count > MexcWebSocketClient.MAX_RECONNECT_ATTEMPTS:
            logger.error(f"❌ Превышен лимит переподключений для {self.connection_id}")
            self.state = ConnectionState.FAILED
            return
        
        # Экспоненциальная задержка
        delay = min(MexcWebSocketClient.RECONNECT_DELAY * (2 ** (self.reconnect_count - 1)), 60)
        logger.info(f"🔄 Переподключение {self.connection_id} через {delay}s (попытка {self.reconnect_count})")
        
        await asyncio.sleep(delay)

    async def _cleanup_connection(self) -> None:
        """Очистка ресурсов подключения"""
        self.state = ConnectionState.DISCONNECTED
        
        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
            
        if self.session and not self.session.closed:
            await self.session.close()
            
        self.websocket = None
        self.session = None
        self.active_subscriptions.clear()

    async def add_pair(self, pair: str) -> None:
        """Добавление новой пары к подключению"""
        if pair in self.pairs:
            return
            
        self.pairs.append(pair)
        
        # Подписываемся на каналы для новой пары
        if self.websocket and self.state == ConnectionState.CONNECTED:
            for sub_type in self.subscription_types:
                await self._subscribe_to_channel(pair, sub_type)
                
        logger.info(f"➕ Добавлена пара {pair} к подключению {self.connection_id}")

    async def remove_pair(self, pair: str) -> None:
        """Удаление пары из подключения"""
        if pair not in self.pairs:
            return
            
        self.pairs.remove(pair)
        
        # Отписываемся от каналов удаляемой пары
        if self.websocket and self.state == ConnectionState.CONNECTED:
            for sub_type in self.subscription_types:
                await self._unsubscribe_from_channel(pair, sub_type)
                
        logger.info(f"➖ Удалена пара {pair} из подключения {self.connection_id}")

    async def _unsubscribe_from_channel(self, pair: str, sub_type: SubscriptionType) -> None:
        """Отписка от канала"""
        try:
            # Формируем имя канала (аналогично подписке)
            if sub_type == SubscriptionType.TICKER:
                channel = f"spot@public.market.ticker.v3.{pair.replace('_', '')}"
            elif sub_type.value.startswith("kline_"):
                interval = sub_type.value.replace("kline_", "")
                channel = f"spot@public.market.kline.{interval}.{pair.replace('_', '')}"
            elif sub_type == SubscriptionType.DEPTH:
                channel = f"spot@public.market.depth.v3.{pair.replace('_', '')}"
            elif sub_type == SubscriptionType.DEALS:
                channel = f"spot@public.market.deals.v3.{pair.replace('_', '')}"
            else:
                return
            
            # Отправляем команду отписки
            unsubscribe_msg = {
                "method": "UNSUBSCRIPTION",
                "params": [channel]
            }
            
            await self.websocket.send_str(json.dumps(unsubscribe_msg))
            self.active_subscriptions.discard(channel)
            
            logger.debug(f"📺 Отписка от {channel}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отписки от {pair} {sub_type.value}: {e}")

    async def close(self) -> None:
        """Закрытие подключения"""
        logger.info(f"🔌 Закрытие подключения {self.connection_id}...")
        
        self.should_run = False
        await self._cleanup_connection()


# Фабричные функции для удобства использования

def create_websocket_client(
    pairs_fetcher: Optional[MexcPairsFetcher] = None,
    subscription_types: List[SubscriptionType] = None,
    event_handler: Optional[Callable[[WSMessage], None]] = None
) -> MexcWebSocketClient:
    """
    Фабричная функция для создания WebSocket клиента
    
    Args:
        pairs_fetcher: Фетчер пар (если None, создается автоматически)
        subscription_types: Типы подписок
        event_handler: Обработчик событий
        
    Returns:
        MexcWebSocketClient: Настроенный клиент
    """
    return MexcWebSocketClient(
        pairs_fetcher=pairs_fetcher,
        subscription_types=subscription_types,
        event_handler=event_handler
    )


async def create_and_start_websocket_client(
    event_handler: Callable[[WSMessage], None],
    subscription_types: List[SubscriptionType] = None
) -> MexcWebSocketClient:
    """
    Создание и запуск WebSocket клиента в одной функции
    
    Args:
        event_handler: Обработчик событий
        subscription_types: Типы подписок
        
    Returns:
        MexcWebSocketClient: Запущенный клиент
    """
    client = create_websocket_client(
        subscription_types=subscription_types,
        event_handler=event_handler
    )
    
    # Запускаем в фоне
    asyncio.create_task(client.start(), name="websocket_client")
    
    # Ждем инициализации
    await asyncio.sleep(1)
    
    return client
