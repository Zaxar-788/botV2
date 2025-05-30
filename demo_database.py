"""
Примеры использования системы базы данных и кэша сигналов
Демонстрация основных возможностей сохранения и анализа истории
"""

import time
import logging
from datetime import datetime, timedelta
from src.utils.logger import setup_main_logger
from src.main import MexcAnalysisBot
from src.data.database import SignalsManager
from src.config import TRADING_PAIRS, TIMEFRAMES

# Настройка логгера
logger = logging.getLogger(__name__)


def demo_basic_usage():
    """Демонстрация базового использования с сохранением сигналов"""
    logger.info("🎯 === ДЕМО 1: БАЗОВОЕ ИСПОЛЬЗОВАНИЕ ===")
    
    try:
        # Создаем бота с ограниченным набором пар для демо
        demo_pairs = ["BTC_USDT", "ETH_USDT"]
        demo_timeframes = ["Min1", "Min5"]
        
        bot = MexcAnalysisBot(pairs=demo_pairs, timeframes=demo_timeframes)
        
        logger.info("🔍 Выполнение нескольких итераций анализа...")
        
        # Выполняем несколько итераций
        for i in range(3):
            logger.info(f"📊 Итерация {i+1}/3...")
            signals = bot.analyze_single_iteration()
            
            if signals:
                logger.info(f"   🎯 Найдено {len(signals)} сигналов!")
                for signal in signals:
                    logger.info(f"      💫 {signal.pair} ({signal.timeframe}): {signal.spike_ratio:.1f}x")
            else:
                logger.info("   ✅ Сигналов не обнаружено")
            
            # Пауза между итерациями
            time.sleep(2)
        
        # Показываем статистику
        logger.info("📊 Статистика анализа:")
        bot._print_detailed_statistics()
        
        # Показываем статистику базы данных
        logger.info("💾 Статистика базы данных:")
        bot.print_database_statistics()
        
        bot.stop()
        logger.info("✅ Демо базового использования завершено")
        
    except Exception as e:
        logger.error(f"❌ Ошибка демо: {e}")
        raise


def demo_history_analysis():
    """Демонстрация анализа истории сигналов"""
    logger.info("🎯 === ДЕМО 2: АНАЛИЗ ИСТОРИИ СИГНАЛОВ ===")
    
    try:
        # Создаем менеджер для работы с историей
        manager = SignalsManager()
        
        # Получаем общую статистику
        stats = manager.get_full_statistics()
        db_stats = stats['database']
        
        total_signals = db_stats.get('total_signals', 0)
        logger.info(f"📊 Всего сигналов в базе: {total_signals}")
        
        if total_signals == 0:
            logger.warning("⚠️ В базе нет сигналов. Запустите сначала бота для генерации данных.")
            manager.close()
            return
        
        # Анализ по парам
        by_pairs = db_stats.get('by_pairs', {})
        logger.info("📈 Анализ по торговым парам:")
        for pair, count in sorted(by_pairs.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"   {pair}: {count} сигналов")
        
        # Анализ по таймфреймам
        by_timeframes = db_stats.get('by_timeframes', {})
        logger.info("⏰ Анализ по таймфреймам:")
        for tf, count in sorted(by_timeframes.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"   {tf}: {count} сигналов")
        
        # Получаем последние сигналы
        logger.info("🔍 Последние 5 сигналов:")
        recent_signals = manager.get_signals_history(limit=5)
        
        for i, signal in enumerate(recent_signals, 1):
            timestamp = datetime.fromtimestamp(signal['timestamp'] / 1000)
            logger.info(f"   {i}. {signal['pair']} ({signal['timeframe']}) - "
                       f"{timestamp.strftime('%H:%M:%S')} - спайк {signal['spike_ratio']:.1f}x")
        
        # Анализ по конкретной паре
        if by_pairs:
            top_pair = max(by_pairs.items(), key=lambda x: x[1])[0]
            logger.info(f"🎯 Детальный анализ самой активной пары: {top_pair}")
            
            pair_signals = manager.get_signals_history(pair=top_pair, limit=10)
            logger.info(f"   📊 Найдено {len(pair_signals)} сигналов для {top_pair}")
            
            if pair_signals:
                # Анализ спайков
                spike_ratios = [s['spike_ratio'] for s in pair_signals]
                avg_spike = sum(spike_ratios) / len(spike_ratios)
                max_spike = max(spike_ratios)
                
                logger.info(f"   📈 Средний спайк: {avg_spike:.1f}x")
                logger.info(f"   🚀 Максимальный спайк: {max_spike:.1f}x")
        
        manager.close()
        logger.info("✅ Демо анализа истории завершено")
        
    except Exception as e:
        logger.error(f"❌ Ошибка демо истории: {e}")
        raise


def demo_export_and_reporting():
    """Демонстрация экспорта данных и отчетности"""
    logger.info("🎯 === ДЕМО 3: ЭКСПОРТ И ОТЧЕТНОСТЬ ===")
    
    try:
        manager = SignalsManager()
        
        # Проверяем наличие данных
        stats = manager.get_full_statistics()
        total_signals = stats['database'].get('total_signals', 0)
        
        if total_signals == 0:
            logger.warning("⚠️ Нет данных для экспорта")
            manager.close()
            return
        
        logger.info(f"📊 Экспорт {total_signals} сигналов...")
        
        # Экспорт всех данных
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Общий экспорт
        all_export = f"all_signals_{timestamp}.csv"
        success = manager.export_signals(all_export, limit=1000)
        if success:
            logger.info(f"   ✅ Все сигналы экспортированы: {all_export}")
        
        # Экспорт по парам
        by_pairs = stats['database'].get('by_pairs', {})
        for pair in list(by_pairs.keys())[:2]:  # Экспортируем только 2 пары для демо
            pair_export = f"signals_{pair}_{timestamp}.csv"
            success = manager.export_signals(pair_export, pair=pair, limit=500)
            if success:
                count = by_pairs[pair]
                logger.info(f"   ✅ {pair}: {count} сигналов экспортировано в {pair_export}")
        
        # Экспорт по таймфреймам
        by_timeframes = stats['database'].get('by_timeframes', {})
        if "Min1" in by_timeframes:
            tf_export = f"signals_Min1_{timestamp}.csv"
            success = manager.export_signals(tf_export, timeframe="Min1", limit=500)
            if success:
                count = by_timeframes["Min1"]
                logger.info(f"   ✅ Min1: {count} сигналов экспортировано в {tf_export}")
        
        # Создаем сводный отчет
        report_file = f"signals_report_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=== ОТЧЕТ ПО СИГНАЛАМ ===\n")
            f.write(f"Дата создания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Всего сигналов: {total_signals}\n\n")
            
            f.write("По торговым парам:\n")
            for pair, count in sorted(by_pairs.items(), key=lambda x: x[1], reverse=True):
                f.write(f"  {pair}: {count} сигналов\n")
            
            f.write("\nПо таймфреймам:\n")
            for tf, count in sorted(by_timeframes.items(), key=lambda x: x[1], reverse=True):
                f.write(f"  {tf}: {count} сигналов\n")
            
            # Добавляем примеры сигналов
            f.write("\nПримеры последних сигналов:\n")
            recent = manager.get_signals_history(limit=5)
            for signal in recent:
                timestamp_dt = datetime.fromtimestamp(signal['timestamp'] / 1000)
                f.write(f"  {timestamp_dt.strftime('%Y-%m-%d %H:%M:%S')} - "
                       f"{signal['pair']} ({signal['timeframe']}) - "
                       f"спайк {signal['spike_ratio']:.1f}x\n")
        
        logger.info(f"   📄 Сводный отчет создан: {report_file}")
        
        manager.close()
        logger.info("✅ Демо экспорта и отчетности завершено")
        
    except Exception as e:
        logger.error(f"❌ Ошибка демо экспорта: {e}")
        raise


def demo_cache_monitoring():
    """Демонстрация мониторинга кэша в реальном времени"""
    logger.info("🎯 === ДЕМО 4: МОНИТОРИНГ КЭША ===")
    
    try:
        # Создаем бота с настройками для демонстрации кэша
        demo_pairs = ["BTC_USDT"]
        demo_timeframes = ["Min1"]
        
        bot = MexcAnalysisBot(pairs=demo_pairs, timeframes=demo_timeframes)
        
        logger.info("🗂️ Мониторинг состояния кэша в реальном времени...")
        
        # Выполняем несколько итераций с мониторингом кэша
        for i in range(5):
            logger.info(f"🔄 Итерация {i+1}/5...")
            
            # Получаем статистику кэша до анализа
            cache_stats_before = bot.get_database_statistics()['cache']
            buffer_before = cache_stats_before.get('buffer_size', 0)
            
            # Выполняем анализ
            signals = bot.analyze_single_iteration()
            
            # Получаем статистику кэша после анализа
            cache_stats_after = bot.get_database_statistics()['cache']
            buffer_after = cache_stats_after.get('buffer_size', 0)
            
            logger.info(f"   📊 Кэш: {buffer_before} → {buffer_after} "
                       f"(макс: {cache_stats_after.get('max_buffer_size', 0)})")
            
            if signals:
                logger.info(f"   🎯 Найдено {len(signals)} сигналов, добавлено в кэш")
            else:
                logger.info("   ✅ Сигналов не найдено")
            
            # Пауза
            time.sleep(3)
        
        # Показываем финальную статистику
        final_stats = bot.get_database_statistics()
        logger.info("📊 Финальная статистика кэша:")
        cache_stats = final_stats['cache']
        db_stats = final_stats['database']
        
        logger.info(f"   🗂️ Буфер: {cache_stats.get('buffer_size', 0)}/{cache_stats.get('max_buffer_size', 0)}")
        logger.info(f"   💾 В БД: {db_stats.get('total_signals', 0)} сигналов")
        logger.info(f"   ⚙️ Интервал сброса: {cache_stats.get('flush_interval', 0)} сек")
        
        bot.stop()
        logger.info("✅ Демо мониторинга кэша завершено")
        
    except Exception as e:
        logger.error(f"❌ Ошибка демо кэша: {e}")
        raise


def main():
    """Главная функция демонстрации"""
    try:
        # Настраиваем логирование
        setup_main_logger()
        
        logger.info("🚀 === ДЕМОНСТРАЦИЯ СИСТЕМЫ БД И КЭША ===")
        logger.info("💡 Показываем возможности сохранения и анализа истории сигналов")
        
        # Выбираем демо для запуска
        demos = [
            ("Базовое использование", demo_basic_usage),
            ("Анализ истории сигналов", demo_history_analysis),
            ("Экспорт и отчетность", demo_export_and_reporting),
            ("Мониторинг кэша", demo_cache_monitoring)
        ]
        
        for name, demo_func in demos:
            logger.info(f"\n{'='*50}")
            logger.info(f"▶️ Запуск демо: {name}")
            logger.info(f"{'='*50}")
            
            try:
                demo_func()
                logger.info(f"✅ Демо '{name}' завершено успешно")
            except Exception as e:
                logger.error(f"❌ Ошибка в демо '{name}': {e}")
                continue
            
            # Пауза между демо
            logger.info("⏸️ Пауза 3 секунды...")
            time.sleep(3)
        
        logger.info("\n🎉 === ВСЕ ДЕМО ЗАВЕРШЕНЫ ===")
        logger.info("💡 Система базы данных и кэша готова к использованию!")
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка демонстрации: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
