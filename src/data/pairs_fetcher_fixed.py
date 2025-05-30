"""
Модуль для получения списка всех фьючерсных пар с биржи MEXC Futures
Поддержка периодического обновления и кэширования для масштабирования до 750+ пар
"""

import requests
import logging
import threading
import time
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from src.config import MEXC_API_BASE_URL

logger = logging.getLogger(__name__)


@dataclass
class PairInfo:
    """Информация о торговой паре"""
    symbol: str
    base_coin: str
    quote_coin: str
    price_scale: int
    qty_scale: int
    max_leverage: int
    min_leverage: int
    maintain_margin_rate: str
    initial_margin_rate: str
    risk_base_vol: str
    risk_incr_vol: str
    risk_incr_mmr: str
    risk_incr_imr: str
    risk_level_limit: int
    price_unit: str
    vol_unit: str
    min_vol: str
    max_vol: str
    bid_limit_price_rate: str
    ask_limit_price_rate: str
    taker_fee_rate: str
    maker_fee_rate: str
    maintenance_time: str
    is_new: bool
    concept_plate: List[str]


class MexcPairsFetcher:
    """
    Класс для получения и кэширования списка всех фьючерсных пар MEXC
    Поддерживает автоматическое обновление и высокую производительность
    """
    
    def __init__(self, update_interval: int = 3600):
        """
        Инициализация фетчера пар
        
        Args:
            update_interval (int): Интервал обновления в секундах (по умолчанию 1 час)
        """
        self.base_url = MEXC_API_BASE_URL
        self.update_interval = update_interval
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MEXC-MultiPair-Bot/2.0',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Кэш данных
        self._pairs_cache: List[str] = []
        self._pairs_info_cache: Dict[str, PairInfo] = {}
        self._last_update: Optional[datetime] = None
        self._update_lock = threading.RLock()
        self._update_thread: Optional[threading.Thread] = None
        self._stop_updates = threading.Event()
        
        # Статистика
        self.stats = {
            'total_updates': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'last_error': None,
            'cache_hits': 0
        }
        
        logger.info(f"Инициализирован MexcPairsFetcher с интервалом обновления {update_interval}s")
    
    def _fetch_symbols_from_api(self) -> Optional[Dict]:
        """
        Получение данных о символах напрямую от API
        
        Returns:
            Optional[Dict]: Ответ API или None в случае ошибки
        """
        try:
            url = f"{self.base_url}/contract/detail"
            logger.debug(f"Запрос к API: {url}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not isinstance(data, dict):
                logger.error(f"Неожиданный формат ответа API: {type(data)}")
                return None
                
            if 'success' in data and not data['success']:
                logger.error(f"API вернул ошибку: {data.get('errorMsg', 'Unknown error')}")
                return None
                
            return data
            
        except requests.exceptions.Timeout:
            logger.error("Таймаут при запросе к API MEXC")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Ошибка соединения с API MEXC")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP ошибка при запросе к API: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при запросе к API: {e}")
            return None
    
    def _parse_api_response(self, data: Dict) -> tuple[List[str], Dict[str, PairInfo]]:
        """
        Парсинг ответа API и извлечение информации о парах
        
        Args:
            data (Dict): Ответ от API
            
        Returns:
            tuple: (список символов, словарь с детальной информацией)
        """
        symbols = []
        pairs_info = {}
        
        try:
            # API MEXC возвращает данные в поле 'data'
            contracts = data.get('data', [])
            
            if not isinstance(contracts, list):
                logger.error(f"Ожидался список контрактов, получен: {type(contracts)}")
                return [], {}
            
            for contract in contracts:
                if not isinstance(contract, dict):
                    continue
                    
                symbol = contract.get('symbol')
                if not symbol:
                    continue
                
                try:
                    pair_info = PairInfo(
                        symbol=symbol,
                        base_coin=contract.get('baseCoin', ''),
                        quote_coin=contract.get('quoteCoin', ''),
                        price_scale=contract.get('priceScale', 0),
                        qty_scale=contract.get('volScale', 0),
                        max_leverage=contract.get('maxLeverage', 0),
                        min_leverage=contract.get('minLeverage', 0),
                        maintain_margin_rate=str(contract.get('maintenanceMarginRate', '')),
                        initial_margin_rate=str(contract.get('initialMarginRate', '')),
                        risk_base_vol=str(contract.get('riskBaseVol', '')),
                        risk_incr_vol=str(contract.get('riskIncrVol', '')),
                        risk_incr_mmr=str(contract.get('riskIncrMmr', '')),
                        risk_incr_imr=str(contract.get('riskIncrImr', '')),
                        risk_level_limit=contract.get('riskLevelLimit', 0),
                        price_unit=str(contract.get('priceUnit', '')),
                        vol_unit=str(contract.get('volUnit', '')),
                        min_vol=str(contract.get('minVol', '')),
                        max_vol=str(contract.get('maxVol', '')),
                        bid_limit_price_rate=str(contract.get('bidLimitPriceRate', '')),
                        ask_limit_price_rate=str(contract.get('askLimitPriceRate', '')),
                        taker_fee_rate=str(contract.get('takerFeeRate', '')),
                        maker_fee_rate=str(contract.get('makerFeeRate', '')),
                        maintenance_time=str(contract.get('maintenanceTime', '')),
                        is_new=contract.get('isNew', False),
                        concept_plate=contract.get('conceptPlate', [])
                    )
                    
                    symbols.append(symbol)
                    pairs_info[symbol] = pair_info
                    
                except Exception as e:
                    logger.warning(f"Ошибка при парсинге данных для символа {symbol}: {e}")
                    continue
            
            logger.info(f"Успешно спаршено {len(symbols)} торговых пар")
            return symbols, pairs_info
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге ответа API: {e}")
            return [], {}
    
    def _update_cache(self) -> bool:
        """
        Обновление кэша с данными о парах
        
        Returns:
            bool: True если обновление прошло успешно
        """
        with self._update_lock:
            try:
                self.stats['total_updates'] += 1
                
                logger.debug("Начинаю обновление кэша пар...")
                
                # Получаем данные от API
                api_data = self._fetch_symbols_from_api()
                if not api_data:
                    self.stats['failed_updates'] += 1
                    return False
                
                # Парсим ответ
                symbols, pairs_info = self._parse_api_response(api_data)
                
                if not symbols:
                    logger.error("Не получено ни одной торговой пары")
                    self.stats['failed_updates'] += 1
                    self.stats['last_error'] = "Empty symbols list"
                    return False
                
                # Обновляем кэш
                old_count = len(self._pairs_cache)
                self._pairs_cache = symbols
                self._pairs_info_cache = pairs_info
                self._last_update = datetime.now()
                
                self.stats['successful_updates'] += 1
                self.stats['last_error'] = None
                
                logger.info(f"Кэш обновлён: {len(symbols)} пар (было: {old_count})")
                
                # Логируем некоторые примеры пар для отладки
                if symbols:
                    sample_pairs = symbols[:5]
                    logger.debug(f"Примеры пар: {sample_pairs}")
                
                return True
                
            except Exception as e:
                logger.error(f"Критическая ошибка при обновлении кэша: {e}")
                self.stats['failed_updates'] += 1
                self.stats['last_error'] = str(e)
                return False
    
    def _background_updater(self):
        """Фоновый поток для периодического обновления"""
        logger.info("Запущен фоновый поток обновления пар")
        
        while not self._stop_updates.is_set():
            try:
                if self._update_cache():
                    logger.debug(f"Автоматическое обновление прошло успешно. Следующее через {self.update_interval}s")
                else:
                    logger.warning("Автоматическое обновление завершилось с ошибкой")
                
                # Ждём следующего обновления или сигнала остановки
                self._stop_updates.wait(self.update_interval)
                
            except Exception as e:
                logger.error(f"Ошибка в фоновом потоке обновления: {e}")
                self._stop_updates.wait(60)  # Ждём 1 минуту при ошибке
    
    def start_auto_update(self):
        """Запуск автоматического обновления в фоновом режиме"""
        if self._update_thread and self._update_thread.is_alive():
            logger.warning("Автоматическое обновление уже запущено")
            return
        
        self._stop_updates.clear()
        self._update_thread = threading.Thread(
            target=self._background_updater,
            name="MexcPairsFetcher-Updater",
            daemon=True
        )
        self._update_thread.start()
        logger.info("Автоматическое обновление пар запущено")
    
    def stop_auto_update(self):
        """Остановка автоматического обновления"""
        if not self._update_thread or not self._update_thread.is_alive():
            logger.warning("Автоматическое обновление не запущено")
            return
        
        logger.info("Останавливаю автоматическое обновление...")
        self._stop_updates.set()
        
        if self._update_thread:
            self._update_thread.join(timeout=5)
            if self._update_thread.is_alive():
                logger.warning("Не удалось остановить поток обновления за 5 секунд")
            else:
                logger.info("Автоматическое обновление остановлено")
    
    def get_all_pairs(self, force_update: bool = False) -> List[str]:
        """
        Получение списка всех доступных фьючерсных пар
        
        Args:
            force_update (bool): Принудительное обновление из API
            
        Returns:
            List[str]: Список символов торговых пар
        """
        # Проверяем, нужно ли обновить кэш
        if (force_update or 
            not self._pairs_cache or 
            not self._last_update or 
            datetime.now() - self._last_update > timedelta(seconds=self.update_interval)):
            
            logger.debug("Необходимо обновление кэша пар")
            if not self._update_cache():
                if self._pairs_cache:
                    logger.warning("Обновление не удалось, используем устаревший кэш")
                else:
                    logger.error("Обновление не удалось и кэш пуст")
                    return []
        else:
            self.stats['cache_hits'] += 1
            logger.debug("Используем данные из кэша")
        
        return self._pairs_cache.copy()
    
    def get_pair_info(self, symbol: str) -> Optional[PairInfo]:
        """
        Получение детальной информации о торговой паре
        
        Args:
            symbol (str): Символ торговой пары
            
        Returns:
            Optional[PairInfo]: Информация о паре или None
        """
        # Убеждаемся, что кэш заполнен
        if not self._pairs_info_cache:
            self.get_all_pairs()
        
        return self._pairs_info_cache.get(symbol)
    
    def get_pairs_by_base_coin(self, base_coin: str) -> List[str]:
        """
        Получение пар по базовой валюте
        
        Args:
            base_coin (str): Базовая валюта (например, 'BTC')
            
        Returns:
            List[str]: Список пар с указанной базовой валютой
        """
        # Убеждаемся, что кэш заполнен
        if not self._pairs_info_cache:
            self.get_all_pairs()
        
        pairs = []
        for symbol, info in self._pairs_info_cache.items():
            if info.base_coin.upper() == base_coin.upper():
                pairs.append(symbol)
        return pairs
    
    def get_pairs_by_quote_coin(self, quote_coin: str) -> List[str]:
        """
        Получение пар по котируемой валюте
        
        Args:
            quote_coin (str): Котируемая валюта (например, 'USDT')
            
        Returns:
            List[str]: Список пар с указанной котируемой валютой
        """
        # Убеждаемся, что кэш заполнен
        if not self._pairs_info_cache:
            self.get_all_pairs()
        
        pairs = []
        for symbol, info in self._pairs_info_cache.items():
            if info.quote_coin.upper() == quote_coin.upper():
                pairs.append(symbol)
        return pairs
    
    def filter_pairs_by_volume(self, min_volume: str = "1000000") -> List[str]:
        """
        Фильтрация пар по минимальному объёму
        
        Args:
            min_volume (str): Минимальный объём
            
        Returns:
            List[str]: Список пар, удовлетворяющих критерию
        """
        # Убеждаемся, что кэш заполнен
        if not self._pairs_info_cache:
            self.get_all_pairs()
            
        pairs = []
        try:
            min_vol_float = float(min_volume)
            for symbol, info in self._pairs_info_cache.items():
                try:
                    if info.min_vol and float(info.min_vol) >= min_vol_float:
                        pairs.append(symbol)
                except (ValueError, TypeError):
                    continue
        except ValueError:
            logger.error(f"Некорректное значение минимального объёма: {min_volume}")
        
        return pairs
    
    def get_cache_info(self) -> Dict:
        """
        Получение информации о состоянии кэша
        
        Returns:
            Dict: Информация о кэше и статистике
        """
        return {
            'pairs_count': len(self._pairs_cache),
            'last_update': self._last_update.isoformat() if self._last_update else None,
            'update_interval': self.update_interval,
            'auto_update_running': self._update_thread and self._update_thread.is_alive(),
            'stats': self.stats.copy()
        }
    
    def __enter__(self):
        """Поддержка контекстного менеджера"""
        self.start_auto_update()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Поддержка контекстного менеджера"""
        self.stop_auto_update()


# Глобальный экземпляр фетчера для удобства использования
_global_fetcher: Optional[MexcPairsFetcher] = None


def get_pairs_fetcher(update_interval: int = 3600) -> MexcPairsFetcher:
    """
    Получение глобального экземпляра фетчера пар
    
    Args:
        update_interval (int): Интервал обновления в секундах
        
    Returns:
        MexcPairsFetcher: Экземпляр фетчера
    """
    global _global_fetcher
    
    if _global_fetcher is None:
        _global_fetcher = MexcPairsFetcher(update_interval)
    
    return _global_fetcher


def get_all_futures_pairs(force_update: bool = False) -> List[str]:
    """
    Удобная функция для получения всех фьючерсных пар
    
    Args:
        force_update (bool): Принудительное обновление
        
    Returns:
        List[str]: Список всех доступных торговых пар
    """
    fetcher = get_pairs_fetcher()
    return fetcher.get_all_pairs(force_update=force_update)
