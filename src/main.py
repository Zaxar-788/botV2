"""
Основной модуль бота для анализа аномалий на MEXC Futures

Этот модуль объединяет все компоненты системы:
- Получение данных через REST API
- Анализ спайков объёма
- Отправка уведомлений в Telegram

Версия с поддержкой мультипарности и мульти-таймфрейм анализа
НОВАЯ АРХИТЕКТУРА: Асинхронная обработка 750+ пар с динамическим списком
"""

import time
import logging
import asyncio
from asyncio import TaskGroup
from typing import Optional, List, Dict, Tuple, Set, Callable
from dataclasses import dataclass
from datetime import datetime
import threading

# Импорты наших модулей
from src.utils.logger import setup_main_logger
from src.data.rest_client import MexcRestClient
from src.data.async_rest_client import AsyncMexcRestClient
from src.data.database import SignalsManager
from src.data.pairs_fetcher import get_pairs_fetcher, MexcPairsFetcher
from src.signals.detector import VolumeSpikeDetector, VolumeSignal
from src.telegram.bot import TelegramNotifier
from src.config import TRADING_PAIRS, TIMEFRAMES, TIMEFRAME_CONFIGS, DATABASE_CONFIG, CACHE_CONFIG, PAIRS_FETCHER_CONFIG

# Настройка логирования
logger = logging.getLogger(__name__)


@dataclass
class PairAnalysisTask:
    """Структура для описания задачи анализа пары"""
    pair: str
    timeframe: str
    task: Optional[asyncio.Task] = None
    last_run: Optional[datetime] = None
    error_count: int = 0
    max_errors: int = 5
    last_run: Optional[datetime] = None
    error_count: int = 0
    max_errors: int = 5


class AsyncMexcAnalysisBot:
    """
    Асинхронный бот для анализа аномалий на MEXC Futures
    
    НОВАЯ АРХИТЕКТУРА:
    - Динамический список пар из pairs_fetcher (750+ пар)
    - Асинхронная обработка каждой пары независимо
    - Автоматическое добавление/удаление пар при изменении списка
    - Масштабируемость без ограничений на количество пар
    - Изоляция ошибок - сбой одной пары не влияет на остальные
    """
    
    def __init__(self, timeframes: List[str] = None, 
                 analysis_interval: int = 60,
                 pairs_update_interval: int = 3600):
        """
        Инициализация асинхронного бота
        
        Args:
            timeframes (List[str]): Список таймфреймов для анализа
            analysis_interval (int): Интервал анализа пар в секундах
            pairs_update_interval (int): Интервал обновления списка пар в секундах
        """
        logger.info("🚀 Инициализация асинхронного мультипарного бота анализа MEXC Futures...")
        
        # Конфигурация
        self.timeframes = timeframes or TIMEFRAMES
        self.analysis_interval = analysis_interval
        self.pairs_update_interval = pairs_update_interval        # Инициализируем компоненты
        self.async_client = AsyncMexcRestClient(
            max_connections=100,  # Пул соединений для 750+ пар
            max_connections_per_host=30,
            request_timeout=10
        )
        self.signals_detector = VolumeSpikeDetector()
        self.telegram_notifier = TelegramNotifier()
        self.signals_manager = SignalsManager(DATABASE_CONFIG, CACHE_CONFIG)
        
        # Инициализируем фетчер пар с автообновлением
        self.pairs_fetcher = get_pairs_fetcher(self.pairs_update_interval)
        
        # Состояние системы
        self.current_pairs: Set[str] = set()
        self.running_tasks: Dict[str, PairAnalysisTask] = {}  # key: f"{pair}_{timeframe}"
        self.shutdown_event = asyncio.Event()
        self.pairs_update_task: Optional[asyncio.Task] = None
        
        # Статистика
        self.total_analyses = 0
        self.total_signals = 0
        self.analysis_stats: Dict[str, Dict[str, Dict]] = {}
        
        logger.info(f"⏰ Таймфреймы: {', '.join(self.timeframes)}")
        logger.info(f"🔄 Интервал анализа: {analysis_interval}s")
        logger.info(f"📡 Интервал обновления пар: {pairs_update_interval}s")
        logger.info("✅ Асинхронный мультипарный бот инициализирован")
    
    def _init_pair_stats(self, pair: str):
        """Инициализация статистики для пары"""
        if pair not in self.analysis_stats:
            self.analysis_stats[pair] = {}
            for timeframe in self.timeframes:
                self.analysis_stats[pair][timeframe] = {
                    'analyses': 0,
                    'signals': 0,
                    'errors': 0,
                    'last_signal': None,
                    'last_analysis': None
                }

    async def get_dynamic_pairs(self) -> List[str]:
        """
        Получение актуального списка торговых пар
        
        Returns:
            List[str]: Список всех доступных торговых пар
        """
        try:
            # Получаем все доступные пары через pairs_fetcher
            pairs = self.pairs_fetcher.get_all_pairs()
            
            if pairs:
                logger.debug(f"📡 Получено {len(pairs)} торговых пар от API")
                return pairs
            else:
                # Если API недоступно, используем fallback из конфига
                logger.warning("⚠️ Не удалось получить пары от API, используем fallback")
                return TRADING_PAIRS
                
        except Exception as e:
            logger.error(f"❌ Ошибка при получении списка пар: {e}")
            return TRADING_PAIRS  # Fallback на статический список

    async def analyze_pair_timeframe_async(self, pair: str, timeframe: str) -> Optional[VolumeSignal]:
        """
        Асинхронный анализ конкретной пары на конкретном таймфрейме
        
        Args:
            pair (str): Торговая пара (например, BTC_USDT)
            timeframe (str): Таймфрейм (например, Min1)
            
        Returns:
            VolumeSignal: Найденный сигнал или None
        """
        try:
            # Получаем настройки для данного таймфрейма
            tf_config = TIMEFRAME_CONFIGS.get(timeframe, {
                'limit': 50,
                'window': 10,
                'threshold': 2.0
            })
              # Шаг 1: Получаем свечи через асинхронный REST API
            logger.debug(f"📊 Получение данных для {pair} ({timeframe})...")
            
            klines = await self.async_client.get_klines_async(
                pair=pair,
                interval=timeframe,
                limit=tf_config['limit']
            )
            
            if not klines:
                logger.warning(f"❌ Не удалось получить данные для {pair} ({timeframe})")
                return None
            
            # Шаг 2: Настраиваем детектор для этого таймфрейма
            detector = VolumeSpikeDetector(
                threshold=tf_config['threshold'],
                window_size=tf_config['window']
            )
              # Шаг 3: Анализируем спайки объёма (тоже в executor для CPU-интенсивных операций)
            signal = await asyncio.to_thread(
                detector.analyze_volume_spike,
                klines, pair, timeframe
            )
            
            # Обновляем статистику
            self._update_analysis_stats(pair, timeframe, signal)
            
            # Шаг 4: Если найден сигнал - сохраняем и отправляем уведомление
            if signal:
                logger.info(f"🎯 Обнаружен сигнал для {pair} ({timeframe}): {signal.message}")
                  # Сохраняем сигнал в базу данных через кэш
                await asyncio.to_thread(self.signals_manager.save_signal, signal)
                logger.debug(f"💾 Сигнал для {pair} ({timeframe}) сохранен в БД")
                  # Отправляем через Telegram
                success = await asyncio.to_thread(self.telegram_notifier.send_volume_signal, signal)
                if success:
                    logger.info(f"📤 Сигнал для {pair} ({timeframe}) успешно отправлен")
                else:
                    logger.error(f"❌ Ошибка при отправке сигнала для {pair} ({timeframe})")
                
                return signal
            else:
                logger.debug(f"✅ Аномалий не обнаружено для {pair} ({timeframe})")
                return None
                
        except Exception as e:
            logger.error(f"💥 Ошибка при анализе {pair} ({timeframe}): {e}")
            self._update_error_stats(pair, timeframe)
            return None
    
    def _update_analysis_stats(self, pair: str, timeframe: str, signal: Optional[VolumeSignal]):
        """Обновление статистики анализа"""
        self._init_pair_stats(pair)
        
        self.analysis_stats[pair][timeframe]['analyses'] += 1
        self.analysis_stats[pair][timeframe]['last_analysis'] = datetime.now()
        self.total_analyses += 1
        
        if signal:
            self.analysis_stats[pair][timeframe]['signals'] += 1
            self.analysis_stats[pair][timeframe]['last_signal'] = signal
            self.total_signals += 1
    
    def _update_error_stats(self, pair: str, timeframe: str):
        """Обновление статистики ошибок"""
        self._init_pair_stats(pair)
        self.analysis_stats[pair][timeframe]['errors'] += 1

    async def continuous_pair_analysis(self, pair: str, timeframe: str):
        """
        Непрерывный анализ конкретной пары на конкретном таймфрейме
        
        Эта корутина работает бесконечно, анализируя одну пару/таймфрейм
        с заданным интервалом до получения сигнала shutdown.
        """
        task_key = f"{pair}_{timeframe}"
        error_count = 0
        max_errors = 5
        
        logger.debug(f"🔄 Запущен непрерывный анализ для {pair} ({timeframe})")
        
        try:
            while not self.shutdown_event.is_set():
                try:
                    # Выполняем анализ
                    signal = await self.analyze_pair_timeframe_async(pair, timeframe)
                    
                    # Сбрасываем счетчик ошибок при успешном анализе
                    error_count = 0
                    
                    # Обновляем информацию о задаче
                    if task_key in self.running_tasks:
                        self.running_tasks[task_key].last_run = datetime.now()
                        self.running_tasks[task_key].error_count = error_count
                
                except Exception as e:
                    error_count += 1
                    logger.error(f"❌ Ошибка в анализе {pair} ({timeframe}): {e} (ошибка {error_count}/{max_errors})")
                    
                    # Обновляем счетчик ошибок в задаче
                    if task_key in self.running_tasks:
                        self.running_tasks[task_key].error_count = error_count
                    
                    # Если слишком много ошибок подряд - временно останавливаем эту задачу
                    if error_count >= max_errors:
                        logger.error(f"🚫 Задача {pair} ({timeframe}) остановлена из-за превышения лимита ошибок")
                        break
                
                # Ждем до следующего анализа или сигнала shutdown
                try:
                    await asyncio.wait_for(
                        self.shutdown_event.wait(), 
                        timeout=self.analysis_interval
                    )
                    break  # Получен сигнал shutdown
                except asyncio.TimeoutError:
                    continue  # Таймаут - продолжаем анализ
                    
        except asyncio.CancelledError:
            logger.debug(f"🛑 Задача анализа {pair} ({timeframe}) отменена")
            raise
        except Exception as e:
            logger.error(f"💥 Критическая ошибка в задаче анализа {pair} ({timeframe}): {e}")
        finally:
            logger.debug(f"🏁 Завершена задача анализа {pair} ({timeframe})")

    async def update_pairs_and_tasks(self):
        """
        Периодическое обновление списка пар и управление задачами анализа
        
        Эта корутина:
        1. Получает актуальный список пар
        2. Сравнивает с текущими активными задачами
        3. Запускает новые задачи для новых пар
        4. Останавливает задачи для удаленных пар
        """
        logger.info("🔄 Запущен поток обновления списка пар и управления задачами")
        
        while not self.shutdown_event.is_set():
            try:
                # Получаем актуальный список пар
                new_pairs = await self.get_dynamic_pairs()
                new_pairs_set = set(new_pairs)
                
                logger.debug(f"📡 Проверка обновлений: текущих пар {len(self.current_pairs)}, новых {len(new_pairs_set)}")
                
                # Определяем изменения
                added_pairs = new_pairs_set - self.current_pairs
                removed_pairs = self.current_pairs - new_pairs_set
                
                if added_pairs or removed_pairs:
                    logger.info(f"📈 Изменения в списке пар: +{len(added_pairs)}, -{len(removed_pairs)}")
                    
                    # Останавливаем задачи для удаленных пар
                    if removed_pairs:
                        await self._stop_tasks_for_pairs(removed_pairs)
                    
                    # Запускаем задачи для новых пар
                    if added_pairs:
                        await self._start_tasks_for_pairs(added_pairs)
                    
                    # Обновляем текущий список пар
                    self.current_pairs = new_pairs_set
                    
                    logger.info(f"✅ Обновление завершено. Активных задач: {len(self.running_tasks)}")
                
                # Проверяем состояние задач и перезапускаем упавшие
                await self._check_and_restart_failed_tasks()
                
            except Exception as e:
                logger.error(f"❌ Ошибка при обновлении списка пар: {e}")
            
            # Ждем до следующего обновления или сигнала shutdown
            try:
                await asyncio.wait_for(
                    self.shutdown_event.wait(), 
                    timeout=self.pairs_update_interval
                )
                break  # Получен сигнал shutdown
            except asyncio.TimeoutError:
                continue  # Таймаут - продолжаем работу

    async def _start_tasks_for_pairs(self, pairs: Set[str]):
        """Запуск задач анализа для новых пар"""
        for pair in pairs:
            for timeframe in self.timeframes:
                task_key = f"{pair}_{timeframe}"
                
                if task_key not in self.running_tasks:
                    # Создаем и запускаем новую задачу
                    task = asyncio.create_task(
                        self.continuous_pair_analysis(pair, timeframe),
                        name=task_key
                    )
                    
                    self.running_tasks[task_key] = PairAnalysisTask(
                        pair=pair,
                        timeframe=timeframe,
                        task=task,
                        last_run=None,
                        error_count=0
                    )
                    
                    logger.debug(f"▶️ Запущена задача анализа {pair} ({timeframe})")

    async def _stop_tasks_for_pairs(self, pairs: Set[str]):
        """Остановка задач анализа для удаленных пар"""
        tasks_to_remove = []
        
        for task_key, task_info in self.running_tasks.items():
            if task_info.pair in pairs:
                # Отменяем задачу
                if task_info.task and not task_info.task.done():
                    task_info.task.cancel()
                    try:
                        await task_info.task
                    except asyncio.CancelledError:
                        pass
                
                tasks_to_remove.append(task_key)
                logger.debug(f"⏹️ Остановлена задача анализа {task_info.pair} ({task_info.timeframe})")
        
        # Удаляем остановленные задачи из словаря
        for task_key in tasks_to_remove:
            del self.running_tasks[task_key]

    async def _check_and_restart_failed_tasks(self):
        """Проверка и перезапуск упавших задач"""
        failed_tasks = []
        
        for task_key, task_info in self.running_tasks.items():
            if task_info.task and task_info.task.done():
                # Задача завершилась, проверяем причину
                try:
                    await task_info.task  # Получаем исключение если было
                except asyncio.CancelledError:
                    # Задача была отменена - это нормально
                    continue
                except Exception as e:
                    logger.error(f"💥 Задача {task_key} упала с ошибкой: {e}")
                
                # Если количество ошибок не превышено - перезапускаем
                if task_info.error_count < task_info.max_errors:
                    failed_tasks.append(task_key)
                else:
                    logger.warning(f"🚫 Задача {task_key} не перезапускается (превышен лимит ошибок)")
        
        # Перезапускаем упавшие задачи
        for task_key in failed_tasks:
            task_info = self.running_tasks[task_key]
            
            # Создаем новую задачу
            new_task = asyncio.create_task(
                self.continuous_pair_analysis(task_info.pair, task_info.timeframe),
                name=task_key
            )
            
            task_info.task = new_task
            logger.info(f"🔄 Перезапущена задача {task_key}")

    async def run_async(self):
        """
        Основной асинхронный цикл работы бота
        
        Использует TaskGroup (Python 3.11+) для управления всеми задачами.
        Автоматически останавливает все задачи при получении сигнала завершения.
        """
        logger.info("🚀 Запуск асинхронного мультипарного анализа...")
          # Отправляем уведомление о запуске
        await asyncio.to_thread(self.telegram_notifier.send_startup_notification)
        
        # Запускаем фетчер пар в автоматическом режиме
        self.pairs_fetcher.start_auto_update()
        
        try:
            # Получаем начальный список пар
            initial_pairs = await self.get_dynamic_pairs()
            self.current_pairs = set(initial_pairs)
            
            logger.info(f"📊 Начальный список: {len(self.current_pairs)} торговых пар")
            logger.info(f"⏰ Анализ {len(self.timeframes)} таймфреймов: {', '.join(self.timeframes)}")
            logger.info(f"🎯 Общее количество задач анализа: {len(self.current_pairs) * len(self.timeframes)}")
            
            # Используем TaskGroup для управления всеми задачами
            async with TaskGroup() as tg:
                # Запускаем задачу управления парами
                self.pairs_update_task = tg.create_task(
                    self.update_pairs_and_tasks(),
                    name="pairs_updater"
                )
                
                # Запускаем начальные задачи анализа для всех пар
                await self._start_tasks_for_pairs(self.current_pairs)
                
                logger.info("✅ Все задачи запущены. Система работает в асинхронном режиме")
                logger.info("💡 Для остановки нажмите Ctrl+C")
                
                # Ждем сигнала завершения
                await self.shutdown_event.wait()
                
        except* Exception as eg:
            # TaskGroup автоматически отменяет все задачи при исключении
            logger.error("💥 Критическая ошибка в асинхронном цикле:")
            for e in eg.exceptions:
                logger.error(f"   {type(e).__name__}: {e}")
        finally:
            # Очистка ресурсов
            await self._cleanup()

    async def _cleanup(self):
        """Очистка ресурсов при завершении работы"""
        logger.info("🧹 Начинаю очистку ресурсов...")
        
        # Останавливаем автообновление пар
        if self.pairs_fetcher:
            self.pairs_fetcher.stop_auto_update()
        
        # Отменяем все оставшиеся задачи
        for task_key, task_info in self.running_tasks.items():
            if task_info.task and not task_info.task.done():
                task_info.task.cancel()
                try:
                    await task_info.task
                except asyncio.CancelledError:
                    pass
          # Закрываем соединения
        if hasattr(self.async_client, 'close'):
            await self.async_client.close()
          # Закрываем менеджер сигналов
        await asyncio.to_thread(self.signals_manager.close)
        
        logger.info("✅ Очистка ресурсов завершена")

    def stop(self):
        """Инициация остановки бота"""
        logger.info("🛑 Получен сигнал остановки...")
        self.shutdown_event.set()

    def get_system_status(self) -> Dict:
        """Получение статуса системы"""
        return {
            'total_pairs': len(self.current_pairs),
            'total_tasks': len(self.running_tasks),
            'total_analyses': self.total_analyses,
            'total_signals': self.total_signals,
            'timeframes': self.timeframes,
            'analysis_interval': self.analysis_interval,
            'pairs_update_interval': self.pairs_update_interval,
            'running': not self.shutdown_event.is_set()
        }

    def print_system_statistics(self):
        """Вывод статистики системы"""
        status = self.get_system_status()
        
        logger.info("📊 === СТАТИСТИКА АСИНХРОННОЙ СИСТЕМЫ ===")
        logger.info(f"📈 Всего торговых пар: {status['total_pairs']}")
        logger.info(f"⚙️ Активных задач анализа: {status['total_tasks']}")
        logger.info(f"🔍 Всего анализов: {status['total_analyses']}")
        logger.info(f"🎯 Всего сигналов: {status['total_signals']}")
        logger.info(f"⏰ Таймфреймы: {', '.join(status['timeframes'])}")
        
        # Статистика по парам
        if self.analysis_stats:
            active_pairs = len([p for p in self.analysis_stats.keys() if p in self.current_pairs])
            logger.info(f"📊 Активных пар в статистике: {active_pairs}")


# Обратная совместимость: Адаптер для старого синхронного API
class MexcAnalysisBot:
    """
    Обратно совместимый класс для существующих скриптов
    
    Этот класс предоставляет тот же API, что и раньше, но внутри
    использует новую асинхронную архитектуру для демонстрационных целей.
    """
    
    def __init__(self, pairs: List[str] = None, timeframes: List[str] = None):
        """Инициализация с обратной совместимостью"""
        logger.info("🔄 Инициализация бота (режим обратной совместимости)")
        
        # Используем переданные пары или дефолтные из конфига
        self.trading_pairs = pairs or TRADING_PAIRS
        self.timeframes = timeframes or TIMEFRAMES
        
        # Старые компоненты для совместимости
        self.rest_client = MexcRestClient()
        self.volume_detector = VolumeSpikeDetector()
        self.telegram_notifier = TelegramNotifier()
        self.signals_manager = SignalsManager(DATABASE_CONFIG, CACHE_CONFIG)
        
        # Статистика
        self.analysis_stats = {}
        self.total_analyses = 0
        self.total_signals = 0
        
        self._init_statistics()
        logger.info("✅ Бот инициализирован (обратная совместимость)")
    
    def _init_statistics(self):
        """Инициализация статистики для всех пар и таймфреймов"""
        for pair in self.trading_pairs:
            self.analysis_stats[pair] = {}
            for timeframe in self.timeframes:
                self.analysis_stats[pair][timeframe] = {
                    'analyses': 0,
                    'signals': 0,
                    'last_signal': None
                }
    
    def analyze_pair_timeframe(self, pair: str, timeframe: str) -> Optional[VolumeSignal]:
        """Синхронный анализ пары (для обратной совместимости)"""
        # ...existing synchronous implementation...
        try:
            tf_config = TIMEFRAME_CONFIGS.get(timeframe, {
                'limit': 50, 'window': 10, 'threshold': 2.0
            })
            
            klines = self.rest_client.get_klines(pair=pair, interval=timeframe, limit=tf_config['limit'])
            if not klines:
                return None
            
            detector = VolumeSpikeDetector(threshold=tf_config['threshold'], window_size=tf_config['window'])
            signal = detector.analyze_volume_spike(klines, pair, timeframe)
            
            self.analysis_stats[pair][timeframe]['analyses'] += 1
            self.total_analyses += 1
            
            if signal:
                self.signals_manager.save_signal(signal)
                self.telegram_notifier.send_volume_signal(signal)
                self.analysis_stats[pair][timeframe]['signals'] += 1
                self.analysis_stats[pair][timeframe]['last_signal'] = signal
                self.total_signals += 1
            
            return signal
        except Exception as e:
            logger.error(f"Ошибка при анализе {pair} ({timeframe}): {e}")
            return None
    
    def analyze_single_iteration(self) -> List[VolumeSignal]:
        """Выполнение одной итерации анализа"""
        all_signals = []
        for pair in self.trading_pairs:
            for timeframe in self.timeframes:
                signal = self.analyze_pair_timeframe(pair, timeframe)
                if signal:
                    all_signals.append(signal)
        return all_signals
    
    def run_single_analysis(self):
        """Одиночный анализ для тестирования"""
        return self.analyze_single_iteration()
    
    def run_continuous_analysis(self, interval_seconds: int = 60):
        """Непрерывный анализ (старая версия)"""
        logger.info(f"🔄 Запуск непрерывного анализа с интервалом {interval_seconds} секунд")
        
        try:
            iteration = 0
            while True:
                iteration += 1
                logger.info(f"🔄 Итерация анализа #{iteration}")
                self.analyze_single_iteration()
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("⏹️ Остановка по Ctrl+C")
            self.stop()
    
    def _print_detailed_statistics(self):
        """Статистика"""
        logger.info(f"📊 Анализов: {self.total_analyses}, Сигналов: {self.total_signals}")
    
    def stop(self):
        """Остановка"""
        self.signals_manager.close()
        logger.info("👋 Бот остановлен")

    # Методы для совместимости
    def get_signals_history(self, pair: str = None, timeframe: str = None, limit: int = 50):
        return self.signals_manager.get_signals_history(pair=pair, timeframe=timeframe, limit=limit)
    
    def get_database_statistics(self):
        return self.signals_manager.get_full_statistics()
    
    def export_signals_history(self, filepath: str, pair: str = None, timeframe: str = None, limit: int = 1000):
        return self.signals_manager.export_signals(filepath, pair, timeframe, limit)
    
    def print_database_statistics(self):
        try:
            stats = self.get_database_statistics()
            logger.info("📊 === СТАТИСТИКА БАЗЫ ДАННЫХ ===")
            db_stats = stats.get('database', {})
            logger.info(f"💾 Всего сигналов в БД: {db_stats.get('total_signals', 0)}")
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики БД: {e}")


async def main_async():
    """
    Главная асинхронная функция приложения
    """
    # Настраиваем логирование
    setup_main_logger()
    
    logger.info("🎯 Запуск АСИНХРОННОГО мультипарного бота анализа аномалий MEXC Futures")
    logger.info("🚀 НОВАЯ АРХИТЕКТУРА: Динамический список 750+ пар, полная асинхронность")
    logger.info("💡 Для остановки нажмите Ctrl+C")
    
    try:
        # Создаём и запускаем асинхронного бота
        bot = AsyncMexcAnalysisBot(
            timeframes=TIMEFRAMES,  # Можно настроить конкретные таймфреймы
            analysis_interval=60,    # Интервал анализа каждой пары
            pairs_update_interval=3600  # Интервал обновления списка пар (1 час)
        )
        
        # Запускаем асинхронный анализ
        await bot.run_async()
        
    except KeyboardInterrupt:
        logger.info("⏹️ Получен сигнал остановки (Ctrl+C)")
        if 'bot' in locals():
            bot.stop()
    except Exception as e:
        logger.error(f"💥 Критическая ошибка запуска: {e}")
        raise


def main():
    """
    Точка входа для синхронного запуска асинхронного бота
    """
    try:
        # Запуск асинхронной главной функции
        asyncio.run(main_async())
        return 0
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
        return 0
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
