"""
=================================================================
  Data Schema — Strict validation for all incoming data.
  
  This ensures we NEVER train models on garbage data.
  Every row must pass these checks before entering the pipeline.
=================================================================
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional, List, Dict


# ──────────────────────────────────────────────────────
#  CONSTANTS — Indian EV Context
# ──────────────────────────────────────────────────────

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar",
    "Chhattisgarh", "Goa", "Gujarat", "Haryana", "Himachal Pradesh",
    "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra",
    "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Delhi", "Chandigarh", "Puducherry", "Ladakh",
    "Jammu and Kashmir", "Andaman and Nicobar Islands",
    "Dadra and Nagar Haveli and Daman and Diu", "Lakshadweep",
]

EV_CATEGORIES = ["2W", "3W", "4W", "Bus", "Other"]

CONNECTOR_TYPES = [
    "Type 1", "Type 2", "CCS", "CCS2", "CHAdeMO",
    "Bharat AC-001", "Bharat DC-001", "GB/T", "Tesla",
]

# India bounding box (lat/long)
INDIA_LAT_RANGE = (6.0, 37.0)
INDIA_LON_RANGE = (68.0, 98.0)


# ──────────────────────────────────────────────────────
#  VALIDATORS — Functions to check data quality
# ──────────────────────────────────────────────────────

def validate_ev_sales(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate EV sales/registration data.
    
    Expected columns (flexible):
      - date/year/month: temporal identifier
      - state: Indian state name
      - vehicle_category: 2W, 3W, 4W, Bus
      - quantity/count: number of registrations
    
    Returns:
        Cleaned DataFrame with invalid rows removed.
    """
    original_len = len(df)
    
    # Standardize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    
    # Drop fully empty rows
    df = df.dropna(how="all")
    
    # If there's a 'date' column, parse it
    for col in ["date", "registration_date", "month_year"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            df = df.dropna(subset=[col])
            break
    
    # Numeric columns should be non-negative
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        df = df[df[col] >= 0]
    
    removed = original_len - len(df)
    if removed > 0:
        print(f"  ⚠️  Removed {removed} invalid rows from EV sales data")
    
    print(f"  ✅ EV Sales: {len(df)} valid rows | {len(df.columns)} columns")
    return df.reset_index(drop=True)


def validate_stations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate EV charging station location data.
    
    Expected columns (flexible):
      - latitude, longitude
      - city/state
      - operator/network name
      - connector type / power
    """
    original_len = len(df)
    
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df = df.dropna(how="all")
    
    # Find lat/long columns
    lat_col = next((c for c in df.columns if "lat" in c), None)
    lon_col = next((c for c in df.columns if "lon" in c or "lng" in c), None)
    
    if lat_col and lon_col:
        df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
        df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")
        
        # Filter to India bounding box
        mask = (
            df[lat_col].between(*INDIA_LAT_RANGE) &
            df[lon_col].between(*INDIA_LON_RANGE)
        )
        df = df[mask]
    
    removed = original_len - len(df)
    if removed > 0:
        print(f"  ⚠️  Removed {removed} invalid rows from station data")
    
    print(f"  ✅ Stations: {len(df)} valid rows | {len(df.columns)} columns")
    return df.reset_index(drop=True)


def validate_usage(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate EV charging session/usage data.
    
    Expected columns (flexible):
      - session duration / start time / end time
      - energy consumed (kWh)
      - cost
      - user/vehicle type
    """
    original_len = len(df)
    
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df = df.dropna(how="all")
    
    # Parse time columns
    for col in df.columns:
        if "time" in col or "date" in col or "start" in col or "end" in col:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    
    # Energy should be positive
    for col in df.columns:
        if "energy" in col or "kwh" in col:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df = df[df[col] > 0]
    
    removed = original_len - len(df)
    if removed > 0:
        print(f"  ⚠️  Removed {removed} invalid rows from usage data")
    
    print(f"  ✅ Usage: {len(df)} valid rows | {len(df.columns)} columns")
    return df.reset_index(drop=True)


def generate_data_report(df: pd.DataFrame, name: str) -> Dict:
    """Generate a quality report for any dataset."""
    report = {
        "name": name,
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "missing_pct": (df.isnull().sum() / len(df) * 100).to_dict(),
        "dtypes": df.dtypes.astype(str).to_dict(),
    }
    
    # Numeric summary
    numeric = df.select_dtypes(include=[np.number])
    if not numeric.empty:
        report["numeric_summary"] = numeric.describe().to_dict()
    
    return report
