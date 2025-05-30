"""
Основной модуль бота для анализа аномалий на MEXC Futures

Этот модуль объединяет все компоненты системы:
- Получение данных через REST API
- Анализ спайков объёма
- Отправка уведомлений в Telegram

MVP версия для торговой пары BTC_USDT
"""

import time
import logging
from typing import Optional

# Импорты наших модулей
from src.utils.logger import setup_main_logger
from src.data.rest_client import MexcRestClient
from src.signals.detector import VolumeSpikeDetector, VolumeSignal
from src.telegram.bot import TelegramNotifier
from src.config import TRADING_PAIR, KLINE_LIMIT

# Настройка логирования
logger = logging.getLogger(__name__)


class MexcAnalysisBot:
    """
    Основной класс бота для анализа аномалий на MEXC Futures
    
    Выполняет циклический анализ торговых данных и отправляет уведомления
    о найденных аномалиях объёма.
    """
    
    def __init__(self):
        """Инициализация бота"""
        logger.info("🚀 Инициализация бота анализа MEXC Futures...")
        
        # Инициализируем компоненты
        self.rest_client = MexcRestClient()
        self.volume_detector = VolumeSpikeDetector()
        self.telegram_notifier = TelegramNotifier()
        
        # Статистика работы
        self.analysis_count = 0
        self.signals_sent = 0
        
        logger.info("✅ Бот успешно инициализирован")
    
    def analyze_single_iteration(self) -> Optional[VolumeSignal]:
        """
        Выполнение одной итерации анализа
        
        Returns:
            VolumeSignal: Найденный сигнал или None
        """
        try:
            # Шаг 1: Получаем свечи через REST API
            logger.debug(f"📊 Получение данных для {TRADING_PAIR}...")
            klines = self.rest_client.get_klines(
                pair=TRADING_PAIR,
                limit=KLINE_LIMIT
            )
            
            if not klines:
                logger.warning("❌ Не удалось получить данные с биржи")
                return None
            
            # Шаг 2: Анализируем спайки объёма
            logger.debug(f"🔍 Анализ {len(klines)} свечей на спайки объёма...")
            signal = self.volume_detector.analyze_volume_spike(klines, TRADING_PAIR)
            
            self.analysis_count += 1
            
            # Шаг 3: Если найден сигнал - отправляем уведомление
            if signal:
                logger.info(f"🎯 Обнаружен сигнал: {signal.message}")
                
                # Отправляем через Telegram (пока print)
                success = self.telegram_notifier.send_volume_signal(signal)
                if success:
                    self.signals_sent += 1
                    logger.info("📤 Сигнал успешно отправлен")
                else:
                    logger.error("❌ Ошибка при отправке сигнала")
                
                return signal
            else:
                logger.debug("✅ Аномалий не обнаружено")
                return None
                
        except Exception as e:
            logger.error(f"💥 Ошибка при анализе: {e}")
            return None
    
    def run_continuous_analysis(self, interval_seconds: int = 60):
        """
        Запуск непрерывного анализа с заданным интервалом
        
        Args:
            interval_seconds (int): Интервал между проверками в секундах
        """
        logger.info(f"🔄 Запуск непрерывного анализа с интервалом {interval_seconds} секунд")
        logger.info(f"📈 Отслеживаемая пара: {TRADING_PAIR}")
        
        # Отправляем уведомление о запуске
        self.telegram_notifier.send_startup_notification()
        
        try:
            while True:
                logger.info(f"🔄 Итерация анализа #{self.analysis_count + 1}")
                
                # Выполняем анализ
                signal = self.analyze_single_iteration()
                
                # Выводим статистику каждые 10 итераций
                if self.analysis_count % 10 == 0:
                    logger.info(f"📊 Статистика: выполнено {self.analysis_count} анализов, "
                              f"отправлено {self.signals_sent} сигналов")
                
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
        Выполнение одного анализа (для тестирования)
        """
        logger.info("🧪 Запуск одиночного анализа для тестирования...")
        
        signal = self.analyze_single_iteration()
        
        if signal:
            logger.info("✅ Тест завершён: сигнал обнаружен и отправлен")
        else:
            logger.info("✅ Тест завершён: аномалий не обнаружено")
        
        return signal
    
    def stop(self):
        """Остановка бота и освобождение ресурсов"""
        logger.info("🛑 Остановка бота...")
        
        # Закрываем соединения
        if hasattr(self.rest_client, 'close'):
            self.rest_client.close()
        
        # Выводим финальную статистику
        logger.info(f"📈 Финальная статистика:")
        logger.info(f"   • Выполнено анализов: {self.analysis_count}")
        logger.info(f"   • Отправлено сигналов: {self.signals_sent}")
        
        logger.info("👋 Бот остановлен")


def main():
    """
    Главная функция приложения
    """
    try:
        # Настраиваем логирование
        setup_main_logger()
        
        logger.info("🎯 Запуск бота анализа аномалий MEXC Futures")
        logger.info("💡 Для остановки нажмите Ctrl+C")
        
        # Создаём и запускаем бота
        bot = MexcAnalysisBot()
          # Можно выбрать режим работы:
        bot.run_single_analysis()  # Одиночный анализ для тестирования
        # bot.run_continuous_analysis(interval_seconds=60)  # Непрерывный анализ каждую минуту
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка запуска: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
