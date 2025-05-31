# WebSocket Real-Time Analysis Integration

## Обзор

Комплексное WebSocket решение для real-time анализа всех 750+ контрактных пар MEXC Futures, интегрированное с существующим асинхронным ботом.

## Архитектура

### Dual-Mode Analysis System

Система поддерживает два режима работы:

1. **REST API Mode** (существующий) - периодический анализ через REST API
2. **WebSocket Mode** (новый) - real-time анализ через WebSocket подключения
3. **Dual Mode** - одновременная работа обоих режимов

### Компоненты

#### 1. MexcWebSocketClient (`src/data/ws_client.py`)

Основной WebSocket клиент с возможностями:

- **Автоматическая балансировка нагрузки**: Распределение подписок между соединениями
- **Лимиты MEXC**: До 100 подписок на соединение
- **Fault-tolerance**: Автопереподключение с экспоненциальной задержкой
- **Изоляция ошибок**: Сбой одного соединения не влияет на другие
- **Динамические подписки**: Добавление/удаление пар без перезапуска

#### 2. WebSocket Integration в AsyncMexcAnalysisBot

Расширение основного бота для поддержки WebSocket:

```python
bot = AsyncMexcAnalysisBot(
    timeframes=['Min1', 'Min5', 'Min15'],
    analysis_interval=60,
    enable_websocket=True  # Включить WebSocket режим
)
```

#### 3. Real-Time Event Handlers

Обработчики для различных типов WebSocket сообщений:

- `_handle_kline_message()` - обработка данных свечей
- `_handle_ticker_message()` - обработка данных тикера
- `_handle_deals_message()` - обработка данных сделок

## Конфигурация

### WebSocket настройки (`src/config.py`)

```python
WEBSOCKET_CONFIG = {
    "enabled": True,                    # Включение WebSocket
    "base_url": "wss://contract.mexc.com/ws",
    "max_connections": 10,              # Макс. количество соединений
    "max_subscriptions_per_connection": 100,  # Лимит MEXC
    "ping_interval": 30,                # Интервал ping
    "reconnect_delay": 5,               # Задержка переподключения
    "max_reconnect_attempts": 10,       # Макс. попыток переподключения
    "subscription_types": [             # Типы подписок
        "ticker",
        "kline_Min1",
        "kline_Min5",
        "kline_Min15",
        "kline_Min60"
    ],
    "enable_real_time_analysis": True,  # Real-time анализ
    "real_time_volume_threshold": 1.5   # Порог для RT анализа
}
```

## Использование

### 1. Базовый запуск с WebSocket

```python
import asyncio
from src.main import AsyncMexcAnalysisBot

async def main():
    bot = AsyncMexcAnalysisBot(
        timeframes=['Min1', 'Min5'],
        enable_websocket=True
    )
    await bot.run_async()

asyncio.run(main())
```

### 2. Только WebSocket режим

```python
from src.data.ws_client import create_websocket_client
from src.data.pairs_fetcher import get_pairs_fetcher

async def message_handler(message):
    print(f"Получено: {message.channel} для {message.symbol}")

pairs_fetcher = get_pairs_fetcher()
ws_client = create_websocket_client(
    pairs_fetcher=pairs_fetcher,
    message_handler=message_handler,
    subscription_types=['ticker', 'kline_Min1']
)

await ws_client.start()
```

### 3. Кастомная обработка сообщений

```python
class CustomAnalyzer:
    async def handle_message(self, message):
        if message.channel == 'kline_Min1':
            volume = float(message.data.get('v', 0))
            if volume > threshold:
                await self.process_volume_spike(message.symbol, volume)
        
    async def process_volume_spike(self, symbol, volume):
        # Кастомная логика обработки спайка объёма
        print(f"Спайк объёма в {symbol}: {volume}")
```

## Масштабирование

### Лимиты MEXC

- **Максимум 100 подписок на WebSocket соединение**
- **Максимум 10 одновременных соединений с одного IP**
- **Rate limits на подключения**

### Стратегии масштабирования

#### 1. Горизонтальное масштабирование

```python
# Конфигурация для большого количества пар
WEBSOCKET_CONFIG = {
    "max_connections": 8,  # Используем 8 из 10 доступных
    "max_subscriptions_per_connection": 95,  # Оставляем запас
}

# Для 750+ пар потребуется: 750 / 95 ≈ 8 соединений
```

#### 2. Приоритизация пар

```python
# Подписка только на топ-пары по объёму
priority_pairs = get_top_volume_pairs(limit=500)
```

#### 3. Селективные подписки

```python
# Подписка только на нужные типы данных
subscription_types = ['ticker', 'kline_Min1']  # Только тикер и 1m свечи
```

### Мониторинг производительности

#### ConnectionMetrics

```python
# Метрики каждого соединения
metrics = ws_client.get_connection_metrics()
for conn_id, metrics in metrics.items():
    print(f"Соединение {conn_id}:")
    print(f"  Сообщений получено: {metrics.messages_received}")
    print(f"  Подписок: {metrics.subscriptions_count}")
    print(f"  Здоровье: {metrics.is_healthy}")
```

#### Health Checks

```python
# Проверка здоровья соединений
health_status = await ws_client.check_health()
if not health_status['all_healthy']:
    # Restart unhealthy connections
    await ws_client.restart_unhealthy_connections()
```

## Тестирование

### Unit Tests

```bash
# Запуск WebSocket тестов
python test_websocket_integration.py
```

### Integration Tests

```bash
# Полное тестирование с реальными подключениями
python demo_ws_client.py --mode full --duration 60
```

### Load Testing

```bash
# Тестирование нагрузки
python demo_ws_client.py --pairs 100 --connections 5
```

## Мониторинг и логирование

### Логирование

```python
# Настройка детального логирования WebSocket
logging.getLogger('src.data.ws_client').setLevel(logging.DEBUG)
```

### Метрики

- Количество активных соединений
- Количество подписок на соединение
- Частота получения сообщений
- Количество переподключений
- Ошибки и таймауты

### Алерты

- Потеря соединения с биржей
- Превышение лимитов подписок
- Высокая частота ошибок
- Задержки в получении данных

## Troubleshooting

### Частые проблемы

#### 1. Connection Limit Exceeded

```
Ошибка: Too many connections
Решение: Уменьшить max_connections в конфигурации
```

#### 2. Subscription Limit Exceeded

```
Ошибка: Subscription limit exceeded
Решение: Проверить количество подписок на соединение
```

#### 3. High Reconnection Rate

```
Проблема: Частые переподключения
Причины: Нестабильное соединение, превышение лимитов
Решение: Увеличить reconnect_delay, проверить network
```

### Диагностика

```python
# Получение статистики WebSocket клиента
stats = ws_client.get_statistics()
print(f"Активных соединений: {stats['active_connections']}")
print(f"Всего подписок: {stats['total_subscriptions']}")
print(f"Сообщений в минуту: {stats['messages_per_minute']}")
```

## Roadmap

### Ближайшие улучшения

1. **Intelligent Load Balancing** - умное распределение пар по соединениям
2. **Advanced Filtering** - фильтрация пар по объёму и активности
3. **Circuit Breaker Pattern** - защита от каскадных сбоев
4. **Metrics Dashboard** - веб-интерфейс для мониторинга

### Долгосрочные планы

1. **Multi-Exchange Support** - поддержка других бирж
2. **ML Integration** - машинное обучение для анализа
3. **Distributed Architecture** - распределённая архитектура
4. **Real-Time Alerts** - продвинутые алерты

## Заключение

WebSocket интеграция обеспечивает:

- ✅ **Real-time анализ** всех 750+ пар MEXC Futures
- ✅ **Автоматическая балансировка** нагрузки между соединениями  
- ✅ **Fault-tolerance** с автопереподключением
- ✅ **Изоляция ошибок** между парами
- ✅ **Динамическое управление** подписками
- ✅ **Полная интеграция** с существующим AsyncMexcAnalysisBot

Система готова к production использованию с поддержкой масштабирования до любого количества торговых пар в рамках лимитов MEXC.
