"""
Rainfall Intelligence Module for MonsoonWatch India.
Calculates multi-window accumulations, Antecedent Precipitation Index (API),
and maps rainfall against official India Meteorological Department (IMD) thresholds.
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import math


class IMDThreshold:
    """Official IMD Rainfall Intensity Classification (in mm / 24 hours)."""
    NO_RAIN = (0.0, 0.0, "No Rain", "green")
    VERY_LIGHT = (0.1, 2.4, "Very Light Rain", "green")
    LIGHT = (2.5, 15.5, "Light Rain", "green")
    MODERATE = (15.6, 64.4, "Moderate Rain", "yellow")
    HEAVY = (64.5, 115.5, "Heavy Rain (Yellow Alert)", "amber")
    VERY_HEAVY = (115.6, 204.4, "Very Heavy Rain (Orange Alert)", "orange")
    EXTREMELY_HEAVY = (204.5, 9999.0, "Extremely Heavy Rain (Red Alert)", "red")

    @classmethod
    def classify_24h(cls, rainfall_mm: float) -> Tuple[str, str, str]:
        """Returns (Category Name, IMD Color Code, Alert Level)."""
        if rainfall_mm <= 0.0:
            return "No Rain", "#10B981", "NORMAL"
        elif rainfall_mm <= 2.4:
            return "Very Light Rain", "#10B981", "NORMAL"
        elif rainfall_mm <= 15.5:
            return "Light Rain", "#34D399", "NORMAL"
        elif rainfall_mm <= 64.4:
            return "Moderate Rain", "#FBBF24", "WATCH"
        elif rainfall_mm <= 115.5:
            return "Heavy Rain (IMD Yellow Alert)", "#F59E0B", "WARNING"
        elif rainfall_mm <= 204.4:
            return "Very Heavy Rain (IMD Orange Alert)", "#F97316", "ALERT"
        else:
            return "Extremely Heavy Rain (IMD Red Alert)", "#EF4444", "CRITICAL"


class RainfallAnalyzer:
    """Analytical engine for rainfall observations and forecast projections."""

    @staticmethod
    def calculate_antecedent_precipitation_index(
        daily_rainfall_series: List[float],
        decay_factor: float = 0.85
    ) -> float:
        """
        Calculates the Antecedent Precipitation Index (API):
        API_t = sum_{i=1}^N (P_i * k^i)
        where k is typically 0.80 - 0.90 for tropical urban catchments.
        Higher API indicates prior soil saturation and heightened runoff potential.
        """
        api = 0.0
        for day_idx, p in enumerate(daily_rainfall_series, start=1):
            api += p * (decay_factor ** day_idx)
        return round(api, 2)

    @staticmethod
    def compute_short_duration_intensity(
        rainfall_1h_mm: float,
        rainfall_3h_mm: float
    ) -> Dict[str, Any]:
        """
        Evaluates short-duration intensity risk.
        In urban India, rainfall > 30 mm/h causes rapid street flooding;
        > 60 mm/h triggers severe flash inundation regardless of daily totals.
        """
        hourly_rate = rainfall_1h_mm
        three_hour_rate = rainfall_3h_mm / 3.0 if rainfall_3h_mm > 0 else 0.0

        if hourly_rate >= 60.0:
            status = "TORRENTIAL_BURST"
            severity = "CRITICAL"
            advice = "Immediate flash waterlogging imminent in all low-lying junctions."
        elif hourly_rate >= 30.0:
            status = "INTENSE_DOWNPOUR"
            severity = "HIGH"
            advice = "Rapid runoff exceeding storm drain capacity (typical design: 20-25 mm/h)."
        elif hourly_rate >= 15.0:
            status = "STEADY_MODERATE"
            severity = "MODERATE"
            advice = "Localized puddles; monitors active at culverts."
        else:
            status = "LIGHT_PRECIPITATION"
            severity = "LOW"
            advice = "Normal drainage conditions."

        return {
            "hourly_rate_mm_per_hr": round(hourly_rate, 1),
            "three_hour_avg_rate_mm_per_hr": round(three_hour_rate, 1),
            "intensity_status": status,
            "severity": severity,
            "operational_advice": advice
        }

    @staticmethod
    def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine distance between two coordinates in kilometers."""
        r = 6371.0
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (
            math.sin(d_lat / 2.0) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return r * c

    @classmethod
    def inverse_distance_weighting(
        cls,
        target_lat: float,
        target_lon: float,
        observations: List[Dict[str, Any]],
        value_key: str = "rainfall_24h_mm",
        power: float = 2.0
    ) -> float:
        """
        Interpolates rainfall at an ungauged location using Inverse Distance Weighting (IDW).
        """
        if not observations:
            return 0.0

        weights_sum = 0.0
        weighted_values_sum = 0.0

        for obs in observations:
            dist = cls.haversine_distance_km(target_lat, target_lon, obs["lat"], obs["lon"])
            if dist < 0.1:  # extremely close, return point observation directly
                return obs.get(value_key, 0.0)
            weight = 1.0 / (dist ** power)
            weights_sum += weight
            weighted_values_sum += weight * obs.get(value_key, 0.0)

        if weights_sum == 0.0:
            return 0.0
        return round(weighted_values_sum / weights_sum, 2)
