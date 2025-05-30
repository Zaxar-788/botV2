"""
Основной модуль бота для анализа аномалий на MEXC Futures

Этот модуль объединяет все компоненты системы:
- Получение данных через REST API
- Анализ спайков объёма
- Отправка уведомлений в Telegram

Версия с поддержкой мультипарности и мульти-таймфрейм анализа
"""

import time
import logging
from typing import Optional, List, Dict, Tuple

# Импорты наших модулей
from src.utils.logger import setup_main_logger
from src.data.rest_client import MexcRestClient
from src.signals.detector import VolumeSpikeDetector, VolumeSignal
from src.telegram.bot import TelegramNotifier
from src.config import TRADING_PAIRS, TIMEFRAMES, TIMEFRAME_CONFIGS

# Настройка логирования
logger = logging.getLogger(__name__)


class MexcAnalysisBot:
    """
    Основной класс бота для анализа аномалий на MEXC Futures
    
    Поддерживает анализ нескольких торговых пар и таймфреймов одновременно.
    Выполняет циклический анализ торговых данных и отправляет уведомления
    о найденных аномалиях объёма.
    """
    
    def __init__(self, pairs: List[str] = None, timeframes: List[str] = None):
        """
        Инициализация бота
        
        Args:
            pairs (List[str]): Список торговых пар для анализа
            timeframes (List[str]): Список таймфреймов для анализа
        """
        logger.info("🚀 Инициализация мультипарного бота анализа MEXC Futures...")
        
        # Используем переданные пары или дефолтные из конфига
        self.trading_pairs = pairs or TRADING_PAIRS
        self.timeframes = timeframes or TIMEFRAMES
        
        logger.info(f"📈 Торговые пары: {', '.join(self.trading_pairs)}")
        logger.info(f"⏰ Таймфреймы: {', '.join(self.timeframes)}")
        
        # Инициализируем компоненты
        self.rest_client = MexcRestClient()
        self.volume_detector = VolumeSpikeDetector()
        self.telegram_notifier = TelegramNotifier()
        
        # Статистика работы для каждой пары и таймфрейма
        self.analysis_stats = {}
        self.total_analyses = 0
        self.total_signals = 0
        
        # Инициализируем статистику
        self._init_statistics()
        
        logger.info("✅ Мультипарный бот успешно инициализирован")
    
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
        """
        Выполнение анализа конкретной пары на конкретном таймфрейме
        
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
            
            # Шаг 1: Получаем свечи через REST API
            logger.debug(f"📊 Получение данных для {pair} ({timeframe})...")
            klines = self.rest_client.get_klines(
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
            
            # Шаг 3: Анализируем спайки объёма
            logger.debug(f"🔍 Анализ {len(klines)} свечей {pair} ({timeframe}) на спайки объёма...")
            signal = detector.analyze_volume_spike(klines, pair, timeframe)
            
            # Обновляем статистику
            self.analysis_stats[pair][timeframe]['analyses'] += 1
            self.total_analyses += 1
            
            # Шаг 4: Если найден сигнал - отправляем уведомление
            if signal:
                logger.info(f"🎯 Обнаружен сигнал для {pair} ({timeframe}): {signal.message}")
                
                # Отправляем через Telegram (пока print)
                success = self.telegram_notifier.send_volume_signal(signal)
                if success:
                    self.analysis_stats[pair][timeframe]['signals'] += 1
                    self.analysis_stats[pair][timeframe]['last_signal'] = signal
                    self.total_signals += 1
                    logger.info(f"📤 Сигнал для {pair} ({timeframe}) успешно отправлен")
                else:
                    logger.error(f"❌ Ошибка при отправке сигнала для {pair} ({timeframe})")
                
                return signal
            else:
                logger.debug(f"✅ Аномалий не обнаружено для {pair} ({timeframe})")
                return None
                
        except Exception as e:
            logger.error(f"💥 Ошибка при анализе {pair} ({timeframe}): {e}")
            return None
    
    def analyze_single_iteration(self) -> List[VolumeSignal]:
        """
        Выполнение одной итерации анализа для всех пар и таймфреймов
        
        Returns:
            List[VolumeSignal]: Список найденных сигналов        """
        all_signals = []
        
        logger.info(f"🔄 Анализ {len(self.trading_pairs)} пар на {len(self.timeframes)} таймфреймах...")
        
        # Перебираем все пары
        for pair in self.trading_pairs:
            # Перебираем все таймфреймы для каждой пары
            for timeframe in self.timeframes:
                signal = self.analyze_pair_timeframe(pair, timeframe)
                if signal:
                    all_signals.append(signal)
        
        if all_signals:
            logger.info(f"🎯 Итерация завершена: найдено {len(all_signals)} сигналов")
        else:
            logger.info("✅ Итерация завершена: аномалий не обнаружено")
        
        return all_signals
    
    def run_continuous_analysis(self, interval_seconds: int = 60):
        """
        Запуск непрерывного анализа с заданным интервалом
        
        Args:
            interval_seconds (int): Интервал между проверками в секундах
        """
        logger.info(f"🔄 Запуск непрерывного мультипарного анализа с интервалом {interval_seconds} секунд")
        logger.info(f"📈 Отслеживаемые пары: {', '.join(self.trading_pairs)}")
        logger.info(f"⏰ Таймфреймы: {', '.join(self.timeframes)}")
        
        # Отправляем уведомление о запуске
        self.telegram_notifier.send_startup_notification()
        
        try:
            iteration = 0
            while True:
                iteration += 1
                logger.info(f"🔄 Итерация анализа #{iteration}")
                
                # Выполняем анализ всех пар и таймфреймов
                signals = self.analyze_single_iteration()
                
                # Выводим статистику каждые 10 итераций
                if iteration % 10 == 0:
                    self._print_detailed_statistics()
                
                # Ждём до следующей итерации
                logger.debug(f"😴 Ожидание {interval_seconds} секунд до следующей проверки...")
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("⏹️ Получен сигнал остановки (Ctrl+C)")
            self.stop()
        except Exception as e:
            logger.error(f"💥 Критическая ошибка в цикле анализа: {e}")
            self.stop()
    
    def run_single_analysis(self):
        """
        Выполнение одного анализа всех пар и таймфреймов (для тестирования)
        """
        logger.info("🧪 Запуск одиночного мультипарного анализа для тестирования...")
        
        signals = self.analyze_single_iteration()
        
        if signals:
            logger.info(f"✅ Тест завершён: обнаружено {len(signals)} сигналов")
            for signal in signals:
                logger.info(f"   📊 {signal.pair} ({signal.timeframe}): {signal.spike_ratio:.2f}x")
        else:
            logger.info("✅ Тест завершён: аномалий не обнаружено")
        
        return signals
    
    def _print_detailed_statistics(self):
        """Вывод детальной статистики по всем парам и таймфреймам"""
        logger.info("📊 Детальная статистика анализа:")
        logger.info(f"   🔍 Общий анализов: {self.total_analyses}")
        logger.info(f"   🎯 Общий сигналов: {self.total_signals}")
        
        for pair in self.trading_pairs:
            pair_total_analyses = sum(
                self.analysis_stats[pair][tf]['analyses'] 
                for tf in self.timeframes
            )
            pair_total_signals = sum(
                self.analysis_stats[pair][tf]['signals'] 
                for tf in self.timeframes
            )
            
            if pair_total_analyses > 0:
                logger.info(f"   📈 {pair}: {pair_total_analyses} анализов, {pair_total_signals} сигналов")
                
                for timeframe in self.timeframes:
                    stats = self.analysis_stats[pair][timeframe]
                    if stats['analyses'] > 0:
                        logger.debug(f"      ⏰ {timeframe}: {stats['analyses']} анализов, {stats['signals']} сигналов")
    
    def stop(self):
        """Остановка бота и освобождение ресурсов"""
        logger.info("🛑 Остановка мультипарного бота...")
        
        # Закрываем соединения
        if hasattr(self.rest_client, 'close'):
            self.rest_client.close()
        
        # Выводим финальную статистику
        self._print_detailed_statistics()
        
        logger.info("👋 Мультипарный бот остановлен")


def main():
    """
    Главная функция приложения
    """
    try:
        # Настраиваем логирование
        setup_main_logger()
        
        logger.info("🎯 Запуск мультипарного бота анализа аномалий MEXC Futures")
        logger.info("💡 Для остановки нажмите Ctrl+C")
        
        # Создаём и запускаем бота
        # Можно настроить конкретные пары и таймфреймы или использовать дефолтные
        bot = MexcAnalysisBot()
          # Можно выбрать режим работы:
        # bot.run_single_analysis()  # Одиночный анализ для тестирования
        bot.run_continuous_analysis(interval_seconds=60)  # Непрерывный анализ каждую минуту
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка запуска: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
