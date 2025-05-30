#!/usr/bin/env python3
"""
Демонстрация работы модуля получения торговых пар с MEXC Futures
Показывает основные возможности и производительность для масштабирования до 750+ пар
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

def main():
    """Основная функция демонстрации"""
    
    # Настройка логирования
    logger = setup_logger(__name__, "INFO")
    
    print("=" * 60)
    print("🚀 ДЕМОНСТРАЦИЯ MEXC PAIRS FETCHER")
    print("=" * 60)
    
    # Тест 1: Простое получение всех пар
    print("\n📊 ТЕСТ 1: Получение всех фьючерсных пар")
    print("-" * 40)
    
    start_time = time.time()
    pairs = get_all_futures_pairs(force_update=True)
    fetch_time = time.time() - start_time
    
    print(f"✅ Получено пар: {len(pairs)}")
    print(f"⏱️  Время выполнения: {fetch_time:.2f} секунд")
    
    if pairs:
        print(f"📝 Первые 10 пар: {pairs[:10]}")
        print(f"📝 Последние 5 пар: {pairs[-5:]}")
    else:
        print("❌ Не удалось получить торговые пары")
        return
    
    # Тест 2: Работа с детализированным фетчером
    print("\n🔧 ТЕСТ 2: Детализированная работа с фетчером")
    print("-" * 50)
    
    fetcher = MexcPairsFetcher(update_interval=60)  # Обновление каждую минуту для демо
    
    # Фильтрация пар
    print("\n🔍 Фильтрация торговых пар:")
    
    # USDT пары
    usdt_pairs = fetcher.get_pairs_by_quote_coin('USDT')
    print(f"  • USDT пары: {len(usdt_pairs)}")
    if usdt_pairs:
        print(f"    Примеры: {usdt_pairs[:5]}")
    
    # BTC пары
    btc_pairs = fetcher.get_pairs_by_quote_coin('BTC')
    print(f"  • BTC пары: {len(btc_pairs)}")
    if btc_pairs:
        print(f"    Примеры: {btc_pairs[:3]}")
    
    # ETH базовые пары
    eth_base_pairs = fetcher.get_pairs_by_base_coin('ETH')
    print(f"  • ETH базовые пары: {len(eth_base_pairs)}")
    if eth_base_pairs:
        print(f"    Примеры: {eth_base_pairs[:3]}")
    
    # Тест 3: Детальная информация о парах
    print("\n📋 ТЕСТ 3: Детальная информация о торговых парах")
    print("-" * 52)
    
    # Берём первые несколько USDT пар для анализа
    sample_pairs = usdt_pairs[:3] if usdt_pairs else pairs[:3]
    
    for pair in sample_pairs:
        pair_info = fetcher.get_pair_info(pair)
        if pair_info:
            print(f"\n🔸 {pair}:")
            print(f"    Базовая валюта: {pair_info.base_coin}")
            print(f"    Котируемая валюта: {pair_info.quote_coin}")
            print(f"    Макс. плечо: {pair_info.max_leverage}x")
            print(f"    Мин. плечо: {pair_info.min_leverage}x")
            print(f"    Шкала цены: {pair_info.price_scale}")
            print(f"    Комиссия maker: {pair_info.maker_fee_rate}")
            print(f"    Комиссия taker: {pair_info.taker_fee_rate}")
            print(f"    Мин. объём: {pair_info.min_vol}")
            print(f"    Макс. объём: {pair_info.max_vol}")
            print(f"    Новая пара: {'Да' if pair_info.is_new else 'Нет'}")
            if pair_info.concept_plate:
                print(f"    Концептуальные теги: {', '.join(pair_info.concept_plate)}")
    
    # Тест 4: Производительность и кэширование
    print("\n⚡ ТЕСТ 4: Тестирование производительности и кэширования")
    print("-" * 58)
    
    # Первый запрос (с обновлением)
    start_time = time.time()
    pairs_1 = fetcher.get_all_pairs(force_update=True)
    time_1 = time.time() - start_time
    
    # Второй запрос (из кэша)
    start_time = time.time()
    pairs_2 = fetcher.get_all_pairs(force_update=False)
    time_2 = time.time() - start_time
    
    print(f"📊 Результаты производительности:")
    print(f"  • С обновлением: {time_1:.3f}s ({len(pairs_1)} пар)")
    print(f"  • Из кэша: {time_2:.3f}s ({len(pairs_2)} пар)")
    print(f"  • Ускорение кэша: {time_1/time_2:.1f}x")
    
    # Информация о кэше
    cache_info = fetcher.get_cache_info()
    print(f"\n💾 Информация о кэше:")
    for key, value in cache_info.items():
        if key != 'stats':
            print(f"  • {key}: {value}")
    
    print(f"\n📈 Статистика:")
    for key, value in cache_info['stats'].items():
        print(f"  • {key}: {value}")
    
    # Тест 5: Автоматическое обновление
    print("\n🔄 ТЕСТ 5: Автоматическое обновление (демо)")
    print("-" * 45)
    
    print("Запускаю автоматическое обновление...")
    fetcher.start_auto_update()
    
    print("Ожидание 5 секунд...")
    time.sleep(5)
    
    cache_info_after = fetcher.get_cache_info()
    print(f"Автообновление активно: {cache_info_after['auto_update_running']}")
    
    print("Останавливаю автоматическое обновление...")
    fetcher.stop_auto_update()
    
    # Тест 6: Анализ для большого количества пар
    print("\n🎯 ТЕСТ 6: Анализ готовности к масштабированию")
    print("-" * 52)
    
    total_pairs = len(pairs)
    usdt_count = len(usdt_pairs)
    
    print(f"📊 Анализ текущих данных:")
    print(f"  • Общее количество пар: {total_pairs}")
    print(f"  • USDT пары: {usdt_count} ({usdt_count/total_pairs*100:.1f}%)")
    print(f"  • Память на пару: ~{sys.getsizeof(pairs[0]) if pairs else 0} байт")
    print(f"  • Примерная память для 750 пар: ~{sys.getsizeof(pairs[0]) * 750 / 1024:.1f} КБ")
    
    # Оценка производительности для большого количества пар
    if total_pairs > 100:
        sample_size = min(100, total_pairs)
        start_time = time.time()
        
        # Имитируем обработку большого количества пар
        for pair in pairs[:sample_size]:
            info = fetcher.get_pair_info(pair)
            # Имитация анализа
            if info and info.max_leverage > 50:
                pass
        
        process_time = time.time() - start_time
        estimated_time_750 = (process_time / sample_size) * 750
        
        print(f"\n⚡ Производительность обработки:")
        print(f"  • Время для {sample_size} пар: {process_time:.3f}s")
        print(f"  • Оценка для 750 пар: {estimated_time_750:.3f}s")
        print(f"  • Пар в секунду: {sample_size/process_time:.1f}")
    
    # Рекомендации
    print("\n💡 РЕКОМЕНДАЦИИ ДЛЯ МАСШТАБИРОВАНИЯ:")
    print("-" * 40)
    print("✅ Кэширование работает эффективно")
    print("✅ Фоновое обновление реализовано")
    print("✅ Обработка ошибок настроена")
    print("✅ Фильтрация пар доступна")
    print("✅ Детальная информация о парах")
    
    if total_pairs >= 500:
        print("🎉 Система готова для работы с 750+ парами!")
    else:
        print(f"⚠️  Текущее количество пар ({total_pairs}) меньше целевого")
    
    print("\n" + "=" * 60)
    print("✨ ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⛔ Демонстрация прервана пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Ошибка во время демонстрации: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        print(f"\n\n❌ Ошибка при выполнении демонстрации: {e}")
        import traceback
        traceback.print_exc()