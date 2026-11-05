from typing import Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def plot_temperature_anomalies(
    anomalies_df: pd.DataFrame,
    city_name: str,
) -> Tuple[plt.Figure, plt.Axes]:
    """Generate an anomaly bar chart with 5-year rolling trend curve.

    Bars above zero are colored warm red; bars below are cool blue.
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    years = anomalies_df["year"]
    anomalies = anomalies_df["anomaly"]

    # Red for positive anomalies, blue for negative
    colors = np.where(anomalies >= 0, "#d73027", "#4575b4")

    # Plot anomaly bars
    ax.bar(years, anomalies, color=colors, width=0.8, alpha=0.85, label="Annual Anomaly")

    # Overlay 5-year rolling average
    if "anomaly_rolling_5y" in anomalies_df.columns:
        ax.plot(
            years,
            anomalies_df["anomaly_rolling_5y"],
            color="#1a1a1a",
            linewidth=2.5,
            label="5-Year Rolling Average",
        )

    # Styling
    ax.axhline(0, color="black", linestyle="--", linewidth=1.0, alpha=0.7)
    ax.set_title(
        f"Temperature Anomalies (Reference: 1961–1990) — {city_name}",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("Anomaly (°C)", fontsize=11)
    ax.grid(axis="y", linestyle=":", alpha=0.6)
    ax.legend(frameon=True, loc="upper left")

    fig.tight_layout()
    return fig, ax


def plot_monthly_heatmap(
    matrix: pd.DataFrame,
    city_name: str,
) -> Tuple[plt.Figure, plt.Axes]:
    """Generate a monthly temperature heatmap across all recorded years."""
    fig, ax = plt.subplots(figsize=(12, 8))

    month_labels = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]

    sns.heatmap(
        matrix,
        cmap="coolwarm",
        cbar_kws={"label": "Mean Temperature (°C)"},
        xticklabels=month_labels,
        ax=ax,
    )

    ax.set_title(
        f"Monthly Temperature Climatology & Evolution — {city_name}",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )
    ax.set_xlabel("Month", fontsize=11)
    ax.set_ylabel("Year", fontsize=11)

    fig.tight_layout()
    return fig, ax


if __name__ == "__main__":
    from src.fetch import DEFAULT_CITIES, fetch_weather_data
    from src.data_processing import compute_temperature_anomalies, create_monthly_matrix

    print("Generating anomaly charts and heatmaps for ALL cities...")

    for city_name in DEFAULT_CITIES.keys():
        print(f"\nProcessing {city_name}...")
        df = fetch_weather_data(city_name)

        # 1. Anomaly Bar Chart
        anom_df = compute_temperature_anomalies(df)
        fig_anom, _ = plot_temperature_anomalies(anom_df, city_name)
        anom_path = f"data/{city_name.lower()}_anomalies.png"
        fig_anom.savefig(anom_path)
        print(f"-> Saved {anom_path}")

        # 2. Monthly Heatmap
        matrix_df = create_monthly_matrix(df)
        fig_heat, _ = plot_monthly_heatmap(matrix_df, city_name)
        heat_path = f"data/{city_name.lower()}_heatmap.png"
        fig_heat.savefig(heat_path)
        print(f"-> Saved {heat_path}")

    print("\nAll city figures have been successfully generated!")