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
