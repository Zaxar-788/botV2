#!/usr/bin/env python3
"""
Тест исправленной версии модуля pairs_fetcher
"""

import sys
import os
import time

# Добавляем путь к модулю
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Импортируем из исправленной версии напрямую
from src.data.pairs_fetcher_fixed import MexcPairsFetcher, PairInfo

def test_fixed_pairs_fetcher():
    """Тестируем исправленную версию модуля"""
    print("🧪 Тестирование исправленной версии pairs_fetcher")
    print("=" * 60)
    
    # Инициализируем fetcher
    fetcher = MexcPairsFetcher()
    
    # Тест 1: Получение всех пар
    print("\n📊 Тест 1: Получение всех пар")
    start_time = time.time()
    pairs = fetcher.get_all_pairs()
    end_time = time.time()
    
    print(f"✅ Получено {len(pairs)} торговых пар за {end_time - start_time:.2f} сек")
    if len(pairs) > 0:
        print(f"   Пример пар: {pairs[:5]}")
    
    # Тест 2: Фильтрация по USDT
    print("\n💰 Тест 2: Фильтрация пар USDT")
    start_time = time.time()
    usdt_pairs = fetcher.get_pairs_by_quote_coin("USDT")
    end_time = time.time()
    
    print(f"✅ Найдено {len(usdt_pairs)} пар USDT за {end_time - start_time:.3f} сек")
    if len(usdt_pairs) > 0:
        print(f"   Пример USDT пар: {usdt_pairs[:5]}")
    
    # Тест 3: Фильтрация по BTC
    print("\n🟠 Тест 3: Фильтрация пар с базовой валютой BTC")
    start_time = time.time()
    btc_pairs = fetcher.get_pairs_by_base_coin("BTC")
    end_time = time.time()
    
    print(f"✅ Найдено {len(btc_pairs)} пар BTC за {end_time - start_time:.3f} сек")
    if len(btc_pairs) > 0:
        print(f"   Пример BTC пар: {btc_pairs[:3]}")
    
    # Тест 4: Получение информации о конкретной паре
    print("\n🔍 Тест 4: Информация о конкретной паре")
    if len(pairs) > 0:
        test_symbol = pairs[0]
        start_time = time.time()
        pair_info = fetcher.get_pair_info(test_symbol)
        end_time = time.time()
        
        if pair_info:
            print(f"✅ Информация о {test_symbol} получена за {end_time - start_time:.3f} сек")
            print(f"   Символ: {pair_info.symbol}")
            print(f"   Базовая: {pair_info.base_coin}")
            print(f"   Котировка: {pair_info.quote_coin}")
            print(f"   Макс. плечо: {pair_info.max_leverage}")
            print(f"   Мин. размер: {pair_info.min_vol}")
        else:
            print(f"❌ Не удалось получить информацию о {test_symbol}")
    
    # Тест 5: Проверка кэширования
    print("\n⚡ Тест 5: Производительность кэширования")
    start_time = time.time()
    pairs_cached = fetcher.get_all_pairs()
    end_time = time.time()
    cached_time = end_time - start_time
    
    print(f"✅ Кэшированный запрос: {len(pairs_cached)} пар за {cached_time:.6f} сек")
    
    # Финальная статистика
    print("\n" + "=" * 60)
    print("📈 ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 60)
    print(f"🎯 Всего торговых пар: {len(pairs)}")
    print(f"💰 Пары USDT: {len(usdt_pairs)}")
    print(f"🟠 Пары BTC: {len(btc_pairs)}")
    print(f"⚡ Время кэшированного запроса: {cached_time:.6f} сек")
    
    # Проверяем, что основные функции работают
    assert len(pairs) > 700, f"Ожидали > 700 пар, получили {len(pairs)}"
    assert len(usdt_pairs) > 100, f"Ожидали > 100 пар USDT, получили {len(usdt_pairs)}"
    assert cached_time < 0.01, f"Кэш должен работать быстрее 0.01 сек, получили {cached_time:.6f}"
    
    print("\n✅ Все тесты пройдены успешно!")
    return True

if __name__ == "__main__":
    try:
        test_fixed_pairs_fetcher()
        print("\n🎉 Исправленная версия модуля работает корректно!")
    except Exception as e:
        print(f"\n❌ Ошибка в тестировании: {e}")
        import traceback
        traceback.print_exc()
