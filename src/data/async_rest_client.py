"""
Асинхронный REST API клиент для получения данных с биржи MEXC Futures
Оптимизирован для обработки 750+ торговых пар одновременно
"""

import aiohttp
import asyncio
import logging
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass
from src.config import MEXC_API_BASE_URL

logger = logging.getLogger(__name__)


@dataclass
class RequestResult:
    """Результат асинхронного запроса"""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    pair: Optional[str] = None
    timeframe: Optional[str] = None


class AsyncMexcRestClient:
    """
    Асинхронный клиент для работы с REST API биржи MEXC Futures
    
    ОСОБЕННОСТИ:
    - Полностью асинхронный (aiohttp)
    - Пул соединений для эффективности
    - Batch запросы для множества пар
    - Обработка rate limits
    - Автоматические повторы при ошибках
    - Масштабируется на 750+ пар
    """
    
    def __init__(self, 
                 max_connections: int = 100,
                 max_connections_per_host: int = 30,
                 request_timeout: int = 10,
                 max_retries: int = 3):
        """
        Инициализация асинхронного клиента
        
        Args:
            max_connections: Максимальное количество соединений в пуле
            max_connections_per_host: Максимальное количество соединений на хост
            request_timeout: Таймаут запроса в секундах
            max_retries: Максимальное количество повторных попыток
        """
        self.base_url = MEXC_API_BASE_URL
        self.request_timeout = request_timeout
        self.max_retries = max_retries
        
        # Настройка коннектора с пулом соединений
        self.connector = aiohttp.TCPConnector(
            limit=max_connections,
            limit_per_host=max_connections_per_host,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        # Таймауты
        self.timeout = aiohttp.ClientTimeout(
            total=request_timeout,
            connect=5,
            sock_read=request_timeout
        )
        
        # Сессия будет создана при первом использовании
        self._session: Optional[aiohttp.ClientSession] = None
        self._closed = False
        
        logger.debug(f"Инициализирован асинхронный MEXC REST клиент (пул: {max_connections})")
    
    async def _ensure_session(self):
        """Создание сессии при необходимости"""
        if self._session is None or self._session.closed:
            headers = {
                'User-Agent': 'AsyncMEXC-Bot/2.0',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            self._session = aiohttp.ClientSession(
                connector=self.connector,
                timeout=self.timeout,
                headers=headers
            )
            logger.debug("Создана новая aiohttp сессия")
    
    async def _make_request(self, url: str, params: Dict = None) -> RequestResult:
        """
        Выполнение HTTP запроса с повторными попытками
        
        Args:
            url: URL для запроса
            params: Параметры запроса
            
        Returns:
            RequestResult: Результат запроса
        """
        await self._ensure_session()
        
        for attempt in range(self.max_retries + 1):
            try:
                async with self._session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return RequestResult(success=True, data=data)
                    elif response.status == 429:
                        # Rate limit - ждем и повторяем
                        wait_time = min(2 ** attempt, 10)
                        logger.warning(f"Rate limit, ждем {wait_time}s (попытка {attempt + 1})")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        error_msg = f"HTTP {response.status}: {await response.text()}"
                        if attempt == self.max_retries:
                            return RequestResult(success=False, error=error_msg)
                        logger.warning(f"HTTP ошибка {response.status}, повтор {attempt + 1}")
                        
            except asyncio.TimeoutError:
                error_msg = f"Таймаут запроса после {self.request_timeout}s"
                if attempt == self.max_retries:
                    return RequestResult(success=False, error=error_msg)
                logger.warning(f"Таймаут, повтор {attempt + 1}")
                
            except Exception as e:
                error_msg = f"Ошибка запроса: {str(e)}"
                if attempt == self.max_retries:
                    return RequestResult(success=False, error=error_msg)
                logger.warning(f"Ошибка {str(e)}, повтор {attempt + 1}")
            
            # Экспоненциальная задержка между попытками
            if attempt < self.max_retries:
                wait_time = min(2 ** attempt, 5)
                await asyncio.sleep(wait_time)
        
        return RequestResult(success=False, error="Превышено количество попыток")
    
    async def get_klines_async(self, 
                               pair: str, 
                               interval: str = "Min1", 
                               limit: int = 50) -> Optional[List[Dict]]:
        """
        Асинхронное получение K-line (свечей) для торговой пары
        
        Args:
            pair: Торговая пара (например, BTC_USDT)
            interval: Таймфрейм (например, Min1)
            limit: Количество свечей
            
        Returns:
            List[Dict]: Список свечей или None при ошибке
        """
        try:
            url = f"{self.base_url}/contract/kline/{pair}"
            params = {
                'interval': interval,
                'limit': limit
            }
            
            logger.debug(f"📊 Асинхронный запрос: {pair} ({interval}, {limit} свечей)")
            
            result = await self._make_request(url, params)
            
            if not result.success:
                logger.error(f"❌ Ошибка получения данных для {pair} ({interval}): {result.error}")
                return None
            
            data = result.data
            if not (data.get('success') and 'data' in data):
                logger.error(f"❌ Неверный формат ответа для {pair} ({interval})")
                return None
            
            # Преобразуем данные в формат свечей
            raw_data = data['data']
            klines = []
            
            if 'time' in raw_data and len(raw_data['time']) > 0:
                count = len(raw_data['time'])
                for i in range(count):
                    kline = {
                        't': raw_data['time'][i] * 1000,  # В миллисекундах
                        'o': raw_data['open'][i],
                        'h': raw_data['high'][i],
                        'l': raw_data['low'][i],
                        'c': raw_data['close'][i],
                        'q': raw_data['vol'][i]  # volume
                    }
                    klines.append(kline)
            
            logger.debug(f"✅ Получено {len(klines)} свечей для {pair} ({interval})")
            return klines
            
        except Exception as e:
            logger.error(f"💥 Неожиданная ошибка для {pair} ({interval}): {e}")
            return None
    
    async def get_multiple_klines(self, 
                                  requests: List[Tuple[str, str, int]]) -> Dict[str, RequestResult]:
        """
        Массовое получение свечей для множества пар одновременно
        
        Args:
            requests: Список запросов [(pair, interval, limit), ...]
            
        Returns:
            Dict[str, RequestResult]: Результаты запросов {f"{pair}_{interval}": result}
        """
        logger.info(f"🚀 Массовый запрос свечей для {len(requests)} пар/таймфреймов")
        
        # Создаем задачи для всех запросов
        tasks = []
        task_keys = []
        
        for pair, interval, limit in requests:
            task_key = f"{pair}_{interval}"
            task = self.get_klines_async(pair, interval, limit)
            tasks.append(task)
            task_keys.append(task_key)
        
        # Выполняем все запросы одновременно
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Формируем результат
            response = {}
            successful = 0
            
            for i, (result, task_key) in enumerate(zip(results, task_keys)):
                if isinstance(result, Exception):
                    response[task_key] = RequestResult(
                        success=False,
                        error=str(result),
                        pair=requests[i][0],
                        timeframe=requests[i][1]
                    )
                elif result is not None:
                    response[task_key] = RequestResult(
                        success=True,
                        data=result,
                        pair=requests[i][0],
                        timeframe=requests[i][1]
                    )
                    successful += 1
                else:
                    response[task_key] = RequestResult(
                        success=False,
                        error="Пустой результат",
                        pair=requests[i][0],
                        timeframe=requests[i][1]
                    )
            
            logger.info(f"✅ Массовый запрос завершен: {successful}/{len(requests)} успешных")
            return response
            
        except Exception as e:
            logger.error(f"💥 Ошибка массового запроса: {e}")
            return {}
    
    async def get_batch_klines_for_pairs(self, 
                                         pairs: List[str], 
                                         timeframes: List[str], 
                                         limit: int = 50) -> Dict[str, Dict[str, Optional[List[Dict]]]]:
        """
        Получение свечей для множества пар и таймфреймов
        
        Args:
            pairs: Список торговых пар
            timeframes: Список таймфреймов
            limit: Количество свечей
            
        Returns:
            Dict: {pair: {timeframe: klines_data}}
        """
        # Формируем список всех запросов
        requests = []
        for pair in pairs:
            for timeframe in timeframes:
                requests.append((pair, timeframe, limit))
        
        logger.info(f"📊 Batch запрос: {len(pairs)} пар × {len(timeframes)} таймфреймов = {len(requests)} запросов")
        
        # Выполняем массовый запрос
        raw_results = await self.get_multiple_klines(requests)
        
        # Группируем результаты по парам и таймфреймам
        organized_results = {}
        for pair in pairs:
            organized_results[pair] = {}
            for timeframe in timeframes:
                task_key = f"{pair}_{timeframe}"
                result = raw_results.get(task_key)
                
                if result and result.success:
                    organized_results[pair][timeframe] = result.data
                else:
                    organized_results[pair][timeframe] = None
                    if result and result.error:
                        logger.warning(f"⚠️ Ошибка для {pair}/{timeframe}: {result.error}")
        
        successful_count = sum(
            1 for pair_data in organized_results.values()
            for tf_data in pair_data.values()
            if tf_data is not None
        )
        
        logger.info(f"✅ Batch результат: {successful_count}/{len(requests)} успешных запросов")
        return organized_results
    
    async def close(self):
        """Закрытие асинхронного клиента"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("Асинхронная сессия закрыта")
        
        if self.connector and not self.connector.closed:
            await self.connector.close()
            logger.debug("TCP коннектор закрыт")
        
        self._closed = True
    
    def __del__(self):
        """Деструктор для очистки ресурсов"""
        if not self._closed and self._session and not self._session.closed:
            logger.warning("Асинхронный клиент не был явно закрыт - рекомендуется вызывать close()")
    
    async def __aenter__(self):
        """Поддержка async context manager"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Поддержка async context manager"""
        await self.close()


# Утилитарные функции для batch операций
async def fetch_all_pairs_data(pairs: List[str], 
                               timeframes: List[str], 
                               limit: int = 50) -> Dict[str, Dict[str, Optional[List[Dict]]]]:
    """
    Удобная функция для получения данных по всем парам и таймфреймам
    
    Args:
        pairs: Список торговых пар
        timeframes: Список таймфреймов
        limit: Количество свечей
        
    Returns:
        Dict: Организованные данные по парам и таймфреймам
    """
    async with AsyncMexcRestClient() as client:
        return await client.get_batch_klines_for_pairs(pairs, timeframes, limit)


async def test_async_client():
    """Тестовая функция для проверки асинхронного клиента"""
    logger.info("🧪 Тестирование асинхронного REST клиента")
    
    test_pairs = ["BTC_USDT", "ETH_USDT", "BNB_USDT"]
    test_timeframes = ["Min1", "Min5"]
    
    async with AsyncMexcRestClient() as client:
        # Тест одиночного запроса
        logger.info("🔍 Тест одиночного запроса...")
        klines = await client.get_klines_async("BTC_USDT", "Min1", 10)
        logger.info(f"Результат: {len(klines) if klines else 0} свечей")
        
        # Тест batch запроса
        logger.info("🚀 Тест batch запроса...")
        batch_results = await client.get_batch_klines_for_pairs(test_pairs, test_timeframes, 20)
        
        success_count = 0
        for pair, timeframe_data in batch_results.items():
            for tf, data in timeframe_data.items():
                if data:
                    success_count += 1
                    logger.info(f"✅ {pair}/{tf}: {len(data)} свечей")
                else:
                    logger.warning(f"❌ {pair}/{tf}: данные не получены")
        
        logger.info(f"📊 Итого успешных: {success_count}/{len(test_pairs) * len(test_timeframes)}")


if __name__ == "__main__":
    # Запуск тестирования асинхронного клиента
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    from src.utils.logger import setup_main_logger
    setup_main_logger()
    
    asyncio.run(test_async_client())
