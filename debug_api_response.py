#!/usr/bin/env python3
"""
Отладка структуры ответа API MEXC для понимания формата данных
"""

import sys
import os
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data.pairs_fetcher import MexcPairsFetcher

def debug_api_response():
    """Отладка структуры ответа API"""
    
    print("🔍 ОТЛАДКА СТРУКТУРЫ ОТВЕТА API MEXC")
    print("=" * 50)
    
    fetcher = MexcPairsFetcher()
    
    # Получаем сырые данные от API
    print("Получаем данные от API...")
    api_data = fetcher._fetch_symbols_from_api()
    
    if not api_data:
        print("❌ Не удалось получить данные от API")
        return
    
    print(f"✅ Получены данные от API")
    print(f"Тип ответа: {type(api_data)}")
    print(f"Ключи верхнего уровня: {list(api_data.keys()) if isinstance(api_data, dict) else 'Not a dict'}")
    
    if 'data' in api_data:
        data = api_data['data']
        print(f"\nТип данных в 'data': {type(data)}")
        
        if isinstance(data, list) and len(data) > 0:
            print(f"Количество элементов: {len(data)}")
            print(f"\nПример первого элемента:")
            first_item = data[0]
            print(json.dumps(first_item, indent=2, ensure_ascii=False))
            
            print(f"\nКлючи в элементе: {list(first_item.keys()) if isinstance(first_item, dict) else 'Not a dict'}")
            
            # Проверяем несколько примеров
            print(f"\nПримеры символов и валют:")
            for i, item in enumerate(data[:10]):
                if isinstance(item, dict):
                    symbol = item.get('symbol', 'N/A')
                    base = item.get('baseCoin', 'N/A')
                    quote = item.get('quoteCoin', 'N/A')
                    print(f"  {i+1}. {symbol}: {base}/{quote}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    debug_api_response()
