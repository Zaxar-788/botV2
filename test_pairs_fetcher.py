#!/usr/bin/env python3
"""
Тесты для модуля получения торговых пар MEXC Futures
"""

import sys
import os
import unittest
import time
from unittest.mock import patch, Mock

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data.pairs_fetcher import MexcPairsFetcher, get_all_futures_pairs, PairInfo


class TestMexcPairsFetcher(unittest.TestCase):
    """Тесты для класса MexcPairsFetcher"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.fetcher = MexcPairsFetcher(update_interval=10)
        
        # Мок данные для тестирования
        self.mock_api_response = {
            "success": True,
            "data": [
                {
                    "symbol": "BTC_USDT",
                    "baseCoin": "BTC",
                    "quoteCoin": "USDT",
                    "priceScale": 2,
                    "qtyScale": 6,
                    "maxLeverage": 125,
                    "minLeverage": 1,
                    "maintainMarginRate": "0.005",
                    "initialMarginRate": "0.008",
                    "riskBaseVol": "1000000",
                    "riskIncrVol": "500000",
                    "riskIncrMmr": "0.001",
                    "riskIncrImr": "0.002",
                    "riskLevelLimit": 5,
                    "priceUnit": "0.01",
                    "volUnit": "0.000001",
                    "minVol": "0.001",
                    "maxVol": "10000000",
                    "bidLimitPriceRate": "0.1",
                    "askLimitPriceRate": "0.1",
                    "takerFeeRate": "0.0006",
                    "makerFeeRate": "0.0002",
                    "maintenanceTime": "",
                    "isNew": False,
                    "conceptPlate": ["DeFi", "Layer1"]
                },
                {
                    "symbol": "ETH_USDT",
                    "baseCoin": "ETH",
                    "quoteCoin": "USDT",
                    "priceScale": 2,
                    "qtyScale": 5,
                    "maxLeverage": 100,
                    "minLeverage": 1,
                    "maintainMarginRate": "0.005",
                    "initialMarginRate": "0.01",
                    "riskBaseVol": "500000",
                    "riskIncrVol": "250000",
                    "riskIncrMmr": "0.001",
                    "riskIncrImr": "0.002",
                    "riskLevelLimit": 5,
                    "priceUnit": "0.01",
                    "volUnit": "0.00001",
                    "minVol": "0.01",
                    "maxVol": "5000000",
                    "bidLimitPriceRate": "0.1",
                    "askLimitPriceRate": "0.1",
                    "takerFeeRate": "0.0006",
                    "makerFeeRate": "0.0002",
                    "maintenanceTime": "",
                    "isNew": True,
                    "conceptPlate": ["DeFi"]
                },
                {
                    "symbol": "BNB_BTC",
                    "baseCoin": "BNB",
                    "quoteCoin": "BTC",
                    "priceScale": 8,
                    "qtyScale": 3,
                    "maxLeverage": 50,
                    "minLeverage": 1,
                    "maintainMarginRate": "0.01",
                    "initialMarginRate": "0.02",
                    "riskBaseVol": "100000",
                    "riskIncrVol": "50000",
                    "riskIncrMmr": "0.002",
                    "riskIncrImr": "0.004",
                    "riskLevelLimit": 3,
                    "priceUnit": "0.00000001",
                    "volUnit": "0.001",
                    "minVol": "0.1",
                    "maxVol": "1000000",
                    "bidLimitPriceRate": "0.05",
                    "askLimitPriceRate": "0.05",
                    "takerFeeRate": "0.0008",
                    "makerFeeRate": "0.0003",
                    "maintenanceTime": "",
                    "isNew": False,
                    "conceptPlate": []
                }
            ]
        }
    
    def tearDown(self):
        """Очистка после каждого теста"""
        self.fetcher.stop_auto_update()
    
    @patch('src.data.pairs_fetcher.requests.Session.get')
    def test_fetch_symbols_from_api_success(self, mock_get):
        """Тест успешного получения данных от API"""
        # Настройка мока
        mock_response = Mock()
        mock_response.json.return_value = self.mock_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Тестирование
        result = self.fetcher._fetch_symbols_from_api()
        
        self.assertIsNotNone(result)
        self.assertEqual(result, self.mock_api_response)
        mock_get.assert_called_once()
    
    @patch('src.data.pairs_fetcher.requests.Session.get')
    def test_fetch_symbols_from_api_timeout(self, mock_get):
        """Тест обработки таймаута"""
        # Настройка мока для имитации таймаута
        mock_get.side_effect = Exception("Timeout")
        
        # Тестирование
        result = self.fetcher._fetch_symbols_from_api()
        
        self.assertIsNone(result)
    
    def test_parse_api_response_success(self):
        """Тест успешного парсинга ответа API"""
        symbols, pairs_info = self.fetcher._parse_api_response(self.mock_api_response)
        
        # Проверяем количество символов
        self.assertEqual(len(symbols), 3)
        self.assertEqual(len(pairs_info), 3)
        
        # Проверяем содержание
        expected_symbols = ["BTC_USDT", "ETH_USDT", "BNB_BTC"]
        self.assertEqual(set(symbols), set(expected_symbols))
        
        # Проверяем детальную информацию
        btc_info = pairs_info["BTC_USDT"]
        self.assertEqual(btc_info.symbol, "BTC_USDT")
        self.assertEqual(btc_info.base_coin, "BTC")
        self.assertEqual(btc_info.quote_coin, "USDT")
        self.assertEqual(btc_info.max_leverage, 125)
        self.assertFalse(btc_info.is_new)
        self.assertEqual(btc_info.concept_plate, ["DeFi", "Layer1"])
        
        eth_info = pairs_info["ETH_USDT"]
        self.assertTrue(eth_info.is_new)
        self.assertEqual(eth_info.concept_plate, ["DeFi"])
    
    def test_parse_api_response_empty_data(self):
        """Тест парсинга пустого ответа"""
        empty_response = {"success": True, "data": []}
        symbols, pairs_info = self.fetcher._parse_api_response(empty_response)
        
        self.assertEqual(len(symbols), 0)
        self.assertEqual(len(pairs_info), 0)
    
        @patch.object(MexcPairsFetcher, '_fetch_symbols_from_api')
    def test_update_cache_success(self, mock_fetch):
        """Тест успешного обновления кэша"""
        # Настройка мока
        mock_fetch.return_value = self.mock_api_response
        
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
    
    @patch.object(MexcPairsFetcher, '_update_cache')
    def test_get_all_pairs_with_cache(self, mock_update):
        """Тест получения пар с использованием кэша"""
        from datetime import datetime
        # Предзаполняем кэш
        self.fetcher._pairs_cache = ["BTC_USDT", "ETH_USDT"]
        self.fetcher._last_update = datetime.now()
        mock_update.return_value = True
        
        # Тестирование (без принудительного обновления)
        pairs = self.fetcher.get_all_pairs(force_update=False)
        
        self.assertEqual(len(pairs), 2)
        self.assertEqual(set(pairs), {"BTC_USDT", "ETH_USDT"})
        # Обновление не должно было быть вызвано
        mock_update.assert_not_called()
    
    @patch.object(MexcPairsFetcher, '_update_cache')
    def test_get_all_pairs_force_update(self, mock_update):
        """Тест принудительного обновления"""
        mock_update.return_value = True
        
        # Тестирование с принудительным обновлением
        pairs = self.fetcher.get_all_pairs(force_update=True)
        
        # Обновление должно было быть вызвано
        mock_update.assert_called_once()
    
    def test_filtering_methods(self):
        """Тест методов фильтрации"""
        # Заполняем кэш тестовыми данными
        self.fetcher._pairs_cache = ["BTC_USDT", "ETH_USDT", "BNB_BTC"]
        self.fetcher._pairs_info_cache = {
            "BTC_USDT": PairInfo(
                symbol="BTC_USDT", base_coin="BTC", quote_coin="USDT",
                price_scale=2, qty_scale=6, max_leverage=125, min_leverage=1,
                maintain_margin_rate="0.005", initial_margin_rate="0.008",
                risk_base_vol="1000000", risk_incr_vol="500000",
                risk_incr_mmr="0.001", risk_incr_imr="0.002",
                risk_level_limit=5, price_unit="0.01", vol_unit="0.000001",
                min_vol="0.001", max_vol="10000000",
                bid_limit_price_rate="0.1", ask_limit_price_rate="0.1",
                taker_fee_rate="0.0006", maker_fee_rate="0.0002",
                maintenance_time="", is_new=False, concept_plate=[]
            ),
            "ETH_USDT": PairInfo(
                symbol="ETH_USDT", base_coin="ETH", quote_coin="USDT",
                price_scale=2, qty_scale=5, max_leverage=100, min_leverage=1,
                maintain_margin_rate="0.005", initial_margin_rate="0.01",
                risk_base_vol="500000", risk_incr_vol="250000",
                risk_incr_mmr="0.001", risk_incr_imr="0.002",
                risk_level_limit=5, price_unit="0.01", vol_unit="0.00001",
                min_vol="0.01", max_vol="5000000",
                bid_limit_price_rate="0.1", ask_limit_price_rate="0.1",
                taker_fee_rate="0.0006", maker_fee_rate="0.0002",
                maintenance_time="", is_new=True, concept_plate=[]
            ),
            "BNB_BTC": PairInfo(
                symbol="BNB_BTC", base_coin="BNB", quote_coin="BTC",
                price_scale=8, qty_scale=3, max_leverage=50, min_leverage=1,
                maintain_margin_rate="0.01", initial_margin_rate="0.02",
                risk_base_vol="100000", risk_incr_vol="50000",
                risk_incr_mmr="0.002", risk_incr_imr="0.004",
                risk_level_limit=3, price_unit="0.00000001", vol_unit="0.001",
                min_vol="0.1", max_vol="1000000",
                bid_limit_price_rate="0.05", ask_limit_price_rate="0.05",
                taker_fee_rate="0.0008", maker_fee_rate="0.0003",
                maintenance_time="", is_new=False, concept_plate=[]
            )
        }
        
        # Тест фильтрации по котируемой валюте
        usdt_pairs = self.fetcher.get_pairs_by_quote_coin("USDT")
        self.assertEqual(set(usdt_pairs), {"BTC_USDT", "ETH_USDT"})
        
        btc_pairs = self.fetcher.get_pairs_by_quote_coin("BTC")
        self.assertEqual(set(btc_pairs), {"BNB_BTC"})
        
        # Тест фильтрации по базовой валюте
        btc_base_pairs = self.fetcher.get_pairs_by_base_coin("BTC")
        self.assertEqual(set(btc_base_pairs), {"BTC_USDT"})
        
        eth_base_pairs = self.fetcher.get_pairs_by_base_coin("ETH")
        self.assertEqual(set(eth_base_pairs), {"ETH_USDT"})
    
    def test_get_pair_info(self):
        """Тест получения информации о паре"""
        # Заполняем кэш
        test_info = PairInfo(
            symbol="TEST_USDT", base_coin="TEST", quote_coin="USDT",
            price_scale=4, qty_scale=2, max_leverage=75, min_leverage=1,
            maintain_margin_rate="0.01", initial_margin_rate="0.015",
            risk_base_vol="200000", risk_incr_vol="100000",
            risk_incr_mmr="0.001", risk_incr_imr="0.002",
            risk_level_limit=4, price_unit="0.0001", vol_unit="0.01",
            min_vol="1", max_vol="1000000",
            bid_limit_price_rate="0.08", ask_limit_price_rate="0.08",
            taker_fee_rate="0.0005", maker_fee_rate="0.0001",
            maintenance_time="", is_new=True, concept_plate=["Test"]
        )
        self.fetcher._pairs_info_cache["TEST_USDT"] = test_info
        
        # Тестирование
        info = self.fetcher.get_pair_info("TEST_USDT")
        self.assertIsNotNone(info)
        self.assertEqual(info.symbol, "TEST_USDT")
        self.assertEqual(info.max_leverage, 75)
        self.assertTrue(info.is_new)
        
        # Тест несуществующей пары
        info = self.fetcher.get_pair_info("NONEXISTENT_PAIR")
        self.assertIsNone(info)
      def test_cache_info(self):
        """Тест получения информации о кэше"""
        from datetime import datetime
        # Заполняем кэш
        self.fetcher._pairs_cache = ["BTC_USDT", "ETH_USDT"]
        self.fetcher._last_update = datetime.now()
        self.fetcher.stats['successful_updates'] = 5
        
        cache_info = self.fetcher.get_cache_info()
        
        self.assertEqual(cache_info['pairs_count'], 2)
        self.assertIsNotNone(cache_info['last_update'])
        self.assertEqual(cache_info['update_interval'], 10)
        self.assertFalse(cache_info['auto_update_running'])
        self.assertEqual(cache_info['stats']['successful_updates'], 5)
    
    def test_auto_update_control(self):
        """Тест управления автоматическим обновлением"""
        # Проверяем начальное состояние
        cache_info = self.fetcher.get_cache_info()
        self.assertFalse(cache_info['auto_update_running'])
        
        # Запускаем автообновление
        self.fetcher.start_auto_update()
        time.sleep(0.1)  # Даём время потоку запуститься
        
        cache_info = self.fetcher.get_cache_info()
        self.assertTrue(cache_info['auto_update_running'])
        
        # Останавливаем автообновление
        self.fetcher.stop_auto_update()
        
        cache_info = self.fetcher.get_cache_info()
        self.assertFalse(cache_info['auto_update_running'])


class TestGlobalFunctions(unittest.TestCase):
    """Тесты для глобальных функций"""
    
    @patch('src.data.pairs_fetcher.get_pairs_fetcher')
    def test_get_all_futures_pairs(self, mock_get_fetcher):
        """Тест глобальной функции получения пар"""
        # Настройка мока
        mock_fetcher = Mock()
        mock_fetcher.get_all_pairs.return_value = ["BTC_USDT", "ETH_USDT"]
        mock_get_fetcher.return_value = mock_fetcher
        
        # Тестирование
        pairs = get_all_futures_pairs(force_update=True)
        
        self.assertEqual(len(pairs), 2)
        self.assertEqual(set(pairs), {"BTC_USDT", "ETH_USDT"})
        mock_fetcher.get_all_pairs.assert_called_once_with(force_update=True)


if __name__ == '__main__':
    # Настройка логирования для тестов
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Запуск тестов
    unittest.main(verbosity=2)
