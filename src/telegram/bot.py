"""
Telegram бот для отправки уведомлений о торговых сигналах
Поддержка мультипарности и мульти-таймфрейм анализа
"""

import logging
from typing import Optional, List
from datetime import datetime
from src.signals.detector import VolumeSignal
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TRADING_PAIRS, TIMEFRAMES

# Настройка логгера
logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Класс для отправки уведомлений в Telegram
    
    Поддерживает отправку сигналов для множественных пар и таймфреймов.
    В текущей версии только выводит сигналы в консоль.
    TODO: Добавить реальную интеграцию с Telegram Bot API
    """
    
    def __init__(self, bot_token: str = TELEGRAM_BOT_TOKEN, chat_id: str = TELEGRAM_CHAT_ID):
        """
        Инициализация уведомителя
        
        Args:
            bot_token (str): Токен Telegram бота
            chat_id (str): ID чата для отправки сообщений
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.is_enabled = bool(bot_token and chat_id)
        
        if not self.is_enabled:
            logger.warning("Telegram уведомления отключены: не указан токен или chat_id")
        else:
            logger.info("Telegram уведомления настроены")
    
    def send_volume_signal(self, signal: VolumeSignal) -> bool:
        """
        Отправка сигнала о спайке объёма
        
        Args:
            signal (VolumeSignal): Объект сигнала для отправки
            
        Returns:
            bool: True если сообщение отправлено успешно, False иначе
        """
        try:
            # Форматируем временную метку
            timestamp_str = datetime.fromtimestamp(signal.timestamp / 1000).strftime("%H:%M:%S")
            # Формируем текст сообщения
            message = f"""
🚨 ОБНАРУЖЕН СПАЙК ОБЪЁМА!

📊 Пара: {signal.pair}
⏰ Таймфрейм: {signal.timeframe}
🕐 Время: {timestamp_str}
💰 Цена: ${signal.price:.2f}
📈 Объём: {signal.current_volume:.0f}
📊 Средний объём: {signal.average_volume:.0f}
🔥 Превышение: {signal.spike_ratio:.1f}x

{signal.message}
"""
            
            # TODO: Реализовать отправку через Telegram Bot API
            # Сейчас просто выводим в консоль
            print("=" * 60)
            print("📨 TELEGRAM УВЕДОМЛЕНИЕ:")
            print(message)
            print("=" * 60)
            
            logger.info(f"Сигнал отправлен для {signal.pair} ({signal.timeframe}): {signal.spike_ratio:.1f}x спайк объёма")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отправке Telegram сигнала: {e}")
            return False
    
    def send_multiple_signals(self, signals: List[VolumeSignal]) -> bool:
        """
        Отправка множественных сигналов одним сообщением
        
        Args:
            signals (List[VolumeSignal]): Список сигналов для отправки
            
        Returns:
            bool: True если сообщение отправлено успешно, False иначе
        """
        if not signals:
            return True
        
        try:
            # Группируем сигналы для компактного отображения
            message = f"""
🚨 ОБНАРУЖЕНО {len(signals)} СПАЙКОВ ОБЪЁМА!

"""
            
            for i, signal in enumerate(signals, 1):
                timestamp_str = datetime.fromtimestamp(signal.timestamp / 1000).strftime("%H:%M:%S")
                message += f"""
{i}. 📊 {signal.pair} ({signal.timeframe})
   🕐 {timestamp_str} | 💰 ${signal.price:.2f}
   🔥 Превышение: {signal.spike_ratio:.1f}x
   📈 Объём: {signal.current_volume:.0f} (средний: {signal.average_volume:.0f})

"""
            
            # TODO: Реализовать отправку через Telegram Bot API
            print("=" * 60)
            print("📨 TELEGRAM МАССОВОЕ УВЕДОМЛЕНИЕ:")
            print(message)
            print("=" * 60)
            
            logger.info(f"Отправлено массовое уведомление о {len(signals)} сигналах")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отправке массового уведомления: {e}")
            return False
    
    def send_custom_message(self, message: str) -> bool:
        """
        Отправка произвольного сообщения
        
        Args:
            message (str): Текст сообщения
            
        Returns:
            bool: True если сообщение отправлено успешно, False иначе
        """
        try:
            # TODO: Реализовать отправку через Telegram Bot API
            print("=" * 60)
            print("📨 TELEGRAM СООБЩЕНИЕ:")
            print(message)
            print("=" * 60)
            
            logger.info("Отправлено произвольное сообщение в Telegram")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
            return False
    
    def send_startup_notification(self) -> bool:
        """
        Отправка уведомления о запуске мультипарного бота
        
        Returns:
            bool: True если уведомление отправлено успешно, False иначе
        """
        startup_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        
        # Формируем список отслеживаемых пар и таймфреймов
        pairs_str = ", ".join(TRADING_PAIRS)
        timeframes_str = ", ".join(TIMEFRAMES)
        
        message = f"""
🤖 МУЛЬТИПАРНЫЙ БОТ АНАЛИЗА MEXC FUTURES ЗАПУЩЕН

⏰ Время запуска: {startup_time}
📊 Отслеживаемые пары: {pairs_str}
⏰ Таймфреймы: {timeframes_str}
🔍 Анализ: спайки объёма
📡 Статус: активен

Бот будет уведомлять о значительных аномалиях объёма торгов 
на всех отслеживаемых парах и таймфреймах.
"""
        return self.send_custom_message(message)


# TODO: Функции для будущей интеграции с Telegram Bot API
def _send_telegram_request(bot_token: str, method: str, data: dict) -> Optional[dict]:
    """
    Отправка запроса к Telegram Bot API (заготовка)
    
    Args:
        bot_token (str): Токен бота
        method (str): Метод API (например, 'sendMessage')
        data (dict): Данные для отправки
        
    Returns:
        dict: Ответ от API или None при ошибке
    """
    # TODO: Реализовать HTTP запрос к https://api.telegram.org/bot{token}/{method}
    pass


def _format_message_for_telegram(text: str) -> str:
    """
    Форматирование сообщения для Telegram (экранирование специальных символов)
    
    Args:
        text (str): Исходный текст
        
    Returns:
        str: Отформатированный текст
    """
    # TODO: Добавить экранирование для MarkdownV2 или HTML
    return text
