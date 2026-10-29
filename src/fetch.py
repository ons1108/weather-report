"""
Data ingestion module for Open-Meteo historical records and geocoding.
Handles network requests, rate limiting (429), local CSV caching, and validation.
"""
import re
import time
from pathlib import Path
from typing import Any
import pandas as pd
import requests

from src.config import (
    DATA_DIR,
    DAILY_VARIABLES,
    DEFAULT_CITIES,
    END_DATE,
    OPEN_METEO_ARCHIVE_URL,
    OPEN_METEO_GEOCODING_URL,
    START_DATE,
)


def _sanitize_city_name(city_name: str) -> str:
    """Convert a city name into a safe filename string."""
    clean = re.sub(r"[^\w\s-]", "", city_name).strip().lower()
    return re.sub(r"[-\s]+", "_", clean)


def geocode_city(city_name: str, timeout: int = 10) -> dict[str, Any]:
    """Retrieve coordinates (latitude, longitude) for a city name."""
    params = {"name": city_name, "count": 1, "language": "en", "format": "json"}
    try:
        response = requests.get(OPEN_METEO_GEOCODING_URL, params=params, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        raise requests.RequestException(
            f"Geocoding network error for '{city_name}': {err}"
        ) from err

    payload = response.json()
    results = payload.get("results")
    if not results:
        raise ValueError(f"Could not resolve location for city: '{city_name}'")

    top_hit = results[0]
    return {
        "name": top_hit.get("name", city_name),
        "lat": top_hit["latitude"],
        "lon": top_hit["longitude"],
        "country": top_hit.get("country", "Unknown"),
    }


def fetch_weather_data(
    city_name: str,
    lat: float | None = None,
    lon: float | None = None,
    start_date: str = START_DATE,
    end_date: str = END_DATE,
    force_reload: bool = False,
    timeout: int = 45,
    max_retries: int = 3,
) -> pd.DataFrame:
    """Fetch daily historical weather observations for a given location.

    Includes automatic retries with waiting if the API rate limit (429) is hit.
    """
    safe_name = _sanitize_city_name(city_name)
    cache_file = DATA_DIR / f"{safe_name}.csv"

    # 1. Return from disk if cached
    if cache_file.exists() and not force_reload:
        print(f"[CACHE] Loading {city_name} from {cache_file.name}")
        return pd.read_csv(cache_file, parse_dates=["date"])

    # 2. Resolve coordinates if missing
    if lat is None or lon is None:
        if city_name in DEFAULT_CITIES:
            lat = DEFAULT_CITIES[city_name]["lat"]
            lon = DEFAULT_CITIES[city_name]["lon"]
        else:
            print(f"[GEOCODE] Resolving coordinates for '{city_name}'...")
            geo_info = geocode_city(city_name)
            lat, lon = geo_info["lat"], geo_info["lon"]

    # 3. Query the Open-Meteo Archive API with retry mechanism
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ",".join(DAILY_VARIABLES),
        "timezone": "UTC",
    }

    print(f"[API] Downloading {city_name} ({start_date} to {end_date})...")

    response = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(OPEN_METEO_ARCHIVE_URL, params=params, timeout=timeout)
            
            # If hit by rate-limit (429), pause and retry
            if response.status_code == 429:
                wait_time = 60
                print(f"[RATE LIMIT] Hit 429 for {city_name}. Waiting {wait_time}s (attempt {attempt}/{max_retries})...")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            break  # Success
        except requests.exceptions.Timeout:
            if attempt == max_retries:
                raise requests.RequestException(
                    f"API request timed out for city '{city_name}' after {max_retries} attempts."
                )
            time.sleep(5)
        except requests.exceptions.RequestException as req_err:
            if response is not None and response.status_code != 429:
                raise requests.RequestException(
                    f"API error for '{city_name}': {req_err}"
                ) from req_err

    if response is None or response.status_code != 200:
        raise requests.HTTPError(f"Failed to fetch data for {city_name} after {max_retries} retries.")

    payload = response.json()
    if "daily" not in payload:
        raise KeyError(f"'daily' key missing from API response for '{city_name}'")

    # 4. Normalize and clean DataFrame (without deprecated inplace)
    df = pd.DataFrame(payload["daily"])
    if "time" in df.columns:
        df = df.rename(columns={"time": "date"})

    df["date"] = pd.to_datetime(df["date"])
    df["city"] = city_name
    df["latitude"] = lat
    df["longitude"] = lon

    # 5. Persist to cache
    df.to_csv(cache_file, index=False)
    print(f"[SAVED] Stored {len(df)} records in {cache_file.name}")

    return df


def fetch_default_cities(force_reload: bool = False, delay_between: float = 2.0) -> dict[str, pd.DataFrame]:
    """Fetch and cache datasets for all default cities with polite delays."""
    datasets: dict[str, pd.DataFrame] = {}
    for city, metadata in DEFAULT_CITIES.items():
        datasets[city] = fetch_weather_data(
            city_name=city,
            lat=metadata["lat"],
            lon=metadata["lon"],
            force_reload=force_reload,
        )
        # Small delay between downloads to stay well within free API limits
        if delay_between > 0:
            time.sleep(delay_between)
            
    return datasets


if __name__ == "__main__":
    print("=" * 60)
    print("Fetching and inspecting all default cities...")
    print("=" * 60)

    all_data = fetch_default_cities()

    for city_name, df in all_data.items():
        print(f"\n--- {city_name.upper()} ---")
        print(f"Total rows (days): {len(df):,}")
        print(f"Date range:        {df['date'].min().date()} to {df['date'].max().date()}")
        print(f"Average temp (°C): {df['temperature_2m_mean'].mean():.2f}")
        print(f"Max temp recorded: {df['temperature_2m_max'].max():.1f} °C")
        print(f"Min temp recorded: {df['temperature_2m_min'].min():.1f} °C")
        print(f"Total rain (mm):   {df['precipitation_sum'].sum():,.1f} mm")
        print("-" * 60)