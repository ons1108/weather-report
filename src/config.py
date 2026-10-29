"""
Configuration module for the Weather Report project.
Defines constants, paths, target cities, and baseline periods.
"""
from pathlib import Path

# Paths setup using pathlib (cross-platform compatible)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Target cities for climate comparison
# Coordinates: latitude, longitude
CITIES = {
    "Milan": {"lat": 45.4642, "lon": 9.1900},
    "London": {"lat": 51.5074, "lon": -0.1278},
    "Tokyo": {"lat": 35.6762, "lon": 139.6503},
    "Cairo": {"lat": 30.0444, "lon": 31.2357},
}

# API endpoint
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Climatological baseline window (World Meteorological Organization standard: 1961-1990)
BASELINE_START = "1961-01-01"
BASELINE_END = "1990-12-31"

# Study period
START_DATE = "1960-01-01"
END_DATE = "2025-12-31"

# Daily variables to fetch from Open-Meteo
DAILY_VARS = [
    "temperature_2m_mean",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
]