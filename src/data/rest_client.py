"""
REST API клиент для получения данных с биржи MEXC Futures
"""

import requests
import logging
from typing import List, Dict, Optional
from src.config import MEXC_API_BASE_URL, TRADING_PAIR, KLINE_INTERVAL, KLINE_LIMIT

# Настройка логгера
logger = logging.getLogger(__name__)


class MexcRestClient:
    """
    Клиент для работы с REST API биржи MEXC Futures
    Получает исторические данные по свечам (K-line)
    """
    
    def __init__(self):
        """Инициализация клиента"""
        self.base_url = MEXC_API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MEXC-Bot/1.0',
            'Content-Type': 'application/json'
        })
    
    def get_klines(self, pair: str = TRADING_PAIR, interval: str = KLINE_INTERVAL, 
                   limit: int = KLINE_LIMIT) -> Optional[List[Dict]]:
        """
        Получение минутных K-line (свечей) для указанной торговой пары
        
        Args:
            pair (str): Торговая пара (например, BTC_USDT)
            interval (str): Интервал свечей (Min1 для минутных)
            limit (int): Количество свечей для получения
            
        Returns:
            List[Dict]: Список свечей с полями:
                - o: цена открытия (open)
                - c: цена закрытия (close) 
                - h: максимальная цена (high)
                - l: минимальная цена (low)
                - q: объём (volume)
                - t: временная метка (timestamp)
        """
        try:
            # Формируем URL для запроса
            url = f"{self.base_url}/contract/kline/{pair}"
            params = {
                'interval': interval,
                'limit': limit
            }
            
            logger.info(f"Получаем {limit} свечей для пары {pair} с интервалом {interval}")
            
            # Выполняем запрос
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
              # Парсим ответ
            data = response.json()
            
            if data.get('success') and 'data' in data:
                raw_data = data['data']
                
                # Преобразуем данные в нужный формат (массив объектов OHLCV)
                klines = []
                if 'time' in raw_data and len(raw_data['time']) > 0:
                    count = len(raw_data['time'])
                    for i in range(count):
                        kline = {
                            't': raw_data['time'][i] * 1000,  # Переводим в миллисекунды
                            'o': raw_data['open'][i],
                            'h': raw_data['high'][i], 
                            'l': raw_data['low'][i],
                            'c': raw_data['close'][i],
                            'q': raw_data['vol'][i]  # volume
                        }
                        klines.append(kline)
                
                logger.info(f"Успешно получено {len(klines)} свечей")
                return klines
            else:
                logger.error(f"Ошибка в ответе API: {data}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе к API: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}")
            return None
    
    def get_latest_kline(self, pair: str = TRADING_PAIR) -> Optional[Dict]:
        """
        Получение последней свечи для анализа
        
        Args:
            pair (str): Торговая пара
            
        Returns:
            Dict: Последняя свеча или None при ошибке
        """
        klines = self.get_klines(pair=pair, limit=1)
        if klines and len(klines) > 0:
            return klines[0]
        return None
    
    def close(self):
        """Закрытие сессии"""
        self.session.close()
