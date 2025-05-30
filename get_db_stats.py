#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.data.database import SignalsManager
from src.config import DATABASE_CONFIG, CACHE_CONFIG

def main():
    print("📊 ИТОГОВАЯ СТАТИСТИКА БАЗЫ ДАННЫХ")
    print("=" * 50)
    
    # Инициализация менеджера
    sm = SignalsManager(DATABASE_CONFIG, CACHE_CONFIG)
    
    try:        # Получение статистики
        stats = sm.database.get_statistics()
        
        print(f"💾 Всего сигналов в БД: {stats['total_signals']}")
        print()
        
        print("📈 Распределение по торговым парам:")
        for pair, count in stats['by_pairs'].items():
            print(f"   {pair}: {count} сигналов")
        print()
        
        print("⏰ Распределение по таймфреймам:")
        for timeframe, count in stats['by_timeframes'].items():
            print(f"   {timeframe}: {count} сигналов")
        print()        # Информация о кэше
        cache_info = sm.cache.get_cache_stats()
        print(f"🗂️ Состояние кэша: {cache_info['buffer_size']}/{cache_info['max_buffer_size']} сигналов")
        
        print()
        print("✅ Система БД работает корректно!")
        
    finally:
        sm.close()

if __name__ == "__main__":
    main()
