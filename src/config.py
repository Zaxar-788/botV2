"""
Конфигурация проекта и настройки для анализа аномалий на MEXC Futures
"""

# Настройки для торговой пары
TRADING_PAIR = "BTC_USDT"

# Настройки для получения данных
MEXC_API_BASE_URL = "https://contract.mexc.com/api/v1"
KLINE_INTERVAL = "Min1"  # Минутные свечи
KLINE_LIMIT = 50  # Количество свечей для анализа

# Настройки детектора спайков объёма
VOLUME_SPIKE_THRESHOLD = 2.0  # Во сколько раз объём должен превышать средний
VOLUME_ANALYSIS_WINDOW = 10   # Количество свечей для расчёта среднего объёма (уменьшено для MVP)

# Настройки для Telegram (TODO: добавить токен в .env)
TELEGRAM_BOT_TOKEN = ""  # Будет загружаться из .env
TELEGRAM_CHAT_ID = ""    # Будет загружаться из .env

# Настройки логирования
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
