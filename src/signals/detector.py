"""
Детектор торговых сигналов для анализа аномалий объёма
Поддержка мультипарности и мульти-таймфрейм анализа
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
    Поддержка мультипарности и мульти-таймфрейм
    """
    timestamp: int          # Временная метка свечи
    pair: str              # Торговая пара
    timeframe: str         # Таймфрейм анализа
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
    Поддерживает анализ нескольких пар и таймфреймов.
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
        logger.debug(f"Инициализирован детектор спайков объёма. Порог: {threshold}x, окно: {window_size}")
    
    def analyze_volume_spike(self, klines: List[Dict], pair: str, timeframe: str = "Min1") -> Optional[VolumeSignal]:
        """
        Анализ спайков объёма в списке свечей для конкретной пары и таймфрейма
        
        Args:
            klines (List[Dict]): Список свечей от API биржи
            pair (str): Торговая пара (например, BTC_USDT)
            timeframe (str): Таймфрейм анализа (например, Min1, Min5)
            
        Returns:
            VolumeSignal: Сигнал о спайке или None, если спайк не обнаружен
        """
        if not klines or len(klines) < self.window_size:
            logger.warning(f"Недостаточно данных для анализа {pair} ({timeframe}). "
                          f"Требуется минимум {self.window_size} свечей, получено {len(klines) if klines else 0}")
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
                logger.warning(f"Нет данных для расчёта среднего объёма {pair} ({timeframe})")
                return None
            
            average_volume = mean(analysis_volumes)
            
            # Проверяем, есть ли спайк
            if average_volume > 0:
                spike_ratio = current_volume / average_volume
                
                logger.debug(f"Анализ объёма для {pair} ({timeframe}): текущий={current_volume:.2f}, "
                           f"средний={average_volume:.2f}, коэффициент={spike_ratio:.2f}")
                
                if spike_ratio >= self.threshold:
                    # Обнаружен спайк объёма!
                    signal = VolumeSignal(
                        timestamp=int(current_kline.get('t', 0)),
                        pair=pair,
                        timeframe=timeframe,
                        current_volume=current_volume,
                        average_volume=average_volume,
                        spike_ratio=spike_ratio,
                        price=float(current_kline.get('c', 0)),
                        message=f"🚨 СПАЙК ОБЪЁМА! {pair} ({timeframe}): объём превышен в {spike_ratio:.1f}x "
                               f"(текущий: {current_volume:.0f}, средний: {average_volume:.0f})"
                    )
                    
                    logger.info(f"Обнаружен спайк объёма для {pair} ({timeframe}): {spike_ratio:.1f}x от среднего")
                    return signal
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при анализе спайка объёма для {pair} ({timeframe}): {e}")
            return None
    
    def is_volume_anomaly(self, klines: List[Dict], pair: str, timeframe: str = "Min1") -> bool:
        """
        Простая проверка на наличие аномалии объёма
        
        Args:
            klines (List[Dict]): Список свечей
            pair (str): Торговая пара
            timeframe (str): Таймфрейм
            
        Returns:
            bool: True если обнаружена аномалия, False иначе
        """
        signal = self.analyze_volume_spike(klines, pair, timeframe)
        return signal is not None
    
    def get_volume_statistics(self, klines: List[Dict]) -> Dict[str, float]:
        """
        Получение статистики по объёмам для анализа
        
        Args:
            klines (List[Dict]): Список свечей
            
        Returns:
            Dict: Статистика объёмов (средний, минимальный, максимальный)
        """
        if not klines:
            return {}
        
        try:
            volumes = [float(kline.get('q', 0)) for kline in klines]
            
            return {
                'average': mean(volumes),
                'min': min(volumes),
                'max': max(volumes),
                'count': len(volumes),
                'total': sum(volumes)
            }
        except Exception as e:
            logger.error(f"Ошибка при расчёте статистики объёмов: {e}")
            return {}
