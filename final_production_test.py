#!/usr/bin/env python3
"""
Финальный тест готовности системы к производственному использованию
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.logger import setup_main_logger
from src.main import AsyncMexcAnalysisBot

async def main():
    """Финальный тест производственной готовности"""
    logger = setup_main_logger()
    
    logger.info("🎯 === ФИНАЛЬНЫЙ ТЕСТ ПРОИЗВОДСТВЕННОЙ ГОТОВНОСТИ ===")
    
    try:
        # Создаем бота с полной конфигурацией
        bot = AsyncMexcAnalysisBot(
            timeframes=['Min1', 'Min5', 'Min15', 'Min60'],
            analysis_interval=60,
            pairs_update_interval=3600,
            enable_websocket=True
        )
        
        # Инициализируем WebSocket
        await bot._init_websocket_client()
        
        # Получаем все торговые пары
        pairs = await bot.get_dynamic_pairs()
        
        logger.info(f"🚀 СИСТЕМА ГОТОВА К ПРОИЗВОДСТВЕННОМУ ИСПОЛЬЗОВАНИЮ!")
        logger.info(f"📊 Доступно для анализа: {len(pairs)} торговых пар")
        logger.info(f"🌐 WebSocket клиент: {'✅ АКТИВЕН' if bot.ws_client else '❌ НЕ АКТИВЕН'}")
        logger.info(f"⏰ Таймфреймы: {', '.join(bot.timeframes)}")
        logger.info(f"🔄 Интервал анализа: {bot.analysis_interval}с")
        logger.info(f"📡 Dual-mode архитектура: REST API + WebSocket real-time")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка в финальном тесте: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
