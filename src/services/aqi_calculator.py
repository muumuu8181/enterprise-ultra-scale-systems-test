from typing import Dict, Tuple, Optional, Any
import math

class AQICalculator:
    """
    US EPA方式によるAQI計算クラス
    """

    # Breakpoints: (Low, High, AQI_Low, AQI_High)
    # PM2.5 (µg/m³) - 1 decimal
    BP_PM25 = [
        (0.0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 350.4, 301, 400),
        (350.5, 500.4, 401, 500),
    ]

    # PM10 (µg/m³) - Integer
    BP_PM10 = [
        (0, 54, 0, 50),
        (55, 154, 51, 100),
        (155, 254, 101, 150),
        (255, 354, 151, 200),
        (355, 424, 201, 300),
        (425, 504, 301, 400),
        (505, 604, 401, 500),
    ]

    # CO (ppm) - 1 decimal
    BP_CO = [
        (0.0, 4.4, 0, 50),
        (4.5, 9.4, 51, 100),
        (9.5, 12.4, 101, 150),
        (12.5, 15.4, 151, 200),
        (15.5, 30.4, 201, 300),
        (30.5, 40.4, 301, 400),
        (40.5, 50.4, 401, 500),
    ]

    # NO2 (ppb) - 1 hour - Integer
    BP_NO2 = [
        (0, 53, 0, 50),
        (54, 100, 51, 100),
        (101, 360, 101, 150),
        (361, 649, 151, 200),
        (650, 1249, 201, 300),
        (1250, 1649, 301, 400),
        (1650, 2049, 401, 500),
    ]

    # O3 (ppm) - 8 hour - 3 decimal
    BP_O3 = [
        (0.000, 0.054, 0, 50),
        (0.055, 0.070, 51, 100),
        (0.071, 0.085, 101, 150),
        (0.086, 0.105, 151, 200),
        (0.106, 0.200, 201, 300),
        # 8-hr Ozone values do not define higher AQI values, usually switch to 1-hr
    ]

    @staticmethod
    def _truncate(value: float, decimals: int) -> float:
        """
        指定した桁数で切り捨てを行う (EPA基準準拠)
        例: 12.05, 1 -> 12.0
            12.09, 1 -> 12.0
        """
        factor = 10.0 ** decimals
        return math.floor(value * factor) / factor

    @classmethod
    def _calculate_sub_index(cls, concentration: float, breakpoints: list) -> int:
        for (bp_lo, bp_hi, i_lo, i_hi) in breakpoints:
            if bp_lo <= concentration <= bp_hi:
                return round(((i_hi - i_lo) / (bp_hi - bp_lo)) * (concentration - bp_lo) + i_lo)

        # If out of range (higher than max), extrapolate or cap?
        # Typically cap at 500 or return max defined
        if concentration > breakpoints[-1][1]:
             return 500 # Hazardous+
        return 0

    @classmethod
    def calculate_aqi(cls, pm25: Optional[float] = None, pm10: Optional[float] = None,
                      no2: Optional[float] = None, o3: Optional[float] = None,
                      co: Optional[float] = None) -> Tuple[int, Optional[str]]:
        """
        AQIを計算し、(AQI値, 主要汚染物質) を返す。
        """
        indices = {}

        if pm25 is not None:
            val = cls._truncate(pm25, 1)
            indices['pm25'] = cls._calculate_sub_index(val, cls.BP_PM25)
        if pm10 is not None:
            val = cls._truncate(pm10, 0)
            indices['pm10'] = cls._calculate_sub_index(val, cls.BP_PM10)
        if co is not None:
            val = cls._truncate(co, 1)
            indices['co'] = cls._calculate_sub_index(val, cls.BP_CO)
        if no2 is not None:
            val = cls._truncate(no2, 0)
            indices['no2'] = cls._calculate_sub_index(val, cls.BP_NO2)
        if o3 is not None:
            val = cls._truncate(o3, 3)
            indices['o3'] = cls._calculate_sub_index(val, cls.BP_O3)

        if not indices:
            return 0, None

        max_pollutant = max(indices, key=indices.get)
        return indices[max_pollutant], max_pollutant

    @staticmethod
    def get_aqi_level(aqi: int) -> str:
        if aqi <= 50:
            return "Good"
        elif aqi <= 100:
            return "Moderate"
        elif aqi <= 150:
            return "Unhealthy for Sensitive Groups"
        elif aqi <= 200:
            return "Unhealthy"
        elif aqi <= 300:
            return "Very Unhealthy"
        else:
            return "Hazardous"
