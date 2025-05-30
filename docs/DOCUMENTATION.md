# 📚 Мультипарный бот анализа аномалий MEXC Futures - Полная документация

## 📋 Содержание
- [⚡ Быстрый запуск](#-быстрый-запуск)
- [💾 Система базы данных](#-система-базы-данных)
- [🔧 Конфигурация](#-конфигурация)
- [📊 Использование API](#-использование-api)
- [🧪 Тестирование](#-тестирование)
- [📱 Telegram интеграция](#-telegram-интеграция)
- [🔍 Диагностика](#-диагностика)

---

## ⚡ Быстрый запуск

### 🎯 Готовые команды для запуска

#### 1️⃣ Основной бот (мониторинг):
```bash
cd "g:\Project_VSC\BotV2"
python run_bot.py
```

#### 2️⃣ Статистика базы данных:
```bash
python get_db_stats.py
```

#### 3️⃣ Демонстрация возможностей:
```bash
python demo_database.py      # 4 сценария использования БД
python demo_multiframe.py    # Мультипарный анализ
python demo_telegram_signals.py  # Telegram уведомления
```

#### 4️⃣ Тестирование системы:
```bash
python test_database.py      # Тесты БД и кэша
python test_integration_fixed.py   # Интеграционные тесты
python test_multiframe.py    # Тесты мультипарности
```

### 📊 Текущий статус системы

✅ **Завершено:**
- Мультипарный анализ (5 пар + 4 таймфрейма)
- Система write-back кэширования
- База данных SQLite для истории сигналов
- Telegram интеграция
- Полное покрытие тестами

✅ **Архитектура:**
- **Торговые пары**: BTC_USDT, ETH_USDT, BNB_USDT, ADA_USDT, SOL_USDT
- **Таймфреймы**: Min1, Min5, Min15, Min60
- **Детекторы**: Volume spike, OI spike, Price movement
- **Интеграции**: Telegram бот, SQLite БД, REST + WebSocket API

---

## 💾 Система базы данных

### 🏗️ Архитектура

Система построена на 4 уровнях:
1. **StoredSignal** (dataclass) - структура данных сигнала
2. **SignalsCache** - in-memory буфер с write-back кэшированием
3. **SignalsDatabase** - SQLite база данных
4. **SignalsManager** - единый интерфейс управления

### 📊 Структура таблицы signals

```sql
CREATE TABLE signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,           -- ISO время сигнала
    symbol TEXT NOT NULL,              -- Торговая пара (BTC_USDT)
    timeframe TEXT NOT NULL,           -- Таймфрейм (Min1, Min5, Min15, Min60)
    signal_type TEXT NOT NULL,         -- Тип сигнала (volume_spike, oi_spike, price_movement)
    price REAL NOT NULL,               -- Цена на момент сигнала
    volume REAL NOT NULL,              -- Объём за период
    open_interest REAL,                -- Открытый интерес (может быть NULL)
    change_percent REAL NOT NULL,      -- Изменение в процентах
    status TEXT DEFAULT 'active',     -- Статус сигнала
    notification_text TEXT            -- Текст уведомления
);

-- Индексы для быстрого поиска
CREATE INDEX idx_timestamp ON signals(timestamp);
CREATE INDEX idx_symbol ON signals(symbol);
CREATE INDEX idx_timeframe ON signals(timeframe);
CREATE INDEX idx_signal_type ON signals(signal_type);
```

### 🔧 Настройки кэширования

```python
# В src/config.py
CACHE_CONFIG = {
    'max_size': 100,           # Максимум записей в буфере
    'flush_interval': 300,     # Автосброс каждые 5 минут
    'auto_flush': True         # Включить автоматический сброс
}

DATABASE_CONFIG = {
    'db_path': 'signals_history.db',
    'enable_wal': True,        # Write-Ahead Logging для производительности
    'timeout': 30.0            # Таймаут подключения
}
```

### 📈 Использование API

```python
from src.data.database import SignalsManager

# Инициализация
signals_manager = SignalsManager()

# Сохранение сигнала
signal = StoredSignal(
    timestamp=datetime.now().isoformat(),
    symbol="BTC_USDT",
    timeframe="Min5",
    signal_type="volume_spike",
    price=45000.0,
    volume=1500000.0,
    open_interest=850000.0,
    change_percent=2.5,
    status="active",
    notification_text="🚀 Volume Spike: BTC_USDT +2.5%"
)
signals_manager.save_signal(signal)

# Получение истории
history = signals_manager.get_signals_history(
    symbol="BTC_USDT",
    timeframe="Min5",
    hours=24
)

# Экспорт в CSV
exported_file = signals_manager.export_signals_history(
    symbol="BTC_USDT",
    timeframe="Min5", 
    hours=168  # Неделя
)
```

---

## 🔧 Конфигурация

### 📁 Файл .env
```bash
# Telegram настройки
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# API настройки MEXC
MEXC_API_KEY=your_api_key
MEXC_SECRET_KEY=your_secret_key

# Настройки логирования
LOG_LEVEL=INFO
LOG_FILE=bot.log
```

### ⚙️ Основные настройки (src/config.py)

```python
# Торговые пары для мониторинга
SYMBOLS = ["BTC_USDT", "ETH_USDT", "BNB_USDT", "ADA_USDT", "SOL_USDT"]

# Таймфреймы для анализа
TIMEFRAMES = ["Min1", "Min5", "Min15", "Min60"]

# Пороги для детекции аномалий
VOLUME_SPIKE_THRESHOLD = 2.0      # Скачок объёма в 2+ раза
OI_SPIKE_THRESHOLD = 1.5          # Скачок OI в 1.5+ раза  
PRICE_MOVEMENT_THRESHOLD = 1.0    # Движение цены 1%+

# Telegram уведомления
TELEGRAM_CONFIG = {
    'enabled': True,
    'parse_mode': 'HTML',
    'disable_web_page_preview': True
}
```

---

## 📊 Использование основного бота

### 🚀 Запуск мониторинга

```python
# run_bot.py
from src.main import MexcAnalysisBot

# Создание и запуск бота
bot = MexcAnalysisBot()
bot.run_continuous_monitoring()
```

### 📱 Методы бота

```python
# Получение текущих данных
current_data = bot.get_current_market_data("BTC_USDT", "Min5")

# Анализ всех пар
analysis_results = bot.analyze_all_pairs()

# Получение истории сигналов
history = bot.get_signals_history("BTC_USDT", "Min5", hours=24)

# Экспорт данных
export_file = bot.export_signals_history("BTC_USDT", hours=168)

# Статистика базы данных
bot.print_database_statistics()
```

---

## 🧪 Тестирование

### 🔬 Основные тесты

#### test_database.py
- ✅ Тест основных операций БД
- ✅ Тест системы кэширования  
- ✅ Тест экспорта в CSV
- ✅ Тест производительности (2300+ сигналов/сек)

#### test_integration_fixed.py
- ✅ Интеграция БД с основным ботом
- ✅ Автоматическое сохранение сигналов
- ✅ Мультипарный анализ с сохранением

#### test_multiframe.py
- ✅ Анализ нескольких таймфреймов
- ✅ Корректность детекции аномалий
- ✅ Производительность мультипарного анализа

### 📊 Ожидаемые результаты тестов

```bash
🧪 === ТЕСТ 1: ОСНОВНЫЕ ОПЕРАЦИИ БД ===
✅ Основные операции БД пройдены успешно

🧪 === ТЕСТ 2: СИСТЕМА КЭШИРОВАНИЯ ===
✅ Тест кэширования пройден успешно

🧪 === ТЕСТ 4: ПРОИЗВОДИТЕЛЬНОСТЬ ===
⚡ Производительность: 2300+ сигналов/сек
✅ Тест производительности пройден
```

---

## 📱 Telegram интеграция

### 🤖 Настройка бота

1. Создайте бота через @BotFather
2. Получите токен бота
3. Найдите ID чата
4. Добавьте в `.env` файл

### 📨 Примеры уведомлений

```python
# В src/telegram/bot.py
from src.telegram.bot import TelegramBot

telegram_bot = TelegramBot()

# Отправка сигнала
await telegram_bot.send_signal_notification({
    'symbol': 'BTC_USDT',
    'timeframe': 'Min5',
    'signal_type': 'volume_spike',
    'price': 45000.0,
    'change_percent': 2.5
})

# Отправка отчёта
await telegram_bot.send_daily_report()
```

### 📋 Формат уведомлений

```
🚀 VOLUME SPIKE DETECTED
💰 BTC_USDT | ⏰ Min5
📈 Price: $45,000.00 (+2.5%)
📊 Volume: 1,500,000 USDT
🔥 OI: 850,000 USDT
⏱️ 2025-05-30 15:30:00
```

---

## 🔍 Диагностика

### 🛠️ Проверка системы

```bash
# Полная проверка всех компонентов
python -c "
import sys
sys.path.append('g:/Project_VSC/BotV2')
from src.data.database import SignalsManager
manager = SignalsManager()
print('✅ База данных инициализирована')
manager.print_statistics()
"
```

### ❌ Решение проблем

#### Ошибки импорта:
```bash
# Windows PowerShell
$env:PYTHONPATH = "g:\Project_VSC\BotV2"
```

#### Ошибки БД:
```bash
# Пересоздание БД
del signals_history.db
python get_db_stats.py
```

#### Очистка кэша:
```bash
Get-ChildItem -Recurse -Name "__pycache__" | ForEach-Object { Remove-Item $_ -Recurse -Force }
```

---

## 📊 Статистика использования

### 💾 Размер данных
- База данных: ~45 KB (30+ сигналов)
- Кэш в памяти: до 100 записей
- Автосброс: каждые 5 минут

### ⚡ Производительность
- Запись сигналов: 2300+ ops/sec
- Чтение истории: мгновенно (индексы)
- Экспорт CSV: ~1 сек/1000 записей

### 🎯 Покрытие
- 5 торговых пар
- 4 таймфрейма
- 3 типа детекторов
- 100% покрытие тестами

---

*Создано: 30 мая 2025*  
*Система готова к продакшену! 🚀*
