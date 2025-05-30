# filepath: g:\Project_VSC\BotV2\src\data\rest_client.py
"""
REST API клиент для получения данных с биржи MEXC Futures
оддержка мультипарности и мульти-таймфрейм
"""

import requests
import logging
from typing import List, Dict, Optional
from src.config import MEXC_API_BASE_URL

# астройка логгера
logger = logging.getLogger(__name__)


class MexcRestClient:
    """
    лиент для работы с REST API биржи MEXC Futures
    олучает исторические данные по свечам (K-line) для любых пар и таймфреймов
    """
    
    def __init__(self):
        """нициализация клиента"""
        self.base_url = MEXC_API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MEXC-Bot/1.0',
            'Content-Type': 'application/json'
        })
        logger.debug("нициализирован MEXC REST клиент")
    
    def get_klines(self, pair: str, interval: str = "Min1", limit: int = 50) -> Optional[List[Dict]]:
        """
        олучение K-line (свечей) для указанной торговой пары и таймфрейма
        """
        try:
            # ормируем URL для запроса
            url = f"{self.base_url}/contract/kline/{pair}"
            params = {
                'interval': interval,
                'limit': limit
            }
            
            logger.debug(f"олучаем {limit} свечей для пары {pair} с интервалом {interval}")
            
            # ыполняем запрос
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # арсим ответ
            data = response.json()
            
            if data.get('success') and 'data' in data:
                raw_data = data['data']
                
                # реобразуем данные в нужный формат (массив объектов OHLCV)
                klines = []
                if 'time' in raw_data and len(raw_data['time']) > 0:
                    count = len(raw_data['time'])
                    for i in range(count):
                        kline = {
                            't': raw_data['time'][i] * 1000,  # ереводим в миллисекунды
                            'o': raw_data['open'][i],
                            'h': raw_data['high'][i], 
                            'l': raw_data['low'][i],
                            'c': raw_data['close'][i],
                            'q': raw_data['vol'][i]  # volume
                        }
                        klines.append(kline)
                
                logger.debug(f"спешно получено {len(klines)} свечей для {pair} ({interval})")
                return klines
            else:
                logger.error(f"шибка в ответе API для {pair} ({interval}): {data}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"шибка при запросе к API для {pair} ({interval}): {e}")
            return None
        except Exception as e:
            logger.error(f"еожиданная ошибка при получении данных для {pair} ({interval}): {e}")
            return None
    
    def get_latest_kline(self, pair: str, interval: str = "Min1") -> Optional[Dict]:
        """
        олучение последней свечи для анализа
        """
        klines = self.get_klines(pair=pair, interval=interval, limit=1)
        if klines and len(klines) > 0:
            return klines[0]
        return None
    
    def close(self):
        """акрытие сессии"""
        logger.debug("акрытие REST клиента")
        self.session.close()
