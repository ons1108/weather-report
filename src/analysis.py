"""
Statistical analysis module for climate trends and extreme events.
Computes linear regressions, tropical nights, heatwave frequency, and heavy rainfall.
"""
from typing import Dict, Any
import numpy as np
import pandas as pd
from scipy import stats

from src.config import (
    BASELINE_START_YEAR,
    BASELINE_END_YEAR,
    TROPICAL_NIGHT_THRESHOLD_C,
    HEATWAVE_PERCENTILE,
    HEAVY_RAIN_THRESHOLD_MM,
)
from src.data_processing import prepare_daily_data, resample_annual


def calculate_warming_trend(annual_df: pd.DataFrame) -> Dict[str, Any]:
    """Compute linear regression trend over annual mean temperatures.

    Parameters
    ----------
    annual_df : pd.DataFrame
        Annual resampled dataframe containing 'year' and 'temperature_2m_mean'.

    Returns
    -------
    Dict[str, Any]
        Dictionary with slope (°C/year), warming_rate_per_decade (°C/decade),
        p_value, r_squared, and regression line values.
    """
    clean_series = annual_df.dropna(subset=["temperature_2m_mean"])
    x = clean_series["year"].values
    y = clean_series["temperature_2m_mean"].values

    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    return {
        "slope_per_year": slope,
        "warming_rate_per_decade": slope * 10,
        "intercept": intercept,
        "r_squared": r_value ** 2,
        "p_value": p_value,
        "std_err": std_err,
        "trend_line": intercept + slope * x,
        "years": x,
    }


def compute_tropical_nights(daily_df: pd.DataFrame, threshold: float = TROPICAL_NIGHT_THRESHOLD_C) -> pd.Series:
    """Calculate the annual count of tropical nights (Tmin >= threshold).

    Parameters
    ----------
    daily_df : pd.DataFrame
        Daily observations containing 'temperature_2m_min'.
    threshold : float, default 20.0 °C
        Minimum temperature threshold.

    Returns
    -------
    pd.Series
        Number of tropical nights per year indexed by year.
    """
    df = prepare_daily_data(daily_df)
    is_tropical = df["temperature_2m_min"] >= threshold
    return is_tropical.groupby(df["year"]).sum()


def compute_summer_heatwaves(
    daily_df: pd.DataFrame,
    start_year: int = BASELINE_START_YEAR,
    end_year: int = BASELINE_END_YEAR,
    percentile: float = HEATWAVE_PERCENTILE,
) -> pd.Series:
    """Calculate annual days exceeding the baseline summer 90th percentile of Tmax.

    Summer months: June, July, August (months 6, 7, 8).

    Parameters
    ----------
    daily_df : pd.DataFrame
        Daily observations.
    start_year : int, default 1961
        Baseline start year.
    end_year : int, default 1990
        Baseline end year.
    percentile : float, default 90.0
        Threshold percentile for extreme temperature.

    Returns
    -------
    pd.Series
        Number of extreme heat days per year.
    """
    df = prepare_daily_data(daily_df)

    # Filter baseline summer days (June, July, August)
    baseline_summer = df[
        (df["year"] >= start_year)
        & (df["year"] <= end_year)
        & (df["month"].isin([6, 7, 8]))
    ]

    threshold_val = np.percentile(baseline_summer["temperature_2m_max"].dropna(), percentile)

    # Detect days exceeding this threshold across all recorded years
    is_extreme = df["temperature_2m_max"] >= threshold_val
    return is_extreme.groupby(df["year"]).sum()


def compute_heavy_rain_days(
    daily_df: pd.DataFrame,
    threshold: float = HEAVY_RAIN_THRESHOLD_MM,
) -> pd.Series:
    """Calculate annual count of heavy precipitation days (rain >= threshold mm)."""
    df = prepare_daily_data(daily_df)
    is_heavy_rain = df["precipitation_sum"] >= threshold
    return is_heavy_rain.groupby(df["year"]).sum()


def summarize_city_climate_metrics(daily_df: pd.DataFrame, city_name: str) -> Dict[str, Any]:
    """Generate a comprehensive statistical summary for a single city."""
    annual_df = resample_annual(daily_df)
    trend = calculate_warming_trend(annual_df)
    tropical_nights = compute_tropical_nights(daily_df)
    heatwaves = compute_summer_heatwaves(daily_df)
    heavy_rain = compute_heavy_rain_days(daily_df)

    return {
        "city": city_name,
        "warming_rate_per_decade": trend["warming_rate_per_decade"],
        "p_value": trend["p_value"],
        "r_squared": trend["r_squared"],
        "avg_tropical_nights_early": tropical_nights.loc[1961:1990].mean(),
        "avg_tropical_nights_recent": tropical_nights.loc[2015:2025].mean(),
        "avg_heatwave_days_early": heatwaves.loc[1961:1990].mean(),
        "avg_heatwave_days_recent": heatwaves.loc[2015:2025].mean(),
    }


if __name__ == "__main__":
    from src.fetch import DEFAULT_CITIES, fetch_weather_data

    print("=" * 70)
    print("CLIMATE TRENDS & EXTREME EVENT ANALYSIS (1960 - 2025)")
    print("=" * 70)

    summary_list = []
    for city in DEFAULT_CITIES.keys():
        df = fetch_weather_data(city)
        metrics = summarize_city_climate_metrics(df, city)
        summary_list.append(metrics)

    summary_df = pd.DataFrame(summary_list)
    
    # 1. Affichage fel terminal
    print(summary_df.to_string(index=False))

    # 2. Enregistrement fel dossier data
    output_path = "data/climate_summary_metrics.csv"
    summary_df.to_csv(output_path, index=False)
    print(f"\n[OK] Tableau sauvegardé avec succès dans: {output_path}")