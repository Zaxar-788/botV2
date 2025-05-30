"""
Комплексные unit-тесты для модуля pairs_fetcher.py
Тестирует все компоненты: PairInfo, MexcPairsFetcher и utility функции
"""
import unittest
from unittest.mock import patch, Mock, MagicMock
import time
from threading import Thread
import sys
import os

# Добавляем src в sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.pairs_fetcher import (
    PairInfo, MexcPairsFetcher, 
    get_all_futures_pairs, get_pairs_fetcher
)


class TestPairInfo(unittest.TestCase):
    """Тесты для класса PairInfo"""
    
    def test_pair_info_creation(self):
        """Тест создания объекта PairInfo"""
        pair = PairInfo(
            symbol="BTC_USDT",
            displayName="BTC/USDT",
            quoteCoin="USDT",
            baseCoin="BTC"
        )
        
        self.assertEqual(pair.symbol, "BTC_USDT")
        self.assertEqual(pair.displayName, "BTC/USDT")
        self.assertEqual(pair.quoteCoin, "USDT")
        self.assertEqual(pair.baseCoin, "BTC")
        
    def test_pair_info_defaults(self):
        """Тест значений по умолчанию в PairInfo"""
        pair = PairInfo(symbol="ETH_USDT")
        
        self.assertEqual(pair.symbol, "ETH_USDT")
        self.assertIsNone(pair.displayName)
        self.assertIsNone(pair.quoteCoin)
        self.assertIsNone(pair.baseCoin)


class TestMexcPairsFetcher(unittest.TestCase):
    """Тесты для класса MexcPairsFetcher"""
    
    def setUp(self):
        """Подготовка перед каждым тестом"""
        self.fetcher = MexcPairsFetcher()
        
        # Мок API ответ
        self.mock_api_response = [
            {
                "symbol": "BTC_USDT",
                "displayName": "BTC/USDT",
                "baseCoin": "BTC",
                "quoteCoin": "USDT",
                "contractSize": 0.001,
                "minLeverage": 1,
                "maxLeverage": 125,
                "priceScale": 1,
                "volScale": 3,
                "amountScale": 3,
                "priceUnit": 1,
                "volUnit": 0.001,
                "minVol": 0.001,
                "maxVol": 10000,
                "bidLimitPriceRate": 0.1,
                "askLimitPriceRate": 0.1,
                "takerFeeRate": 0.0003,
                "makerFeeRate": 0.0001,
                "maintenanceMarginRate": 0.005,
                "initialMarginRate": 0.01,
                "riskBaseVol": 10000,
                "riskIncrVol": 200000,
                "riskIncrMmr": 0.005,
                "riskIncrImr": 0.01,
                "riskLevelLimit": 5,
                "priceCoefficientVariation": 0.1,
                "indexOrigin": ["BINANCE", "GATEIO", "HUOBI", "MXC"],
                "state": 0,
                "isNew": False,
                "isHot": True,
                "isHidden": False
            },
            {
                "symbol": "ETH_USDT",
                "displayName": "ETH/USDT",
                "baseCoin": "ETH",
                "quoteCoin": "USDT",
                "contractSize": 0.01,
                "minLeverage": 1,
                "maxLeverage": 100,
                "priceScale": 2,
                "volScale": 2,
                "amountScale": 2,
                "priceUnit": 0.01,
                "volUnit": 0.01,
                "minVol": 0.01,
                "maxVol": 8000,
                "bidLimitPriceRate": 0.1,
                "askLimitPriceRate": 0.1,
                "takerFeeRate": 0.0003,
                "makerFeeRate": 0.0001,
                "maintenanceMarginRate": 0.005,
                "initialMarginRate": 0.01,
                "riskBaseVol": 8000,
                "riskIncrVol": 160000,
                "riskIncrMmr": 0.005,
                "riskIncrImr": 0.01,
                "riskLevelLimit": 5,
                "priceCoefficientVariation": 0.1,
                "indexOrigin": ["BINANCE", "GATEIO", "HUOBI", "MXC"],
                "state": 0,
                "isNew": False,
                "isHot": True,
                "isHidden": False
            },
            {
                "symbol": "SOL_USDT",
                "displayName": "SOL/USDT",
                "baseCoin": "SOL",
                "quoteCoin": "USDT",
                "contractSize": 0.1,
                "minLeverage": 1,
                "maxLeverage": 50,
                "priceScale": 3,
                "volScale": 1,
                "amountScale": 1,
                "priceUnit": 0.001,
                "volUnit": 0.1,
                "minVol": 0.1,
                "maxVol": 50000,
                "bidLimitPriceRate": 0.1,
                "askLimitPriceRate": 0.1,
                "takerFeeRate": 0.0003,
                "makerFeeRate": 0.0001,
                "maintenanceMarginRate": 0.01,
                "initialMarginRate": 0.02,
                "riskBaseVol": 50000,
                "riskIncrVol": 100000,
                "riskIncrMmr": 0.005,
                "riskIncrImr": 0.01,
                "riskLevelLimit": 5,
                "priceCoefficientVariation": 0.1,
                "indexOrigin": ["BINANCE", "GATEIO", "HUOBI", "MXC"],
                "state": 0,
                "isNew": True,
                "isHot": False,
                "isHidden": False
            }
        ]
    
    def tearDown(self):
        """Очистка после каждого теста"""
        if hasattr(self.fetcher, '_update_thread') and self.fetcher._update_thread:
            self.fetcher.stop_periodic_updates()
            if self.fetcher._update_thread.is_alive():
                self.fetcher._update_thread.join(timeout=1)
    
    @patch('requests.Session.get')
    def test_fetch_symbols_from_api_success(self, mock_get):
        """Тест успешного получения данных от API"""
        # Настройка мока
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": self.mock_api_response}
        mock_get.return_value = mock_response
        
        # Тестирование
        result = self.fetcher._fetch_symbols_from_api()
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].symbol, "BTC_USDT")
        self.assertEqual(result[0].baseCoin, "BTC")
        self.assertEqual(result[0].quoteCoin, "USDT")
    
    @patch('requests.Session.get')
    def test_fetch_symbols_from_api_failure(self, mock_get):
        """Тест неудачного запроса к API"""
        # Настройка мока для имитации ошибки
        mock_get.side_effect = Exception("Connection error")
        
        # Тестирование
        result = self.fetcher._fetch_symbols_from_api()
        
        self.assertIsNone(result)
    
    @patch.object(MexcPairsFetcher, '_fetch_symbols_from_api')
    def test_update_cache_success(self, mock_fetch):
        """Тест успешного обновления кэша"""
        # Настройка мока
        mock_fetch.return_value = [
            PairInfo(symbol="BTC_USDT", baseCoin="BTC", quoteCoin="USDT"),
            PairInfo(symbol="ETH_USDT", baseCoin="ETH", quoteCoin="USDT"),
            PairInfo(symbol="SOL_USDT", baseCoin="SOL", quoteCoin="USDT")
        ]
        
        # Тестирование
        result = self.fetcher._update_cache()
        
        self.assertTrue(result)
        self.assertEqual(len(self.fetcher._pairs_cache), 3)
        self.assertIsNotNone(self.fetcher._last_update)
        self.assertEqual(self.fetcher.stats['successful_updates'], 1)
    
    @patch.object(MexcPairsFetcher, '_fetch_symbols_from_api')
    def test_update_cache_failure(self, mock_fetch):
        """Тест неудачного обновления кэша"""
        # Настройка мока для имитации ошибки
        mock_fetch.return_value = None
        
        # Тестирование
        result = self.fetcher._update_cache()
        
        self.assertFalse(result)
        self.assertEqual(len(self.fetcher._pairs_cache), 0)
        self.assertEqual(self.fetcher.stats['failed_updates'], 1)
    
    def test_is_cache_valid_empty_cache(self):
        """Тест валидации пустого кэша"""
        result = self.fetcher._is_cache_valid()
        self.assertFalse(result)
    
    @patch.object(MexcPairsFetcher, '_fetch_symbols_from_api')
    def test_is_cache_valid_fresh_cache(self, mock_fetch):
        """Тест валидации свежего кэша"""
        # Заполняем кэш
        mock_fetch.return_value = [PairInfo(symbol="BTC_USDT")]
        self.fetcher._update_cache()
        
        # Тестирование
        result = self.fetcher._is_cache_valid()
        self.assertTrue(result)
    
    @patch.object(MexcPairsFetcher, '_fetch_symbols_from_api')
    def test_is_cache_valid_expired_cache(self, mock_fetch):
        """Тест валидации устаревшего кэша"""
        # Заполняем кэш
        mock_fetch.return_value = [PairInfo(symbol="BTC_USDT")]
        self.fetcher._update_cache()
        
        # Имитируем устаревший кэш
        self.fetcher._last_update = time.time() - 3700  # Более часа назад
        
        # Тестирование
        result = self.fetcher._is_cache_valid()
        self.assertFalse(result)
    
    @patch.object(MexcPairsFetcher, '_fetch_symbols_from_api')
    def test_get_all_pairs(self, mock_fetch):
        """Тест получения всех пар"""
        # Настройка мока
        mock_pairs = [
            PairInfo(symbol="BTC_USDT", baseCoin="BTC", quoteCoin="USDT"),
            PairInfo(symbol="ETH_USDT", baseCoin="ETH", quoteCoin="USDT")
        ]
        mock_fetch.return_value = mock_pairs
        
        # Тестирование
        result = self.fetcher.get_all_pairs()
        
        self.assertEqual(len(result), 2)
        self.assertIn("BTC_USDT", result)
        self.assertIn("ETH_USDT", result)
    
    @patch.object(MexcPairsFetcher, '_fetch_symbols_from_api')
    def test_get_pair_info(self, mock_fetch):
        """Тест получения информации о конкретной паре"""
        # Настройка мока
        mock_pairs = [
            PairInfo(symbol="BTC_USDT", baseCoin="BTC", quoteCoin="USDT", displayName="BTC/USDT")
        ]
        mock_fetch.return_value = mock_pairs
        
        # Тестирование
        info = self.fetcher.get_pair_info("BTC_USDT")
        
        self.assertIsNotNone(info)
        self.assertEqual(info.symbol, "BTC_USDT")
        self.assertEqual(info.baseCoin, "BTC")
        self.assertEqual(info.quoteCoin, "USDT")
        
        # Тест несуществующей пары
        info = self.fetcher.get_pair_info("NONEXISTENT")
        self.assertIsNone(info)
    
    @patch.object(MexcPairsFetcher, '_fetch_symbols_from_api')
    def test_get_pairs_by_quote_coin(self, mock_fetch):
        """Тест фильтрации по котируемой валюте"""
        # Настройка мока
        mock_pairs = [
            PairInfo(symbol="BTC_USDT", baseCoin="BTC", quoteCoin="USDT"),
            PairInfo(symbol="ETH_USDT", baseCoin="ETH", quoteCoin="USDT"),
            PairInfo(symbol="BTC_USD", baseCoin="BTC", quoteCoin="USD")
        ]
        mock_fetch.return_value = mock_pairs
        
        # Тестирование
        usdt_pairs = self.fetcher.get_pairs_by_quote_coin("USDT")
        usd_pairs = self.fetcher.get_pairs_by_quote_coin("USD")
        
        self.assertEqual(len(usdt_pairs), 2)
        self.assertIn("BTC_USDT", usdt_pairs)
        self.assertIn("ETH_USDT", usdt_pairs)
        
        self.assertEqual(len(usd_pairs), 1)
        self.assertIn("BTC_USD", usd_pairs)
    
    @patch.object(MexcPairsFetcher, '_fetch_symbols_from_api')
    def test_get_pairs_by_base_coin(self, mock_fetch):
        """Тест фильтрации по базовой валюте"""
        # Настройка мока
        mock_pairs = [
            PairInfo(symbol="BTC_USDT", baseCoin="BTC", quoteCoin="USDT"),
            PairInfo(symbol="BTC_USD", baseCoin="BTC", quoteCoin="USD"),
            PairInfo(symbol="ETH_USDT", baseCoin="ETH", quoteCoin="USDT")
        ]
        mock_fetch.return_value = mock_pairs
        
        # Тестирование
        btc_pairs = self.fetcher.get_pairs_by_base_coin("BTC")
        eth_pairs = self.fetcher.get_pairs_by_base_coin("ETH")
        
        self.assertEqual(len(btc_pairs), 2)
        self.assertIn("BTC_USDT", btc_pairs)
        self.assertIn("BTC_USD", btc_pairs)
        
        self.assertEqual(len(eth_pairs), 1)
        self.assertIn("ETH_USDT", eth_pairs)
    
    @patch.object(MexcPairsFetcher, '_fetch_symbols_from_api')
    def test_get_cache_info(self, mock_fetch):
        """Тест получения информации о кэше"""
        # Тест пустого кэша
        info = self.fetcher.get_cache_info()
        self.assertEqual(info['pairs_count'], 0)
        self.assertIsNone(info['last_update'])
        self.assertFalse(info['is_valid'])
        
        # Заполняем кэш и тестируем
        mock_fetch.return_value = [PairInfo(symbol="BTC_USDT")]
        self.fetcher._update_cache()
        
        info = self.fetcher.get_cache_info()
        self.assertEqual(info['pairs_count'], 1)
        self.assertIsNotNone(info['last_update'])
        self.assertTrue(info['is_valid'])
    
    @patch.object(MexcPairsFetcher, '_fetch_symbols_from_api')
    def test_get_stats(self, mock_fetch):
        """Тест получения статистики"""
        # Успешное обновление
        mock_fetch.return_value = [PairInfo(symbol="BTC_USDT")]
        self.fetcher._update_cache()
        
        # Неудачное обновление
        mock_fetch.return_value = None
        self.fetcher._update_cache()
        
        stats = self.fetcher.get_stats()
        self.assertEqual(stats['successful_updates'], 1)
        self.assertEqual(stats['failed_updates'], 1)
        self.assertEqual(stats['total_requests'], 2)
    
    @patch.object(MexcPairsFetcher, '_fetch_symbols_from_api')
    def test_periodic_updates(self, mock_fetch):
        """Тест периодических обновлений"""
        mock_fetch.return_value = [PairInfo(symbol="BTC_USDT")]
        
        # Запускаем периодические обновления с очень малым интервалом
        self.fetcher.start_periodic_updates(interval_seconds=0.1)
        
        # Ждём несколько обновлений
        time.sleep(0.3)
        
        # Останавливаем обновления
        self.fetcher.stop_periodic_updates()
        
        # Проверяем, что произошло несколько обновлений
        stats = self.fetcher.get_stats()
        self.assertGreater(stats['successful_updates'], 1)


class TestUtilityFunctions(unittest.TestCase):
    """Тесты для utility функций"""
    
    @patch.object(MexcPairsFetcher, '_fetch_symbols_from_api')
    def test_get_all_futures_pairs(self, mock_fetch):
        """Тест функции get_all_futures_pairs"""
        mock_fetch.return_value = [
            PairInfo(symbol="BTC_USDT"),
            PairInfo(symbol="ETH_USDT")
        ]
        
        pairs = get_all_futures_pairs()
        
        self.assertEqual(len(pairs), 2)
        self.assertIn("BTC_USDT", pairs)
        self.assertIn("ETH_USDT", pairs)
    
    def test_get_pairs_fetcher(self):
        """Тест функции get_pairs_fetcher"""
        fetcher = get_pairs_fetcher()
        
        self.assertIsInstance(fetcher, MexcPairsFetcher)
        
        # Проверяем, что возвращается тот же экземпляр (singleton)
        fetcher2 = get_pairs_fetcher()
        self.assertIs(fetcher, fetcher2)


if __name__ == '__main__':
    # Настройка подробного вывода
    unittest.main(verbosity=2)
