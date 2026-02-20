"""
=================================================================
  Data Processing — Clean, validate, and prepare data for modeling.
  
  This is the MAIN PIPELINE that transforms raw → processed data.
  
  Usage:
    python -m src.data.processing
=================================================================
"""

import os
import sys
import pandas as pd
import numpy as np
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.data.ingestion import load_all, PROCESSED_DIR, RAW_DIR
from src.data.schema import (
    validate_ev_sales,
    validate_stations,
    validate_usage,
    generate_data_report,
)


def process_ev_sales(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full cleaning pipeline for EV sales/registration data.
    
    Steps:
      1. Schema validation (remove garbage rows)
      2. Standardize column names
      3. Fill missing values intelligently
      4. Add derived columns
    """
    print("\n" + "─" * 50)
    print("  PROCESSING: EV Sales / Registrations")
    print("─" * 50)
    
    # Step 1: Validate
    df = validate_ev_sales(df)
    
    # Step 2: Standardize — detect and rename key columns
    col_map = {}
    for col in df.columns:
        col_lower = col.lower()
        if "state" in col_lower or "region" in col_lower:
            col_map[col] = "state"
        elif "categ" in col_lower or "vehicle" in col_lower or "type" in col_lower:
            col_map[col] = "vehicle_category"
        elif "year" in col_lower and "month" not in col_lower:
            col_map[col] = "year"
        elif "month" in col_lower:
            col_map[col] = "month"
        elif "count" in col_lower or "quantity" in col_lower or "number" in col_lower or "sale" in col_lower:
            col_map[col] = "ev_sales_count"
    
    if col_map:
        df = df.rename(columns=col_map)
        print(f"  📝 Renamed columns: {col_map}")
    
    # Step 3: Ensure numeric sales count
    if "ev_sales_count" in df.columns:
        df["ev_sales_count"] = pd.to_numeric(df["ev_sales_count"], errors="coerce").fillna(0).astype(int)
    
    # Step 4: Ensure year column exists
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce")
        df = df.dropna(subset=["year"])
        df["year"] = df["year"].astype(int)
    
    print(f"  ✅ Processed: {len(df)} rows, columns: {list(df.columns)}")
    return df


def process_stations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full cleaning pipeline for charging station data.
    
    Steps:
      1. Schema validation (India bounding box)
      2. Standardize column names
      3. Clean text columns for NLP
      4. Add geospatial features
    """
    print("\n" + "─" * 50)
    print("  PROCESSING: Charging Stations")
    print("─" * 50)
    
    # Step 1: Validate
    df = validate_stations(df)
    
    # Step 2: Standardize columns
    col_map = {}
    for col in df.columns:
        col_lower = col.lower()
        if "lat" in col_lower and "latitude" not in df.columns:
            col_map[col] = "latitude"
        elif ("lon" in col_lower or "lng" in col_lower) and "longitude" not in df.columns:
            col_map[col] = "longitude"
        elif "city" in col_lower or "town" in col_lower:
            col_map[col] = "city"
        elif "state" in col_lower or "province" in col_lower:
            col_map[col] = "state"
        elif "operator" in col_lower or "network" in col_lower or "provider" in col_lower:
            col_map[col] = "operator"
        elif "connector" in col_lower or "plug" in col_lower:
            col_map[col] = "connector_type"
        elif "power" in col_lower or "kw" in col_lower:
            col_map[col] = "power_kw"
    
    if col_map:
        df = df.rename(columns=col_map)
        print(f"  📝 Renamed columns: {col_map}")
    
    # Step 3: Clean text columns (NLP prep)
    text_cols = df.select_dtypes(include=["object"]).columns
    for col in text_cols:
        df[col] = df[col].str.strip()
        df[col] = df[col].replace(["", "N/A", "n/a", "NA", "null", "None"], np.nan)
    
    # Step 4: Add geospatial region tags
    if "latitude" in df.columns:
        df["region"] = pd.cut(
            df["latitude"],
            bins=[6, 15, 23, 30, 37],
            labels=["South", "Central", "North", "Far North"],
        )
    
    print(f"  ✅ Processed: {len(df)} rows, columns: {list(df.columns)}")
    return df


def process_usage(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full cleaning pipeline for charging session/usage data.
    
    Steps:
      1. Schema validation
      2. Parse timestamps
      3. Calculate derived features (duration, cost/kWh)
      4. Add time-based features
    """
    print("\n" + "─" * 50)
    print("  PROCESSING: Charging Usage / Sessions")
    print("─" * 50)
    
    # Step 1: Validate
    df = validate_usage(df)
    
    # Step 2: Standardize columns
    col_map = {}
    for col in df.columns:
        col_lower = col.lower()
        if "duration" in col_lower:
            col_map[col] = "duration_hours"
        elif "energy" in col_lower or "kwh" in col_lower:
            col_map[col] = "energy_kwh"
        elif "cost" in col_lower or "charge" in col_lower and "charg" not in col_lower:
            col_map[col] = "cost_inr"
        elif "start" in col_lower and "time" in col_lower:
            col_map[col] = "start_time"
        elif "end" in col_lower and "time" in col_lower:
            col_map[col] = "end_time"
        elif "vehicle" in col_lower and "type" in col_lower:
            col_map[col] = "vehicle_type"
    
    if col_map:
        df = df.rename(columns=col_map)
        print(f"  📝 Renamed columns: {col_map}")
    
    # Step 3: Parse time columns
    for col in ["start_time", "end_time"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    
    # Step 4: Derived features
    if "start_time" in df.columns and "end_time" in df.columns:
        df["duration_calc_hours"] = (df["end_time"] - df["start_time"]).dt.total_seconds() / 3600
    
    if "energy_kwh" in df.columns and "cost_inr" in df.columns:
        df["cost_per_kwh"] = df["cost_inr"] / df["energy_kwh"].replace(0, np.nan)
    
    # Step 5: Time features for later analysis
    time_col = "start_time" if "start_time" in df.columns else None
    if time_col and pd.api.types.is_datetime64_any_dtype(df[time_col]):
        df["hour_of_day"] = df[time_col].dt.hour
        df["day_of_week"] = df[time_col].dt.dayofweek
        df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
        df["month"] = df[time_col].dt.month
    
    print(f"  ✅ Processed: {len(df)} rows, columns: {list(df.columns)}")
    return df


def run_pipeline():
    """Run the full data processing pipeline."""
    print("=" * 60)
    print("  EV INFRASTRUCTURE — DATA PROCESSING PIPELINE")
    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    # Load all raw data
    raw_data = load_all()
    
    if not raw_data:
        print("\n❌ No data found! Please run download_datasets.py first.")
        return
    
    processed = {}
    reports = []
    
    # Process each dataset
    processors = {
        "ev_sales": process_ev_sales,
        "stations": process_stations,
        "usage": process_usage,
    }
    
    for name, processor in processors.items():
        if name in raw_data:
            try:
                processed[name] = processor(raw_data[name])
                
                # Save processed data
                out_path = os.path.join(PROCESSED_DIR, f"{name}_processed.csv")
                processed[name].to_csv(out_path, index=False)
                print(f"  💾 Saved: {out_path}")
                
                # Generate quality report
                report = generate_data_report(processed[name], name)
                reports.append(report)
                
            except Exception as e:
                print(f"  ❌ Error processing {name}: {e}")
    
    # Save quality reports
    if reports:
        report_path = os.path.join(PROCESSED_DIR, "data_quality_report.json")
        with open(report_path, "w") as f:
            json.dump(reports, f, indent=2, default=str)
        print(f"\n  📋 Quality report saved: {report_path}")
    
    # Summary
    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)
    for name, df in processed.items():
        print(f"  • {name}: {len(df)} rows × {len(df.columns)} cols")
    print()
    
    return processed


if __name__ == "__main__":
    run_pipeline()
