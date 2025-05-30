#!/usr/bin/env python3
"""
Финальный интеграционный тест для модуля pairs_fetcher.py
Проверяет полную функциональность с реальным API MEXC
"""

import sys
import os
import time
import logging
from datetime import datetime

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data.pairs_fetcher import MexcPairsFetcher, get_all_futures_pairs, get_pairs_fetcher
from src.utils.logger import setup_logger


def test_basic_functionality():
    """Базовый тест функциональности"""
    print("🔧 Тест 1: Базовая функциональность")
    
    # Тест получения всех пар
    pairs = get_all_futures_pairs(force_update=True)
    assert len(pairs) > 500, f"Ожидалось > 500 пар, получено: {len(pairs)}"
    print(f"  ✅ Получено {len(pairs)} торговых пар")
    
    # Тест глобального фетчера
    fetcher = get_pairs_fetcher()
    assert fetcher is not None, "Глобальный фетчер не создан"
    print("  ✅ Глобальный фетчер работает")
    
    return True


def test_filtering_capabilities():
    """Тест возможностей фильтрации"""
    print("🔍 Тест 2: Фильтрация пар")
    
    fetcher = MexcPairsFetcher()
    
    # Фильтрация по котируемой валюте
    usdt_pairs = fetcher.get_pairs_by_quote_coin('USDT')
    usd_pairs = fetcher.get_pairs_by_quote_coin('USD')
    btc_pairs = fetcher.get_pairs_by_quote_coin('BTC')
    
    assert len(usdt_pairs) > 500, f"USDT пар должно быть > 500, получено: {len(usdt_pairs)}"
    assert len(usd_pairs) > 0, f"USD пар должно быть > 0, получено: {len(usd_pairs)}"
    
    print(f"  ✅ USDT пары: {len(usdt_pairs)}")
    print(f"  ✅ USD пары: {len(usd_pairs)}")
    print(f"  ✅ BTC пары: {len(btc_pairs)}")
    
    # Фильтрация по базовой валюте
    btc_base_pairs = fetcher.get_pairs_by_base_coin('BTC')
    eth_base_pairs = fetcher.get_pairs_by_base_coin('ETH')
    
    print(f"  ✅ BTC базовые пары: {len(btc_base_pairs)}")
    print(f"  ✅ ETH базовые пары: {len(eth_base_pairs)}")
    
    return True


def test_detailed_info():
    """Тест детальной информации о парах"""
    print("📋 Тест 3: Детальная информация")
    
    fetcher = MexcPairsFetcher()
    usdt_pairs = fetcher.get_pairs_by_quote_coin('USDT')
    
    # Тестируем информацию о нескольких парах
    test_pairs = usdt_pairs[:5]
    valid_info_count = 0
    
    for pair in test_pairs:
        info = fetcher.get_pair_info(pair)
        if info:
            valid_info_count += 1
            assert info.symbol == pair, f"Символ не соответствует: {info.symbol} != {pair}"
            assert info.base_coin is not None, f"Базовая валюта не найдена для {pair}"
            assert info.quote_coin is not None, f"Котируемая валюта не найдена для {pair}"
            assert info.max_leverage > 0, f"Некорректное плечо для {pair}: {info.max_leverage}"
    
    assert valid_info_count >= 3, f"Недостаточно валидной информации: {valid_info_count}/5"
    print(f"  ✅ Получена валидная информация для {valid_info_count}/{len(test_pairs)} пар")
    
    return True


def test_performance():
    """Тест производительности"""
    print("⚡ Тест 4: Производительность")
    
    fetcher = MexcPairsFetcher()
    
    # Тест скорости с обновлением
    start_time = time.time()
    pairs_1 = fetcher.get_all_pairs(force_update=True)
    time_1 = time.time() - start_time
    
    # Тест скорости из кэша
    start_time = time.time()
    pairs_2 = fetcher.get_all_pairs(force_update=False)
    time_2 = time.time() - start_time
    
    assert len(pairs_1) == len(pairs_2), "Количество пар из кэша не совпадает"
    assert time_2 < time_1, "Кэш не ускоряет получение данных"
    
    speedup = time_1 / time_2 if time_2 > 0 else float('inf')
    
    print(f"  ✅ Время с обновлением: {time_1:.3f}s")
    print(f"  ✅ Время из кэша: {time_2:.3f}s")
    print(f"  ✅ Ускорение кэша: {speedup:.1f}x")
    
    assert speedup > 100, f"Ускорение кэша недостаточное: {speedup:.1f}x"
    
    return True


def test_auto_update():
    """Тест автоматического обновления"""
    print("🔄 Тест 5: Автоматическое обновление")
    
    fetcher = MexcPairsFetcher(update_interval=2)  # Обновление каждые 2 секунды
    
    # Запускаем автообновление
    fetcher.start_auto_update()
    
    cache_info = fetcher.get_cache_info()
    assert cache_info['auto_update_running'] == True, "Автообновление не запустилось"
    
    print("  ✅ Автообновление запущено")
    
    # Ждём немного
    time.sleep(3)
    
    # Останавливаем
    fetcher.stop_auto_update()
    
    cache_info = fetcher.get_cache_info()
    assert cache_info['auto_update_running'] == False, "Автообновление не остановилось"
    
    print("  ✅ Автообновление остановлено")
    
    return True


def test_error_handling():
    """Тест обработки ошибок"""
    print("🛡️ Тест 6: Обработка ошибок")
    
    fetcher = MexcPairsFetcher()
    
    # Тест с несуществующей парой
    info = fetcher.get_pair_info("NONEXISTENT_PAIR")
    assert info is None, "Должен возвращать None для несуществующей пары"
    
    # Тест фильтрации с несуществующей валютой
    empty_pairs = fetcher.get_pairs_by_quote_coin("NONEXISTENT")
    assert len(empty_pairs) == 0, "Должен возвращать пустой список для несуществующей валюты"
    
    print("  ✅ Обработка ошибок работает корректно")
    
    return True


def test_scalability():
    """Тест готовности к масштабированию"""
    print("📈 Тест 7: Готовность к масштабированию")
    
    fetcher = MexcPairsFetcher()
    all_pairs = fetcher.get_all_pairs()
    
    # Проверяем, что количество пар достаточное
    assert len(all_pairs) >= 750, f"Недостаточно пар для масштабирования: {len(all_pairs)}"
    
    # Тест обработки большого количества пар
    start_time = time.time()
    processed = 0
    
    for pair in all_pairs[:100]:  # Тестируем на 100 парах
        info = fetcher.get_pair_info(pair)
        if info:
            processed += 1
    
    processing_time = time.time() - start_time
    pairs_per_second = processed / processing_time if processing_time > 0 else 0
    
    print(f"  ✅ Всего пар: {len(all_pairs)}")
    print(f"  ✅ Обработано пар: {processed}/100")
    print(f"  ✅ Скорость обработки: {pairs_per_second:.1f} пар/сек")
    
    # Оценка для 750 пар
    estimated_time = 750 / pairs_per_second if pairs_per_second > 0 else float('inf')
    print(f"  ✅ Оценка времени для 750 пар: {estimated_time:.1f}s")
    
    assert pairs_per_second > 10, f"Скорость обработки слишком низкая: {pairs_per_second:.1f}"
    assert estimated_time < 60, f"Время обработки 750 пар слишком большое: {estimated_time:.1f}s"
    
    return True


def main():
    """Главная функция тестирования"""
    print("=" * 70)
    print("🧪 ИНТЕГРАЦИОННЫЙ ТЕСТ MEXC PAIRS FETCHER")
    print("=" * 70)
    
    # Настройка логирования
    logger = setup_logger(__name__, "WARNING")  # Минимальное логирование для тестов
    
    start_time = time.time()
    tests = [
        test_basic_functionality,
        test_filtering_capabilities,
        test_detailed_info,
        test_performance,
        test_auto_update,
        test_error_handling,
        test_scalability
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            print(f"\n{test_func.__doc__ or test_func.__name__}")
            print("-" * 50)
            
            result = test_func()
            if result:
                passed += 1
                print("  🎉 PASSED")
            else:
                failed += 1
                print("  ❌ FAILED")
                
        except Exception as e:
            failed += 1
            print(f"  ❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    total_time = time.time() - start_time
    
    print("\n" + "=" * 70)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 70)
    print(f"✅ Пройдено тестов: {passed}")
    print(f"❌ Провалено тестов: {failed}")
    print(f"📝 Всего тестов: {passed + failed}")
    print(f"⏱️  Время выполнения: {total_time:.1f}s")
    
    if failed == 0:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Модуль готов к использованию.")
        print("✨ Система поддерживает 750+ торговых пар MEXC Futures")
        return True
    else:
        print(f"\n❌ {failed} тест(ов) провалено. Требуется доработка.")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⛔ Тестирование прервано пользователем")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
