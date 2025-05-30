"""
Тестирование системы базы данных и кэша сигналов
Проверка write-back caching и сохранения в SQLite
"""

import time
import logging
from datetime import datetime, timezone
from src.utils.logger import setup_main_logger
from src.data.database import SignalsManager, StoredSignal
from src.signals.detector import VolumeSignal
from src.config import DATABASE_CONFIG, CACHE_CONFIG

# Настройка логгера
logger = logging.getLogger(__name__)


def create_test_signal(pair: str, timeframe: str, spike_ratio: float) -> VolumeSignal:
    """
    Создание тестового сигнала для проверки
    
    Args:
        pair (str): Торговая пара
        timeframe (str): Таймфрейм
        spike_ratio (float): Коэффициент спайка
        
    Returns:
        VolumeSignal: Тестовый сигнал
    """
    timestamp = int(time.time() * 1000)  # Текущее время в миллисекундах
    current_volume = 1000.0 * spike_ratio
    average_volume = 1000.0
    price = 50000.0  # Примерная цена BTC
    
    message = f"🧪 ТЕСТОВЫЙ СИГНАЛ! {pair} ({timeframe}): объём превышен в {spike_ratio:.1f}x"
    
    return VolumeSignal(
        timestamp=timestamp,
        pair=pair,
        timeframe=timeframe,
        current_volume=current_volume,
        average_volume=average_volume,
        spike_ratio=spike_ratio,
        price=price,
        message=message
    )


def test_database_basic():
    """Базовый тест базы данных без кэша"""
    logger.info("🧪 === ТЕСТ 1: БАЗОВЫЕ ОПЕРАЦИИ С БД ===")
    
    try:
        # Создаем менеджер с отключенным кэшем
        test_cache_config = CACHE_CONFIG.copy()
        test_cache_config['enable_cache'] = False
        
        manager = SignalsManager(DATABASE_CONFIG, test_cache_config)
        
        # Создаем тестовые сигналы
        signals = [
            create_test_signal("BTC_USDT", "Min1", 2.5),
            create_test_signal("ETH_USDT", "Min5", 3.2),
            create_test_signal("BNB_USDT", "Min15", 2.8)
        ]
        
        # Сохраняем сигналы (должны идти напрямую в БД)
        logger.info("💾 Сохранение тестовых сигналов...")
        for i, signal in enumerate(signals):
            manager.save_signal(signal)
            logger.info(f"   ✅ Сигнал {i+1}/3 сохранен: {signal.pair} ({signal.timeframe})")
        
        # Проверяем статистику
        stats = manager.get_full_statistics()
        db_stats = stats['database']
        
        logger.info(f"📊 Статистика БД: {db_stats['total_signals']} сигналов")
        logger.info(f"📈 По парам: {db_stats['by_pairs']}")
        logger.info(f"⏰ По таймфреймам: {db_stats['by_timeframes']}")
        
        # Получаем историю
        history = manager.get_signals_history(limit=10)
        logger.info(f"📜 Получено из истории: {len(history)} сигналов")
        
        for signal in history[-3:]:  # Последние 3
            logger.info(f"   🔍 {signal['pair']} ({signal['timeframe']}): "
                       f"спайк {signal['spike_ratio']:.1f}x")
        
        manager.close()
        logger.info("✅ Тест базы данных пройден успешно")
        
    except Exception as e:
        logger.error(f"❌ Ошибка теста БД: {e}")
        raise


def test_cache_system():
    """Тест системы кэширования"""
    logger.info("🧪 === ТЕСТ 2: СИСТЕМА КЭШИРОВАНИЯ ===")
    
    try:
        # Создаем менеджер с маленьким буфером для тестирования
        test_cache_config = {
            'enable_cache': True,
            'buffer_size': 3,  # Маленький буфер для быстрого тестирования
            'flush_interval': 5,  # 5 секунд
            'batch_size': 2
        }
        
        manager = SignalsManager(DATABASE_CONFIG, test_cache_config)
        
        # Проверяем начальное состояние кэша
        cache_stats = manager.get_full_statistics()['cache']
        logger.info(f"🗂️ Начальное состояние кэша: {cache_stats['buffer_size']}/{cache_stats['max_buffer_size']}")
        
        # Добавляем сигналы в кэш
        logger.info("➕ Добавление сигналов в кэш...")
        test_signals = [
            create_test_signal("ADA_USDT", "Min1", 2.1),
            create_test_signal("SOL_USDT", "Min5", 2.4),
            create_test_signal("DOT_USDT", "Min15", 2.7),
            create_test_signal("LINK_USDT", "Min60", 3.1),  # Этот должен вызвать принудительный сброс
        ]
        
        for i, signal in enumerate(test_signals):
            manager.save_signal(signal)
            cache_size = manager.cache.get_buffer_size()
            logger.info(f"   📝 Сигнал {i+1}: {signal.pair}, буфер: {cache_size}")
            
            if cache_size == 0 and i < len(test_signals) - 1:
                logger.info("   🔄 Буфер сброшен автоматически!")
        
        # Проверяем финальное состояние
        final_stats = manager.get_full_statistics()
        cache_stats = final_stats['cache']
        db_stats = final_stats['database']
        
        logger.info(f"📊 Финальная статистика:")
        logger.info(f"   🗂️ Кэш: {cache_stats['buffer_size']}/{cache_stats['max_buffer_size']}")
        logger.info(f"   💾 БД: {db_stats['total_signals']} сигналов")
        
        # Принудительный сброс оставшихся данных
        logger.info("🔄 Принудительный сброс кэша...")
        manager.cache.flush_buffer()
        
        final_cache_size = manager.cache.get_buffer_size()
        logger.info(f"   🗂️ Размер буфера после сброса: {final_cache_size}")
        
        manager.close()
        logger.info("✅ Тест кэширования пройден успешно")
        
    except Exception as e:
        logger.error(f"❌ Ошибка теста кэширования: {e}")
        raise


def test_export_functionality():
    """Тест функции экспорта"""
    logger.info("🧪 === ТЕСТ 3: ЭКСПОРТ ДАННЫХ ===")
    
    try:
        manager = SignalsManager(DATABASE_CONFIG, CACHE_CONFIG)
        
        # Экспортируем все сигналы
        export_file = "test_signals_export.csv"
        success = manager.export_signals(export_file, limit=100)
        
        if success:
            logger.info(f"📁 Экспорт выполнен успешно: {export_file}")
            
            # Проверяем размер файла
            import os
            if os.path.exists(export_file):
                size = os.path.getsize(export_file)
                logger.info(f"   📏 Размер файла: {size} байт")
                
                # Читаем несколько строк для проверки
                with open(export_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:5]  # Первые 5 строк
                    logger.info(f"   📄 Содержимое (первые строки):")
                    for i, line in enumerate(lines):
                        logger.info(f"      {i+1}: {line.strip()[:100]}...")
            else:
                logger.warning("⚠️ Файл экспорта не найден")
        else:
            logger.warning("⚠️ Экспорт не выполнен (возможно, нет данных)")
        
        manager.close()
        logger.info("✅ Тест экспорта завершен")
        
    except Exception as e:
        logger.error(f"❌ Ошибка теста экспорта: {e}")
        raise


def test_performance():
    """Тест производительности системы"""
    logger.info("🧪 === ТЕСТ 4: ПРОИЗВОДИТЕЛЬНОСТЬ ===")
    
    try:
        # Тест с большим количеством сигналов
        test_cache_config = {
            'enable_cache': True,
            'buffer_size': 50,
            'flush_interval': 10,
            'batch_size': 20
        }
        
        manager = SignalsManager(DATABASE_CONFIG, test_cache_config)
        
        # Генерируем много тестовых сигналов
        pairs = ["BTC_USDT", "ETH_USDT", "BNB_USDT", "ADA_USDT", "SOL_USDT"]
        timeframes = ["Min1", "Min5", "Min15", "Min60"]
        
        logger.info("⚡ Генерация большого количества сигналов...")
        start_time = time.time()
        
        signal_count = 0
        for pair in pairs:
            for timeframe in timeframes:
                for i in range(10):  # 10 сигналов на комбинацию
                    spike_ratio = 2.0 + (i * 0.2)  # От 2.0 до 3.8
                    signal = create_test_signal(pair, timeframe, spike_ratio)
                    manager.save_signal(signal)
                    signal_count += 1
        
        generation_time = time.time() - start_time
        logger.info(f"   📊 Сгенерировано {signal_count} сигналов за {generation_time:.2f} сек")
        logger.info(f"   ⚡ Скорость: {signal_count/generation_time:.1f} сигналов/сек")
        
        # Проверяем состояние кэша
        cache_stats = manager.get_full_statistics()['cache']
        logger.info(f"   🗂️ Кэш: {cache_stats['buffer_size']}/{cache_stats['max_buffer_size']}")
        
        # Финальный сброс и проверка
        logger.info("🔄 Финальный сброс кэша...")
        flush_start = time.time()
        manager.cache.flush_buffer()
        flush_time = time.time() - flush_start
        
        final_stats = manager.get_full_statistics()['database']
        logger.info(f"   💾 Сброс за {flush_time:.2f} сек")
        logger.info(f"   📊 Итого в БД: {final_stats['total_signals']} сигналов")
        
        manager.close()
        logger.info("✅ Тест производительности завершен")
        
    except Exception as e:
        logger.error(f"❌ Ошибка теста производительности: {e}")
        raise


def main():
    """Главная функция тестирования"""
    try:
        # Настраиваем логирование
        setup_main_logger()
        
        logger.info("🚀 === ТЕСТИРОВАНИЕ СИСТЕМЫ БД И КЭША ===")
        logger.info(f"🗂️ Конфигурация БД: {DATABASE_CONFIG}")
        logger.info(f"⚙️ Конфигурация кэша: {CACHE_CONFIG}")
        
        # Запускаем тесты
        test_database_basic()
        print()  # Разделитель в консоли
        
        test_cache_system()
        print()
        
        test_export_functionality()
        print()
        
        test_performance()
        print()
        
        logger.info("🎉 === ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО ===")
        logger.info("💡 Система базы данных и кэша готова к использованию!")
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка тестирования: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
