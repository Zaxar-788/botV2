"""
Конфигурация проекта и настройки для анализа аномалий на MEXC Futures
Поддержка мультипарности и мульти-таймфрейм анализа
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройки для торговых пар - поддержка нескольких пар
TRADING_PAIRS = [
    "BTC_USDT",
    "ETH_USDT", 
    "BNB_USDT",
    "ADA_USDT",
    "SOL_USDT"
]

# Настройки для таймфреймов - поддержка нескольких интервалов
TIMEFRAMES = [
    "Min1",   # 1 минута
    "Min5",   # 5 минут  
    "Min15",  # 15 минут
    "Min60"   # 60 минут (1 час)
]

# Настройки для получения данных
MEXC_API_BASE_URL = "https://contract.mexc.com/api/v1"
KLINE_LIMIT = 50  # Количество свечей для анализа

# Настройки для фетчера торговых пар
PAIRS_FETCHER_CONFIG = {
    "update_interval": 3600,      # Интервал обновления списка пар в секундах (1 час)
    "request_timeout": 30,        # Таймаут запросов к API в секундах
    "max_retries": 3,            # Максимальное количество повторных попыток
    "retry_delay": 5,            # Задержка между повторными попытками в секундах
    "cache_size_limit": 1000,    # Максимальное количество пар в кэше
    "enable_auto_update": True,   # Автоматическое обновление в фоновом режиме
    "filter_inactive": True,     # Фильтровать неактивные пары
    "min_volume_threshold": "0"  # Минимальный порог объёма для фильтрации
}

# Настройки детектора спайков объёма
VOLUME_SPIKE_THRESHOLD = 2.0  # Во сколько раз объём должен превышать средний
VOLUME_ANALYSIS_WINDOW = 10   # Количество свечей для расчёта среднего объёма

# Настройки для разных таймфреймов
TIMEFRAME_CONFIGS = {
    "Min1": {
        "limit": 50,
        "window": 10,
        "threshold": 2.0,
        "description": "1-минутные свечи"
    },
    "Min5": {
        "limit": 40,
        "window": 8,
        "threshold": 2.2,
        "description": "5-минутные свечи"
    },
    "Min15": {
        "limit": 30,
        "window": 6,
        "threshold": 2.5,
        "description": "15-минутные свечи"
    },    "Min60": {
        "limit": 24,
        "window": 5,
        "threshold": 3.0,
        "description": "60-минутные свечи (1 час)"
    }
}

# Настройки для Telegram (из переменных окружения)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Настройки логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Настройки базы данных для хранения истории сигналов
DATABASE_CONFIG = {
    "type": "sqlite",  # sqlite или postgresql
    "path": "signals_history.db",  # Путь к SQLite файлу
    # Для PostgreSQL (если нужно в будущем):
    # "host": os.getenv("DB_HOST", "localhost"),
    # "port": os.getenv("DB_PORT", 5432),
    # "database": os.getenv("DB_NAME", "mexc_signals"),
    # "user": os.getenv("DB_USER", ""),
    # "password": os.getenv("DB_PASSWORD", "")
}

# Настройки write-back кэша для сигналов
CACHE_CONFIG = {
    "buffer_size": 100,      # Максимальный размер буфера перед сбросом в БД
    "flush_interval": 300,   # Интервал принудительного сброса в секундах (5 минут)
    "batch_size": 50,        # Размер пакета для записи в БД
    "enable_cache": True     # Включение/выключение кэширования
}

# Настройки WebSocket для real-time анализа
WEBSOCKET_CONFIG = {
    "enabled": True,                    # Включение/выключение WebSocket анализа
    "base_url": "wss://contract.mexc.com/ws",
    "max_connections": 10,              # Максимальное количество одновременных соединений
    "max_subscriptions_per_connection": 100,  # Лимит MEXC на подписки на соединение
    "ping_interval": 30,                # Интервал ping в секундах
    "reconnect_delay": 5,               # Базовая задержка переподключения
    "max_reconnect_attempts": 10,       # Максимальное количество попыток переподключения
    "message_timeout": 60,              # Таймаут ожидания сообщений
    "subscription_types": [             # Типы данных для подписки
        "ticker",           # Данные тикера
        "kline_Min1",       # 1-минутные свечи
        "kline_Min5",       # 5-минутные свечи  
        "kline_Min15",      # 15-минутные свечи
        "kline_Min60"       # 1-часовые свечи
    ],
    "enable_real_time_analysis": True,  # Включить real-time анализ входящих данных
    "real_time_volume_threshold": 1.5,  # Порог для real-time анализа спайков объёма
    "buffer_size": 1000,                # Размер буфера для входящих сообщений
    "connection_health_check_interval": 60  # Интервал проверки здоровья соединений
}
