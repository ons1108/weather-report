from typing import Tuple
import pandas as pd
import numpy as np

from src.config import BASELINE_START_YEAR, BASELINE_END_YEAR


def prepare_daily_data(df: pd.DataFrame) -> pd.DataFrame:
    """ Cleaned dataframe with DatetimeIndex and extracted year/month columns."""
    clean_df = df.copy()
    if not isinstance(clean_df.index, pd.DatetimeIndex):
        clean_df["date"] = pd.to_datetime(clean_df["date"])
        clean_df = clean_df.set_index("date")

    # Add temporal helper columns
    clean_df["year"] = clean_df.index.year
    clean_df["month"] = clean_df.index.month
    clean_df["day_of_year"] = clean_df.index.dayofyear
    return clean_df


def resample_annual(df: pd.DataFrame) -> pd.DataFrame:
    """Annual dataframe with mean/min/max temperatures and total precipitation."""
    clean_df = prepare_daily_data(df)

    annual = clean_df.resample("YE").agg({
        "temperature_2m_mean": "mean",
        "temperature_2m_max": "max",
        "temperature_2m_min": "min",
        "precipitation_sum": "sum",
        "city": "first",
    })

    annual["year"] = annual.index.year
    return annual


def resample_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly aggregated dataframe. """
    clean_df = prepare_daily_data(df)

    monthly = clean_df.resample("ME").agg({
        "temperature_2m_mean": "mean",
        "temperature_2m_max": "max",
        "temperature_2m_min": "min",
        "precipitation_sum": "sum",
        "city": "first",
    })
    monthly["year"] = monthly.index.year
    monthly["month"] = monthly.index.month
    return monthly


def calculate_baseline(
    df: pd.DataFrame,
    start_year: int = BASELINE_START_YEAR,
    end_year: int = BASELINE_END_YEAR,
) -> float:
    """Calculate reference mean temperature for the baseline period (1961-1990)."""
    clean_df = prepare_daily_data(df)
    baseline_mask = (clean_df["year"] >= start_year) & (clean_df["year"] <= end_year)
    baseline_subset = clean_df.loc[baseline_mask]

    if baseline_subset.empty:
        raise ValueError(f"No records found for baseline period {start_year}-{end_year}")

    return float(baseline_subset["temperature_2m_mean"].mean())


def compute_temperature_anomalies(
    df: pd.DataFrame,
    start_year: int = BASELINE_START_YEAR,
    end_year: int = BASELINE_END_YEAR,
) -> pd.DataFrame:
    """Compute annual temperature anomalies relative to the baseline climatology.
    Formula:
        Anomaly_y = MeanTemp_y - BaselineMean
    """
    annual_df = resample_annual(df)
    baseline_mean = calculate_baseline(df, start_year, end_year)

    annual_df["baseline_reference"] = baseline_mean
    annual_df["anomaly"] = annual_df["temperature_2m_mean"] - baseline_mean
    annual_df["anomaly_rolling_5y"] = annual_df["anomaly"].rolling(window=5, center=True).mean()

    return annual_df


def create_monthly_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Create a 2D matrix (Year x Month) of average temperatures for heatmaps."""
    monthly_df = resample_monthly(df)
    matrix = monthly_df.pivot(index="year", columns="month", values="temperature_2m_mean")
    return matrix


if __name__ == "__main__":
    from src.fetch import fetch_weather_data

    print("Testing src/processing.py on Milan data...")
    milan_raw = fetch_weather_data("Milan")

    # Compute baseline
    base = calculate_baseline(milan_raw)
    print(f"Milan Baseline (1961-1990): {base:.2f} °C")

    # Compute anomalies
    anomalies = compute_temperature_anomalies(milan_raw)
    print("\nRecent 5 years of anomalies:")
    print(anomalies[["year", "temperature_2m_mean", "anomaly", "anomaly_rolling_5y"]].tail())

    # Create monthly pivot matrix
    matrix = create_monthly_matrix(milan_raw)
    print(f"\nMonthly matrix shape (Years x Months): {matrix.shape}")