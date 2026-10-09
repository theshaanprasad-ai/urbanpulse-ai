"""
Climate and Infrastructure Stress-Testing Module for MonsoonWatch India.
Enables urban planners to compare IPCC CMIP6 and INDRA downscaled climate scenarios
against current storm drainage capacity, while explicitly distinguishing long-term
climatological return periods from operational short-term weather forecasts.
"""

from typing import List, Dict, Any


class ClimateStressEngine:
    """Analytical engine for climate scenario comparison and infrastructure stress testing."""

    SCENARIOS = [
        {
            "id": "chennai-historical",
            "city_id": "chennai",
            "scenario_name": "Historical Baseline (1985-2014)",
            "time_horizon": "1985-2014 Reference",
            "projected_annual_rainfall_change_pct": 0.0,
            "extreme_rainfall_frequency_multiplier": 1.0,
            "vulnerable_ward_count": 4,
            "projected_runoff_increase_pct": 0.0,
            "data_source_citation": "IMD 0.25-Degree Daily Gridded Precipitation Climatology (1985-2014)"
        },
        {
            "id": "chennai-ssp245-2050",
            "city_id": "chennai",
            "scenario_name": "CMIP6 SSP2-4.5 (Middle of the Road)",
            "time_horizon": "2040-2060 (Mid-Century)",
            "projected_annual_rainfall_change_pct": 7.4,
            "extreme_rainfall_frequency_multiplier": 1.38,
            "vulnerable_ward_count": 7,
            "projected_runoff_increase_pct": 16.5,
            "data_source_citation": "INDRA-CMIP6 High-Resolution Downscaled Projections for Peninsular India"
        },
        {
            "id": "chennai-ssp585-2050",
            "city_id": "chennai",
            "scenario_name": "CMIP6 SSP5-8.5 (High Emissions)",
            "time_horizon": "2040-2060 (Mid-Century)",
            "projected_annual_rainfall_change_pct": 14.8,
            "extreme_rainfall_frequency_multiplier": 1.85,
            "vulnerable_ward_count": 11,
            "projected_runoff_increase_pct": 28.2,
            "data_source_citation": "NEX-GDDP-CMIP6 Ensemble Projections (IITM Pune / MoES)"
        },
        {
            "id": "chennai-ssp585-2080",
            "city_id": "chennai",
            "scenario_name": "CMIP6 SSP5-8.5 (Late-Century Extreme)",
            "time_horizon": "2070-2099 (Late-Century)",
            "projected_annual_rainfall_change_pct": 22.1,
            "extreme_rainfall_frequency_multiplier": 2.45,
            "vulnerable_ward_count": 14,
            "projected_runoff_increase_pct": 45.0,
            "data_source_citation": "IPCC AR6 Working Group I Atlas (South Asia Regional Assessment)"
        }
    ]

    @classmethod
    def get_scenarios(cls, city_id: str = "chennai") -> List[Dict[str, Any]]:
        return [s for s in cls.SCENARIOS if s["city_id"] == city_id] or cls.SCENARIOS

    @classmethod
    def compare_scenarios(cls, city_id: str = "chennai") -> Dict[str, Any]:
        scenarios = cls.get_scenarios(city_id)
        return {
            "city_id": city_id,
            "scenarios": scenarios,
            "climatological_guidance": (
                "Under SSP5-8.5 mid-century projections, the 1-in-25-year 24-hour extreme rainfall event "
                "(currently ~240mm) is projected to occur with a return period of approximately 1-in-11 years. "
                "Current storm sewer design standards (typically 25-30 mm/h) require retrofitting with decentralized "
                "sponge-city retention parks and tidal backwater surge gates."
            ),
            "disclaimer": (
                "IMPORTANT: Climate projections represent multi-decadal statistical distributions. "
                "They are intended for master planning and infrastructure asset sizing, NOT for short-term 24-hour flood alerts."
            )
        }
