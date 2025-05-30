"""
Модуль для работы с базой данных и кэшем сигналов
Реализует write-back caching с периодическим сбросом в SQLite/PostgreSQL
"""

import sqlite3
import threading
import time
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from queue import Queue
from src.config import DATABASE_CONFIG, CACHE_CONFIG
from src.signals.detector import VolumeSignal

# Настройка логгера
logger = logging.getLogger(__name__)


@dataclass
class StoredSignal:
    """
    Структура сигнала для хранения в базе данных
    Расширенная версия VolumeSignal с дополнительными полями
    """
    id: Optional[int] = None         # ID записи в БД (автоинкремент)
    timestamp: int = 0               # Временная метка сигнала (миллисекунды)
    pair: str = ""                   # Торговая пара (BTC_USDT и т.д.)
    timeframe: str = ""              # Таймфрейм (Min1, Min5 и т.д.)
    signal_type: str = "volume_spike" # Тип сигнала
    price: float = 0.0               # Цена на момент сигнала
    current_volume: float = 0.0      # Текущий объём
    average_volume: float = 0.0      # Средний объём
    spike_ratio: float = 0.0         # Коэффициент превышения объёма
    open_interest: float = 0.0       # Открытый интерес (если доступно)
    period_change: float = 0.0       # Изменение цены за период (%)
    status: str = "new"              # Статус сигнала (new, processed, archived)
    notification_text: str = ""      # Текст уведомления
    created_at: Optional[str] = None # Время создания записи
    
    @classmethod
    def from_volume_signal(cls, signal: VolumeSignal) -> 'StoredSignal':
        """
        Создание StoredSignal из VolumeSignal
        
        Args:
            signal (VolumeSignal): Исходный сигнал от детектора
            
        Returns:
            StoredSignal: Сигнал для сохранения в БД
        """
        return cls(
            timestamp=signal.timestamp,
            pair=signal.pair,
            timeframe=signal.timeframe,
            signal_type="volume_spike",
            price=signal.price,
            current_volume=signal.current_volume,
            average_volume=signal.average_volume,
            spike_ratio=signal.spike_ratio,
            notification_text=signal.message,
            created_at=datetime.now(timezone.utc).isoformat()
        )


class SignalsDatabase:
    """
    Класс для работы с базой данных сигналов
    Поддержка SQLite с возможностью расширения для PostgreSQL
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Инициализация подключения к базе данных
        
        Args:
            config (Dict): Конфигурация БД из config.py
        """
        self.config = config or DATABASE_CONFIG
        self.db_type = self.config.get("type", "sqlite")
        self.connection = None
        self._init_database()
        logger.info(f"Инициализирована база данных: {self.db_type}")
    
    def _init_database(self):
        """Инициализация базы данных и создание таблиц"""
        if self.db_type == "sqlite":
            self._init_sqlite()
        else:
            # TODO: Добавить поддержку PostgreSQL
            logger.warning("PostgreSQL пока не поддерживается, используется SQLite")
            self._init_sqlite()
    
    def _init_sqlite(self):
        """Инициализация SQLite базы данных"""
        try:
            db_path = self.config.get("path", "signals_history.db")
            self.connection = sqlite3.connect(db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # Для доступа к столбцам по имени
            
            # Создаем таблицу сигналов
            self._create_tables()
            
            logger.debug(f"SQLite база данных инициализирована: {db_path}")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации SQLite: {e}")
            raise
    
    def _create_tables(self):
        """Создание таблиц в базе данных"""
        create_signals_table = """
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER NOT NULL,
            pair TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            signal_type TEXT NOT NULL DEFAULT 'volume_spike',
            price REAL NOT NULL,
            current_volume REAL NOT NULL,
            average_volume REAL NOT NULL,
            spike_ratio REAL NOT NULL,
            open_interest REAL DEFAULT 0.0,
            period_change REAL DEFAULT 0.0,
            status TEXT DEFAULT 'new',
            notification_text TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(timestamp, pair, timeframe) ON CONFLICT IGNORE
        );
        """
        
        # Создаем индексы для быстрого поиска
        create_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_signals_pair ON signals(pair);",
            "CREATE INDEX IF NOT EXISTS idx_signals_timeframe ON signals(timeframe);",
            "CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status);",
            "CREATE INDEX IF NOT EXISTS idx_signals_created_at ON signals(created_at);"        ]
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(create_signals_table)
            
            for index_sql in create_indexes:
                cursor.execute(index_sql)
            
            self.connection.commit()
            logger.debug("Таблицы базы данных созданы успешно")
            
        except Exception as e:
            logger.error(f"Ошибка создания таблиц: {e}")
            raise

    def insert_signal(self, signal: StoredSignal) -> Optional[int]:
        """
        Вставка одного сигнала в базу данных
        
        Args:
            signal (StoredSignal): Сигнал для вставки
            
        Returns:
            int: ID вставленной записи или None при ошибке
        """
        try:
            cursor = self.connection.cursor()
            
            # Подготавливаем данные для вставки (исключаем id)
            signal_dict = asdict(signal)
            del signal_dict['id']  # id автоинкремент
            
            # Создаем SQL запрос безопасно
            columns = list(signal_dict.keys())
            values = list(signal_dict.values())
            
            placeholders = ', '.join(['?' for _ in columns])
            columns_str = ', '.join(columns)
            
            sql = f"INSERT INTO signals ({columns_str}) VALUES ({placeholders})"
            
            cursor.execute(sql, values)
            self.connection.commit()
            
            signal_id = cursor.lastrowid
            logger.debug(f"Сигнал сохранен в БД с ID: {signal_id}")
            return signal_id
            
        except Exception as e:
            logger.error(f"Ошибка вставки сигнала в БД: {e}")
            return None
    
    def insert_signals_batch(self, signals: List[StoredSignal]) -> int:
        """
        Пакетная вставка сигналов в базу данных
        
        Args:
            signals (List[StoredSignal]): Список сигналов для вставки
            
        Returns:
            int: Количество успешно вставленных записей
        """
        if not signals:
            return 0
        
        try:
            cursor = self.connection.cursor()
            inserted_count = 0
            
            for signal in signals:
                # Подготавливаем данные (исключаем id)
                signal_dict = asdict(signal)
                del signal_dict['id']
                
                # Создаем SQL запрос безопасно
                columns = list(signal_dict.keys())
                values = list(signal_dict.values())
                
                placeholders = ', '.join(['?' for _ in columns])
                columns_str = ', '.join(columns)
                
                sql = f"INSERT OR IGNORE INTO signals ({columns_str}) VALUES ({placeholders})"
                
                cursor.execute(sql, values)
                if cursor.rowcount > 0:
                    inserted_count += 1
            
            self.connection.commit()
            logger.info(f"Пакетная вставка: {inserted_count}/{len(signals)} сигналов сохранено")
            return inserted_count
            
        except Exception as e:
            logger.error(f"Ошибка пакетной вставки сигналов: {e}")
            return 0
    
    def get_signals(self, pair: str = None, timeframe: str = None, 
                   status: str = None, limit: int = 100) -> List[Dict]:
        """
        Получение сигналов из базы данных с фильтрацией
        
        Args:
            pair (str): Фильтр по торговой паре
            timeframe (str): Фильтр по таймфрейму
            status (str): Фильтр по статусу
            limit (int): Максимальное количество записей
            
        Returns:
            List[Dict]: Список сигналов
        """
        try:
            cursor = self.connection.cursor()
            
            # Строим SQL запрос с фильтрами
            sql = "SELECT * FROM signals WHERE 1=1"
            params = []
            
            if pair:
                sql += " AND pair = ?"
                params.append(pair)
            
            if timeframe:
                sql += " AND timeframe = ?"
                params.append(timeframe)
            
            if status:
                sql += " AND status = ?"
                params.append(status)
            
            sql += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            # Преобразуем в список словарей
            signals = [dict(row) for row in rows]
            
            logger.debug(f"Получено {len(signals)} сигналов из БД")
            return signals
            
        except Exception as e:
            logger.error(f"Ошибка получения сигналов из БД: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Получение статистики по сигналам в базе данных
        
        Returns:
            Dict: Статистика (общее количество, по парам, по таймфреймам и т.д.)
        """
        try:
            cursor = self.connection.cursor()
            
            # Общее количество сигналов
            cursor.execute("SELECT COUNT(*) as total FROM signals")
            total = cursor.fetchone()['total']
            
            # Количество по парам
            cursor.execute("""
                SELECT pair, COUNT(*) as count 
                FROM signals 
                GROUP BY pair 
                ORDER BY count DESC
            """)
            by_pairs = {row['pair']: row['count'] for row in cursor.fetchall()}
            
            # Количество по таймфреймам
            cursor.execute("""
                SELECT timeframe, COUNT(*) as count 
                FROM signals 
                GROUP BY timeframe 
                ORDER BY count DESC
            """)
            by_timeframes = {row['timeframe']: row['count'] for row in cursor.fetchall()}
            
            # Количество по статусам
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM signals 
                GROUP BY status
            """)
            by_status = {row['status']: row['count'] for row in cursor.fetchall()}
            
            return {
                'total_signals': total,
                'by_pairs': by_pairs,
                'by_timeframes': by_timeframes,
                'by_status': by_status
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}
    
    def close(self):
        """Закрытие подключения к базе данных"""
        if self.connection:
            self.connection.close()
            logger.debug("Подключение к базе данных закрыто")


class SignalsCache:
    """
    Write-back кэш для сигналов с периодическим сбросом в базу данных
    Обеспечивает высокую производительность при сохранении надёжности
    """
    
    def __init__(self, database: SignalsDatabase, config: Dict[str, Any] = None):
        """
        Инициализация кэша
        
        Args:
            database (SignalsDatabase): Экземпляр базы данных
            config (Dict): Конфигурация кэша
        """
        self.database = database
        self.config = config or CACHE_CONFIG
        
        # Настройки кэша
        self.buffer_size = self.config.get("buffer_size", 100)
        self.flush_interval = self.config.get("flush_interval", 300)
        self.batch_size = self.config.get("batch_size", 50)
        self.enabled = self.config.get("enable_cache", True)
        
        # Буфер для сигналов
        self.buffer: List[StoredSignal] = []
        self.buffer_lock = threading.Lock()
        
        # Поток для периодического сброса
        self.flush_thread = None
        self.stop_event = threading.Event()
        
        if self.enabled:
            self._start_flush_thread()
        
        logger.info(f"Инициализирован кэш сигналов: размер буфера={self.buffer_size}, "
                   f"интервал сброса={self.flush_interval}с")
    
    def _start_flush_thread(self):
        """Запуск потока для периодического сброса буфера"""
        self.flush_thread = threading.Thread(target=self._flush_worker, daemon=True)
        self.flush_thread.start()
        logger.debug("Поток периодического сброса кэша запущен")
    
    def _flush_worker(self):
        """Рабочий поток для периодического сброса буфера в БД"""
        while not self.stop_event.wait(self.flush_interval):
            self.flush_buffer()
    
    def add_signal(self, signal: VolumeSignal):
        """
        Добавление сигнала в кэш
        
        Args:
            signal (VolumeSignal): Сигнал от детектора
        """
        if not self.enabled:
            # Если кэш отключен, сразу записываем в БД
            stored_signal = StoredSignal.from_volume_signal(signal)
            self.database.insert_signal(stored_signal)
            return
        
        stored_signal = StoredSignal.from_volume_signal(signal)
        
        with self.buffer_lock:
            self.buffer.append(stored_signal)
            logger.debug(f"Сигнал добавлен в кэш. Размер буфера: {len(self.buffer)}/{self.buffer_size}")
            
            # Проверяем, нужен ли принудительный сброс
            if len(self.buffer) >= self.buffer_size:
                logger.info("Буфер заполнен, принудительный сброс в БД")
                self._flush_buffer_unsafe()
    
    def flush_buffer(self):
        """Безопасный сброс буфера в базу данных"""
        with self.buffer_lock:
            self._flush_buffer_unsafe()
    
    def _flush_buffer_unsafe(self):
        """Небезопасный сброс буфера (должен вызываться под блокировкой)"""
        if not self.buffer:
            return
        
        signals_to_flush = self.buffer.copy()
        self.buffer.clear()
        
        # Сбрасываем пакетами для лучшей производительности
        for i in range(0, len(signals_to_flush), self.batch_size):
            batch = signals_to_flush[i:i + self.batch_size]
            inserted = self.database.insert_signals_batch(batch)
            
            if inserted < len(batch):
                logger.warning(f"Не все сигналы из пакета сохранены: {inserted}/{len(batch)}")
        
        logger.info(f"Сброшено {len(signals_to_flush)} сигналов из кэша в БД")
    
    def get_buffer_size(self) -> int:
        """Получение текущего размера буфера"""
        with self.buffer_lock:
            return len(self.buffer)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Получение статистики кэша"""
        return {
            'enabled': self.enabled,
            'buffer_size': self.get_buffer_size(),
            'max_buffer_size': self.buffer_size,
            'flush_interval': self.flush_interval,
            'batch_size': self.batch_size
        }
    
    def close(self):
        """Закрытие кэша с финальным сбросом данных"""
        logger.info("Закрытие кэша сигналов...")
        
        # Останавливаем поток сброса
        if self.flush_thread:
            self.stop_event.set()
            self.flush_thread.join(timeout=5)
        
        # Финальный сброс буфера
        self.flush_buffer()
        
        logger.info("Кэш сигналов закрыт")


class SignalsManager:
    """
    Главный менеджер для работы с сигналами
    Объединяет базу данных и кэш в единый интерфейс
    """
    
    def __init__(self, db_config: Dict[str, Any] = None, 
                 cache_config: Dict[str, Any] = None):
        """
        Инициализация менеджера сигналов
        
        Args:
            db_config (Dict): Конфигурация базы данных
            cache_config (Dict): Конфигурация кэша
        """
        self.database = SignalsDatabase(db_config)
        self.cache = SignalsCache(self.database, cache_config)
        
        logger.info("Менеджер сигналов инициализирован")
    
    def save_signal(self, signal: VolumeSignal):
        """
        Сохранение сигнала (через кэш или напрямую в БД)
        
        Args:
            signal (VolumeSignal): Сигнал от детектора
        """
        self.cache.add_signal(signal)
    
    def get_signals_history(self, pair: str = None, timeframe: str = None, 
                          limit: int = 100) -> List[Dict]:
        """
        Получение истории сигналов
        
        Args:
            pair (str): Фильтр по торговой паре
            timeframe (str): Фильтр по таймфрейму
            limit (int): Максимальное количество записей
            
        Returns:
            List[Dict]: Список сигналов
        """
        return self.database.get_signals(pair=pair, timeframe=timeframe, limit=limit)
    
    def get_full_statistics(self) -> Dict[str, Any]:
        """
        Получение полной статистики (БД + кэш)
        
        Returns:
            Dict: Полная статистика системы
        """
        db_stats = self.database.get_statistics()
        cache_stats = self.cache.get_cache_stats()
        
        return {
            'database': db_stats,
            'cache': cache_stats
        }
    
    def export_signals(self, filepath: str, pair: str = None, 
                      timeframe: str = None, limit: int = 1000) -> bool:
        """
        Экспорт сигналов в CSV файл
        
        Args:
            filepath (str): Путь к файлу для экспорта
            pair (str): Фильтр по торговой паре
            timeframe (str): Фильтр по таймфрейму
            limit (int): Максимальное количество записей
            
        Returns:
            bool: True если экспорт успешен
        """
        try:
            import csv
            
            signals = self.get_signals_history(pair=pair, timeframe=timeframe, limit=limit)
            
            if not signals:
                logger.warning("Нет сигналов для экспорта")
                return False
            
            # Записываем в CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = signals[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for signal in signals:
                    writer.writerow(signal)
            
            logger.info(f"Экспортировано {len(signals)} сигналов в {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка экспорта сигналов: {e}")
            return False
    
    def close(self):
        """Закрытие менеджера сигналов"""
        logger.info("Закрытие менеджера сигналов...")
        self.cache.close()
        self.database.close()
        logger.info("Менеджер сигналов закрыт")
