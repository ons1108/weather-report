
"""
Configuration module for the Weather Report climate analysis project.
Defines endpoints, paths, default cities, baseline windows, and weather thresholds.
"""
from pathlib import Path

# Paths configuration
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# API Endpoints
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"

# Default Target Cities (can be dynamically extended via geocoding)
DEFAULT_CITIES = {
    "Milan": {"lat": 45.4642, "lon": 9.1900, "country": "Italy"},
    "London": {"lat": 51.5074, "lon": -0.1278, "country": "United Kingdom"},
    "Tokyo": {"lat": 35.6762, "lon": 139.6503, "country": "Japan"},
    "Cairo": {"lat": 30.0444, "lon": 31.2357, "country": "Egypt"},
    "Paris": {"lat": 48.8566, "lon": 2.3522, "country": "France"},
}

# Study time boundaries
START_DATE = "1960-01-01"
END_DATE = "2025-12-31"

# Standard WMO 30-year climatological baseline
BASELINE_START_YEAR = 1961
BASELINE_END_YEAR = 1990

# Daily meteorological variables to query
DAILY_VARIABLES = [
    "temperature_2m_mean",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
]

# Physical thresholds for extreme events
TROPICAL_NIGHT_THRESHOLD_C = 20.0  # Daily Tmin >= 20°C
HEATWAVE_PERCENTILE = 90.0         # Tmax above 90th percentile of baseline summer
HEAVY_RAIN_THRESHOLD_MM = 10.0     # Daily precipitation >= 10 mm