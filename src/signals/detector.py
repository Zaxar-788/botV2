"""
Детектор торговых сигналов для анализа аномалий объёма
"""

import logging
from typing import List, Dict, Optional, NamedTuple
from statistics import mean
from src.config import VOLUME_SPIKE_THRESHOLD, VOLUME_ANALYSIS_WINDOW

# Настройка логгера
logger = logging.getLogger(__name__)


class VolumeSignal(NamedTuple):
    """
    Структура сигнала о спайке объёма
    """
    timestamp: int          # Временная метка свечи
    pair: str              # Торговая пара
    current_volume: float  # Текущий объём
    average_volume: float  # Средний объём за период
    spike_ratio: float     # Во сколько раз превышен средний объём
    price: float          # Цена закрытия свечи
    message: str          # Текстовое описание сигнала


class VolumeSpikeDetector:
    """
    Детектор спайков объёма на основе анализа исторических данных
    
    Анализирует объём торгов и выявляет аномально высокие значения,
    которые могут указывать на важные рыночные события.
    """
    
    def __init__(self, threshold: float = VOLUME_SPIKE_THRESHOLD, 
                 window_size: int = VOLUME_ANALYSIS_WINDOW):
        """
        Инициализация детектора
        
        Args:
            threshold (float): Порог для определения спайка (во сколько раз объём должен превышать средний)
            window_size (int): Размер окна для расчёта среднего объёма
        """
        self.threshold = threshold
        self.window_size = window_size
        logger.info(f"Инициализирован детектор спайков объёма. Порог: {threshold}x, окно: {window_size}")
    
    def analyze_volume_spike(self, klines: List[Dict], pair: str = "BTC_USDT") -> Optional[VolumeSignal]:
        """
        Анализ спайков объёма в списке свечей
        
        Args:
            klines (List[Dict]): Список свечей с OHLCV данными
            pair (str): Торговая пара для анализа
            
        Returns:
            VolumeSignal: Объект сигнала если обнаружен спайк, иначе None
        """
        if not klines or len(klines) < self.window_size:
            logger.warning(f"Недостаточно данных для анализа. Требуется минимум {self.window_size} свечей")
            return None
        
        try:
            # Извлекаем объёмы из свечей (поле 'q')
            volumes = []
            for kline in klines:
                volume = float(kline.get('q', 0))
                volumes.append(volume)
            
            # Берём последнюю свечу для анализа
            current_kline = klines[-1]
            current_volume = volumes[-1]
            
            # Рассчитываем средний объём за предыдущие свечи (исключая текущую)
            analysis_volumes = volumes[-(self.window_size + 1):-1]  # Берём window_size свечей перед текущей
            
            if len(analysis_volumes) < self.window_size:
                # Если не хватает данных, берём все доступные (кроме текущей)
                analysis_volumes = volumes[:-1]
            
            if not analysis_volumes:
                logger.warning("Нет данных для расчёта среднего объёма")
                return None
            
            average_volume = mean(analysis_volumes)
            
            # Проверяем, есть ли спайк
            if average_volume > 0:
                spike_ratio = current_volume / average_volume
                
                logger.debug(f"Анализ объёма для {pair}: текущий={current_volume:.2f}, "
                           f"средний={average_volume:.2f}, коэффициент={spike_ratio:.2f}")
                
                if spike_ratio >= self.threshold:
                    # Обнаружен спайк объёма!
                    signal = VolumeSignal(
                        timestamp=int(current_kline.get('t', 0)),
                        pair=pair,
                        current_volume=current_volume,
                        average_volume=average_volume,
                        spike_ratio=spike_ratio,
                        price=float(current_kline.get('c', 0)),
                        message=f"🚨 СПАЙК ОБЪЁМА! {pair}: объём превышен в {spike_ratio:.1f}x "
                               f"(текущий: {current_volume:.0f}, средний: {average_volume:.0f})"
                    )
                    
                    logger.info(f"Обнаружен спайк объёма для {pair}: {spike_ratio:.1f}x от среднего")
                    return signal
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при анализе спайка объёма: {e}")
            return None
    
    def is_volume_anomaly(self, klines: List[Dict]) -> bool:
        """
        Простая проверка на наличие аномалии объёма
        
        Args:
            klines (List[Dict]): Список свечей
            
        Returns:
            bool: True если обнаружена аномалия, False иначе
        """
        signal = self.analyze_volume_spike(klines)
        return signal is not None
