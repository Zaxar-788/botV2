
#!/usr/bin/env python3
"""
Быстрый тест фильтрации пар
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data.pairs_fetcher import MexcPairsFetcher

def test_filtering():
    """Тест фильтрации пар"""
    
    print("🧪 БЫСТРЫЙ ТЕСТ ФИЛЬТРАЦИИ")
    print("=" * 40)
    
    fetcher = MexcPairsFetcher()
    
    # Получаем все пары
    print("1. Получение пар...")
    pairs = fetcher.get_all_pairs(force_update=True)
    print(f"   Всего пар: {len(pairs)}")
    
    # Проверяем, что кэш информации заполнен
    print(f"   Кэш информации: {len(fetcher._pairs_info_cache)} элементов")
    
    if len(fetcher._pairs_info_cache) == 0:
        print("❌ Кэш информации пуст!")
        return
    
    # Показываем несколько примеров информации о парах
    print("\n2. Примеры информации о парах:")
    sample_pairs = list(fetcher._pairs_info_cache.keys())[:5]
    
    for symbol in sample_pairs:
        info = fetcher._pairs_info_cache[symbol]
        print(f"   {symbol}: {info.base_coin}/{info.quote_coin}")
    
    # Тестируем фильтрацию
    print("\n3. Тестирование фильтрации:")
    
    usdt_pairs = fetcher.get_pairs_by_quote_coin('USDT')
    print(f"   USDT пары: {len(usdt_pairs)}")
    if usdt_pairs:
        print(f"   Примеры: {usdt_pairs[:5]}")
    
    usd_pairs = fetcher.get_pairs_by_quote_coin('USD')
    print(f"   USD пары: {len(usd_pairs)}")
    if usd_pairs:
        print(f"   Примеры: {usd_pairs[:3]}")
    
    btc_pairs = fetcher.get_pairs_by_quote_coin('BTC')
    print(f"   BTC пары: {len(btc_pairs)}")
    if btc_pairs:
        print(f"   Примеры: {btc_pairs[:3]}")
    
    # Тестируем базовые валюты
    btc_base = fetcher.get_pairs_by_base_coin('BTC')
    print(f"   BTC базовые: {len(btc_base)}")
    if btc_base:
        print(f"   Примеры: {btc_base[:3]}")
    
    eth_base = fetcher.get_pairs_by_base_coin('ETH')
    print(f"   ETH базовые: {len(eth_base)}")
    if eth_base:
        print(f"   Примеры: {eth_base[:3]}")

if __name__ == "__main__":
    test_filtering()
