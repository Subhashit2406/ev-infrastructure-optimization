"""
=================================================================
  Feature Engineering — Extract meaningful features from raw data.
  
  This module creates the features that feed into ML models.
  Each function is a pure transform: DataFrame in → DataFrame out.
=================================================================
"""

import pandas as pd
import numpy as np
from typing import Optional


# ──────────────────────────────────────────────────────
#  EV SALES FEATURES (Phase 1: Demand Forecasting)
# ──────────────────────────────────────────────────────

def add_time_features(df: pd.DataFrame, date_col: str = None) -> pd.DataFrame:
    """
    Add time-based features from a date column or year/month columns.
    
    Features created:
      - quarter, half_year
      - year_month (string for grouping)
      - is_q4 (festival season in India = Oct-Dec)
      - months_since_start (for trend modeling)
    """
    df = df.copy()
    
    # Case 1: We have a proper datetime column
    if date_col and date_col in df.columns:
        dt = pd.to_datetime(df[date_col], errors="coerce")
        df["year"] = dt.dt.year
        df["month"] = dt.dt.month
        df["quarter"] = dt.dt.quarter
    elif "year" in df.columns and "month" in df.columns:
        df["quarter"] = ((df["month"] - 1) // 3) + 1
    elif "year" in df.columns:
        df["quarter"] = 1  # default
        df["month"] = 1
    
    if "quarter" in df.columns:
        df["half_year"] = (df["quarter"] <= 2).astype(int) + 1  # H1 or H2
    
    if "month" in df.columns:
        df["is_festival_season"] = df["month"].isin([10, 11, 12]).astype(int)  # Diwali boost
    
    if "year" in df.columns and "month" in df.columns:
        df["year_month"] = df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2)
        
        # Months since first record (for trend)
        min_year = df["year"].min()
        min_month = df.loc[df["year"] == min_year, "month"].min() if "month" in df.columns else 1
        df["months_since_start"] = (df["year"] - min_year) * 12 + (df["month"] - min_month)
    
    print(f"  🔧 Time features added: {[c for c in df.columns if c in ['quarter', 'half_year', 'is_festival_season', 'year_month', 'months_since_start']]}")
    return df


def calculate_ev_penetration(
    df: pd.DataFrame,
    sales_col: str = "ev_sales_count",
    group_col: str = "state",
) -> pd.DataFrame:
    """
    Calculate EV Penetration Rate per group (state/city/RTO).
    
    Penetration = state's EV sales / total EV sales (national) × 100
    Growth = year-over-year growth rate per state.
    """
    df = df.copy()
    
    if sales_col not in df.columns:
        print(f"  ⚠️  Column '{sales_col}' not found, skipping penetration calc")
        return df
    
    # National share
    if group_col in df.columns and "year" in df.columns:
        yearly_total = df.groupby("year")[sales_col].transform("sum")
        df["national_share_pct"] = (df[sales_col] / yearly_total.replace(0, np.nan) * 100).round(2)
        
        # Year-over-year growth per state
        df = df.sort_values([group_col, "year"])
        df["yoy_growth_pct"] = df.groupby(group_col)[sales_col].pct_change() * 100
        df["yoy_growth_pct"] = df["yoy_growth_pct"].round(2)
        
        print(f"  🔧 Penetration features: national_share_pct, yoy_growth_pct")
    
    return df


def add_lag_features(
    df: pd.DataFrame,
    value_col: str = "ev_sales_count",
    group_col: str = "state",
    lags: list = [1, 2, 3, 6, 12],
) -> pd.DataFrame:
    """
    Add lagged values for time-series forecasting.
    
    Lag-1 = last month's sales (strong predictor).
    Lag-12 = same month last year (seasonality).
    """
    df = df.copy()
    
    if value_col not in df.columns:
        print(f"  ⚠️  Column '{value_col}' not found, skipping lag features")
        return df
    
    df = df.sort_values([group_col, "year"] + (["month"] if "month" in df.columns else []))
    
    for lag in lags:
        col_name = f"{value_col}_lag_{lag}"
        df[col_name] = df.groupby(group_col)[value_col].shift(lag)
    
    # Rolling averages
    df[f"{value_col}_rolling_3"] = df.groupby(group_col)[value_col].transform(
        lambda x: x.rolling(3, min_periods=1).mean()
    )
    df[f"{value_col}_rolling_6"] = df.groupby(group_col)[value_col].transform(
        lambda x: x.rolling(6, min_periods=1).mean()
    )
    
    print(f"  🔧 Lag features added: {len(lags)} lags + 2 rolling averages")
    return df


# ──────────────────────────────────────────────────────
#  STATION FEATURES (Phase 2: Geospatial)
# ──────────────────────────────────────────────────────

def add_station_density(df: pd.DataFrame, radius_km: float = 5.0) -> pd.DataFrame:
    """
    Calculate how many other stations are within `radius_km` of each station.
    
    Uses the Haversine formula for accurate distance on Earth's surface.
    """
    df = df.copy()
    
    if "latitude" not in df.columns or "longitude" not in df.columns:
        print("  ⚠️  Lat/Long not found, skipping density calculation")
        return df
    
    lat = np.radians(df["latitude"].values)
    lon = np.radians(df["longitude"].values)
    
    density = []
    for i in range(len(df)):
        dlat = lat - lat[i]
        dlon = lon - lon[i]
        a = np.sin(dlat / 2) ** 2 + np.cos(lat[i]) * np.cos(lat) * np.sin(dlon / 2) ** 2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        distances = 6371 * c  # Earth radius in km
        nearby = (distances <= radius_km).sum() - 1  # exclude self
        density.append(nearby)
    
    df["station_density_5km"] = density
    print(f"  🔧 Station density: avg {np.mean(density):.1f} neighbors within {radius_km}km")
    return df


# ──────────────────────────────────────────────────────
#  USAGE FEATURES (Phase 3: Grid / Load)
# ──────────────────────────────────────────────────────

def add_usage_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived features from charging session data."""
    df = df.copy()
    
    # Charging speed (if energy and duration available)
    if "energy_kwh" in df.columns and "duration_hours" in df.columns:
        df["charging_speed_kw"] = df["energy_kwh"] / df["duration_hours"].replace(0, np.nan)
    
    # Peak hour flag (6-9 PM = peak grid load in India)
    if "hour_of_day" in df.columns:
        df["is_peak_hour"] = df["hour_of_day"].between(18, 21).astype(int)
        df["is_off_peak"] = df["hour_of_day"].between(0, 6).astype(int)
    
    # Time slot bins
    if "hour_of_day" in df.columns:
        df["time_slot"] = pd.cut(
            df["hour_of_day"],
            bins=[0, 6, 12, 18, 24],
            labels=["Night", "Morning", "Afternoon", "Evening"],
            include_lowest=True,
        )
    
    print(f"  🔧 Usage features added")
    return df


# ──────────────────────────────────────────────────────
#  MASTER FUNCTION — Apply all features
# ──────────────────────────────────────────────────────

def engineer_all_features(datasets: dict) -> dict:
    """
    Apply feature engineering to all available datasets.
    
    Args:
        datasets: dict from processing pipeline {"ev_sales": df, "stations": df, "usage": df}
    
    Returns:
        Same dict with feature-engineered DataFrames.
    """
    print("\n" + "=" * 60)
    print("  FEATURE ENGINEERING")
    print("=" * 60)
    
    result = {}
    
    if "ev_sales" in datasets:
        df = datasets["ev_sales"]
        df = add_time_features(df)
        df = calculate_ev_penetration(df)
        df = add_lag_features(df)
        result["ev_sales"] = df
    
    if "stations" in datasets:
        df = datasets["stations"]
        df = add_station_density(df)
        result["stations"] = df
    
    if "usage" in datasets:
        df = datasets["usage"]
        df = add_usage_features(df)
        result["usage"] = df
    
    print("\n  ✅ Feature engineering complete!")
    for name, df in result.items():
        print(f"     {name}: {len(df.columns)} features")
    
    return result
