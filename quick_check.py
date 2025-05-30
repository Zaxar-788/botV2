#!/usr/bin/env python3
"""
🧪 Быстрая проверка работоспособности системы
"""

import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🚀 БЫСТРАЯ ПРОВЕРКА СИСТЕМЫ MEXC BOT")
print("="*50)

# 1. Проверка импортов
print("\n1️⃣ Проверка импортов...")
try:
    from src.main import MexcAnalysisBot
    from src.data.database import SignalsManager
    print("✅ Все основные модули импортированы успешно")
except Exception as e:
    print(f"❌ Ошибка импорта: {e}")

# 2. Проверка БД
print("\n2️⃣ Проверка базы данных...")
try:
    manager = SignalsManager()
    stats = manager.database.get_statistics()
    print(f"✅ БД подключена, сигналов: {stats.get('total_signals', 0)}")
    manager.close()
except Exception as e:
    print(f"❌ Ошибка БД: {e}")

# 3. Проверка бота
print("\n3️⃣ Проверка бота...")
try:
    bot = MexcAnalysisBot()
    print("✅ Бот инициализирован успешно")
except Exception as e:
    print(f"❌ Ошибка бота: {e}")

# 4. Проверка документации
print("\n4️⃣ Проверка документации...")
docs_files = ["docs/DOCUMENTATION.md", "docs/DEVELOPMENT.md", "README.md"]
for file_path in docs_files:
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print(f"✅ {file_path} ({size:,} байт)")
    else:
        print(f"❌ {file_path} не найден")

print("\n" + "="*50)
print("🎯 Проверка завершена!")
print("\n📚 Документация:")
print("   - docs/DOCUMENTATION.md - руководство пользователя")
print("   - docs/DEVELOPMENT.md - техническая документация")
