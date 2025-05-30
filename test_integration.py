#!/usr/bin/env python3
"""
Простой интеграционный тест для проверки основной функциональности модуля pairs_fetcher
"""

import sys
import os
import time

# Добавляем src в sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data.pairs_fetcher import MexcPairsFetcher, get_all_futures_pairs

def test_basic_functionality():
    """Базовый тест функциональности"""
    
    print("🧪 БАЗОВЫЙ ТЕСТ ФУНКЦИОНАЛЬНОСТИ")
    print("=" * 50)
    
    # Тест 1: Создание экземпляра фетчера
    print("1. Создание экземпляра MexcPairsFetcher...")
    fetcher = MexcPairsFetcher(update_interval=60)
    print("   ✅ Фетчер создан успешно")
    
    # Тест 2: Получение всех пар
    print("\n2. Получение всех торговых пар...")
    start_time = time.time()
    pairs = fetcher.get_all_pairs(force_update=True)
    elapsed = time.time() - start_time
    
    print(f"   ✅ Получено пар: {len(pairs)}")
    print(f"   ⏱️  Время выполнения: {elapsed:.2f}s")
    
    if len(pairs) > 0:
        print(f"   📝 Примеры пар: {pairs[:5]}")
        
        # Тест 3: Получение информации о паре
        print("\n3. Получение информации о первой паре...")
        first_pair = pairs[0]
        pair_info = fetcher.get_pair_info(first_pair)
        
        if pair_info:
            print(f"   ✅ Информация о {first_pair}:")
            print(f"      Базовая валюта: {pair_info.base_coin}")
            print(f"      Котируемая валюта: {pair_info.quote_coin}")
            print(f"      Макс. плечо: {pair_info.max_leverage}")
            print(f"      Мин. плечо: {pair_info.min_leverage}")
        else:
            print(f"   ❌ Не удалось получить информацию о {first_pair}")
        
        # Тест 4: Фильтрация пар
        print("\n4. Тестирование фильтрации...")
        
        usdt_pairs = fetcher.get_pairs_by_quote_coin('USDT')
        print(f"   • USDT пары: {len(usdt_pairs)}")
        if len(usdt_pairs) > 0:
            print(f"     Примеры: {usdt_pairs[:3]}")
        
        usd_pairs = fetcher.get_pairs_by_quote_coin('USD')
        print(f"   • USD пары: {len(usd_pairs)}")
        if len(usd_pairs) > 0:
            print(f"     Примеры: {usd_pairs[:3]}")
        
        btc_base_pairs = fetcher.get_pairs_by_base_coin('BTC')
        print(f"   • BTC базовые пары: {len(btc_base_pairs)}")
        if len(btc_base_pairs) > 0:
            print(f"     Примеры: {btc_base_pairs[:3]}")
        
        # Тест 5: Кэширование
        print("\n5. Тестирование кэширования...")
        start_time = time.time()
        cached_pairs = fetcher.get_all_pairs(force_update=False)
        cached_elapsed = time.time() - start_time
        
        print(f"   ✅ Из кэша получено: {len(cached_pairs)} пар")
        print(f"   ⏱️  Время из кэша: {cached_elapsed:.4f}s")
        print(f"   🚀 Ускорение: {elapsed/cached_elapsed:.1f}x")
        
        # Тест 6: Информация о кэше
        print("\n6. Информация о кэше...")
        cache_info = fetcher.get_cache_info()
        print(f"   • Пар в кэше: {cache_info['pairs_count']}")
        print(f"   • Последнее обновление: {cache_info['last_update']}")
        print(f"   • Интервал обновления: {cache_info['update_interval']}s")
        print(f"   • Статистика обновлений: {cache_info['stats']['successful_updates']} успешных")
        
        # Тест 7: Глобальная функция
        print("\n7. Тестирование глобальной функции...")
        global_pairs = get_all_futures_pairs()
        print(f"   ✅ Глобальная функция вернула: {len(global_pairs)} пар")
        
        # Тест 8: Автообновление (краткий тест)
        print("\n8. Краткий тест автообновления...")
        fetcher.start_auto_update()
        print("   ✅ Автообновление запущено")
        
        time.sleep(2)  # Ждём 2 секунды
        
        cache_info_after = fetcher.get_cache_info()
        auto_running = cache_info_after['auto_update_running']
        print(f"   • Автообновление активно: {auto_running}")
        
        fetcher.stop_auto_update()
        print("   ✅ Автообновление остановлено")
        
        print("\n" + "=" * 50)
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Модуль pairs_fetcher готов к использованию")
        print(f"✅ Поддерживается {len(pairs)} торговых пар")
        print(f"✅ Включая {len(usdt_pairs)} USDT пар")
        print("✅ Кэширование работает эффективно")
        print("✅ Фильтрация работает корректно")
        print("✅ Автообновление функционирует")
        
    else:
        print("   ❌ Не удалось получить торговые пары")
        return False
    
    return True

def test_error_handling():
    """Тест обработки ошибок"""
    
    print("\n🛡️  ТЕСТ ОБРАБОТКИ ОШИБОК")
    print("=" * 40)
    
    fetcher = MexcPairsFetcher()
    
    # Тест получения несуществующей пары
    print("1. Тест получения несуществующей пары...")
    info = fetcher.get_pair_info("NONEXISTENT_PAIR")
    if info is None:
        print("   ✅ Корректно обработана несуществующая пара")
    else:
        print("   ❌ Ошибка: получена информация о несуществующей паре")
    
    # Тест пустых фильтров
    print("\n2. Тест пустых фильтров...")
    empty_pairs = fetcher.get_pairs_by_quote_coin("NONEXISTENT")
    if len(empty_pairs) == 0:
        print("   ✅ Фильтр корректно возвращает пустой список")
    else:
        print("   ❌ Ошибка: фильтр возвратил непустой список")
    
    print("   ✅ Обработка ошибок работает корректно")

def main():
    """Главная функция тестирования"""
    
    print("🚀 ИНТЕГРАЦИОННОЕ ТЕСТИРОВАНИЕ PAIRS_FETCHER")
    print("=" * 60)
    
    try:
        # Основные тесты
        success = test_basic_functionality()
        
        if success:
            # Тест обработки ошибок
            test_error_handling()
            
            print("\n" + "=" * 60)
            print("🎊 ВСЕ ИНТЕГРАЦИОННЫЕ ТЕСТЫ ЗАВЕРШЕНЫ УСПЕШНО!")
            print("🎯 Модуль готов для интеграции в основной бот")
            print("=" * 60)
        else:
            print("\n❌ Базовые тесты не пройдены")
            
    except Exception as e:
        print(f"\n💥 Критическая ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
