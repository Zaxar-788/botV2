#!/usr/bin/env python3
"""
Запускной скрипт для бота анализа аномалий MEXC Futures
"""

import sys
import os

# Добавляем текущую директорию в путь для импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Теперь импортируем и запускаем основной модуль
from src.main import main

if __name__ == "__main__":
    exit(main())
