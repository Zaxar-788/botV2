"""
Telegram бот для отправки уведомлений о торговых сигналах
Поддержка мультипарности и мульти-таймфрейм анализа
"""

import logging
import requests
from typing import Optional, List, Union
from datetime import datetime
from src.signals.detector import VolumeSignal
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TRADING_PAIRS, TIMEFRAMES

# Настройка логгера
logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Класс для отправки уведомлений в Telegram
    
    Поддерживает отправку сигналов для множественных пар и таймфреймов.
    Включает профессиональное оформление сообщений с HTML-разметкой и inline-кнопками.
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
    
    def send_professional_signal(self, 
                                token: str, 
                                chat_id: Union[str, int], 
                                coin: str,
                                timeframe: str, 
                                signal_type: str,
                                price: float,
                                volume: float,
                                oi: Optional[float] = None,
                                change_percent: Optional[float] = None,
                                coin_url: Optional[str] = None,
                                comment: Optional[str] = None) -> bool:
        """
        Отправка профессионально оформленного торгового сигнала в Telegram
        
        Args:
            token (str): Токен Telegram бота
            chat_id (Union[str, int]): ID чата для отправки
            coin (str): Название монеты (например: BTC_USDT)
            timeframe (str): Таймфрейм (например: 1m)
            signal_type (str): Тип сигнала (pump/dump/long/short/alert)
            price (float): Цена
            volume (float): Объём
            oi (Optional[float]): Open Interest (опционально)
            change_percent (Optional[float]): Изменение за период в процентах
            coin_url (Optional[str]): Ссылка на монету на MEXC
            comment (Optional[str]): Дополнительный комментарий
            
        Returns:
            bool: True если сообщение отправлено успешно, False иначе
        """
        try:
            # Определяем emoji и стиль по типу сигнала
            signal_config = {
                'pump': {'emoji': '🚀', 'color': '🟢', 'name': 'ПАМП'},
                'dump': {'emoji': '💥', 'color': '🔴', 'name': 'ДАМП'},
                'long': {'emoji': '🟢', 'color': '🟢', 'name': 'ЛОНГ'},
                'short': {'emoji': '🔴', 'color': '🔴', 'name': 'ШОРТ'},
                'alert': {'emoji': '⚡️', 'color': '🟡', 'name': 'АЛЕРТ'}
            }
            
            config = signal_config.get(signal_type.lower(), signal_config['alert'])
            
            # Формируем ссылку на монету, если не передана
            if not coin_url:
                coin_url = f"https://futures.mexc.com/exchange/{coin}"
            
            # Формируем основное сообщение
            message = f"{config['emoji']} <b>{config['name']} СИГНАЛ</b>\n\n"
            
            # Добавляем информацию о монете с кликабельной ссылкой
            message += f"💰 Монета: <a href='{coin_url}'>{coin}</a> <code>{coin}</code>\n"
            
            # Добавляем основные параметры
            message += f"⏰ Таймфрейм: <b>{timeframe}</b>\n"
            message += f"💵 Цена: <b>${price:,.4f}</b>\n"
            message += f"📊 Объём: <b>{volume:,.0f}</b>\n"
            
            # Добавляем OI если передан
            if oi is not None:
                message += f"🔄 OI: <b>{oi:,.0f}</b>\n"
            
            # Добавляем изменение за период если передано
            if change_percent is not None:
                change_emoji = "📈" if change_percent > 0 else "📉"
                sign = "+" if change_percent > 0 else ""
                message += f"{change_emoji} Изменение: <b>{sign}{change_percent:.2f}%</b>\n"
            
            # Добавляем временную метку
            current_time = datetime.now().strftime("%H:%M:%S")
            message += f"🕐 Время: <b>{current_time}</b>\n"
            
            # Добавляем комментарий если есть
            if comment:
                message += f"\n💬 <i>{comment}</i>\n"
            
            # Формируем inline клавиатуру с кнопкой
            reply_markup = {
                "inline_keyboard": [[
                    {
                        "text": f"📈 Открыть {coin} на MEXC",
                        "url": coin_url
                    }
                ]]
            }
            
            # Отправляем сообщение через Telegram Bot API
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
                "reply_markup": reply_markup
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("ok"):
                logger.info(f"Профессиональный сигнал отправлен: {coin} ({timeframe}) - {signal_type.upper()}")
                return True
            else:
                logger.error(f"Ошибка Telegram API: {result.get('description', 'Неизвестная ошибка')}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при отправке HTTP запроса в Telegram: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при отправке профессионального сигнала: {e}")
            return False
    
    def send_volume_signal(self, signal: VolumeSignal) -> bool:
        """
        Отправка сигнала о спайке объёма с использованием профессионального оформления
        
        Args:
            signal (VolumeSignal): Объект сигнала для отправки
            
        Returns:
            bool: True если сообщение отправлено успешно, False иначе
        """
        if not self.is_enabled:
            # Fallback: выводим в консоль если Telegram не настроен
            timestamp_str = datetime.fromtimestamp(signal.timestamp / 1000).strftime("%H:%M:%S")
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
            print("=" * 60)
            print("📨 TELEGRAM УВЕДОМЛЕНИЕ:")
            print(message)
            print("=" * 60)
            
            logger.info(f"Сигнал отправлен для {signal.pair} ({signal.timeframe}): {signal.spike_ratio:.1f}x спайк объёма")
            return True
        
        try:
            # Определяем тип сигнала на основе спайка объёма
            if signal.spike_ratio >= 5.0:
                signal_type = "pump" if signal.price > 0 else "alert"
            elif signal.spike_ratio >= 3.0:
                signal_type = "alert"
            else:
                signal_type = "alert"
            
            # Формируем комментарий
            comment = f"Спайк объёма {signal.spike_ratio:.1f}x от среднего значения. {signal.message}"
            
            # Отправляем через новую функцию профессионального оформления
            return self.send_professional_signal(
                token=self.bot_token,
                chat_id=self.chat_id,
                coin=signal.pair,
                timeframe=signal.timeframe,
                signal_type=signal_type,
                price=signal.price,
                volume=signal.current_volume,
                change_percent=None,  # Можно добавить расчет изменения цены
                comment=comment
            )
            
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
