"""
=================================================================
  Data Ingestion — Loads raw data from disk.
  
  This is the SINGLE ENTRY POINT for all data loading.
  Every script/notebook should use these functions.
=================================================================
"""

import os
import glob
import pandas as pd
import json
from typing import Optional, Dict, Tuple


# ──────────────────────────────────────────────────────
#  PATH CONFIGURATION
# ──────────────────────────────────────────────────────

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")


def _find_csv(directory: str, keywords: list) -> Optional[list]:
    """Find ALL CSV files matching any of the keywords."""
    if not os.path.exists(directory):
        return None
    
    matches = []
    for f in os.listdir(directory):
        f_lower = f.lower()
        if f_lower.endswith(".csv"):
            for kw in keywords:
                if kw in f_lower:
                    matches.append(os.path.join(directory, f))
                    break
    return matches if matches else None


# ──────────────────────────────────────────────────────
#  LOADERS — One function per dataset type
# ──────────────────────────────────────────────────────

def load_ev_sales(path: Optional[str] = None) -> pd.DataFrame:
    """
    Load EV sales/registration data.
    
    Auto-detects the file in data/raw/ if no path is given.
    Looks for files containing: 'sales', 'registration', 'market', 'ev_data'
    """
    if path is None:
        files = _find_csv(RAW_DIR, ["sales", "registration", "market", "ev_data"])
        if not files:
            files = _find_csv(PROCESSED_DIR, ["sales", "registration", "market"])
    else:
        files = [path]
    
    if not files:
        raise FileNotFoundError(
            f"No EV sales CSV found in {RAW_DIR}.\n"
            f"Run: python download_datasets.py"
        )
    
    dfs = []
    for p in files:
        print(f"  📂 Loading EV sales from: {os.path.basename(p)}")
        dfs.append(pd.read_csv(p))
    
    df = pd.concat(dfs, ignore_index=True)
    print(f"     → {len(df)} rows (Total merged)")
    return df


def load_stations(path: Optional[str] = None) -> pd.DataFrame:
    """
    Load EV charging station location data.
    
    Looks for files containing: 'station', 'charging', 'charger', 'location'
    """
    if path is None:
        files = _find_csv(RAW_DIR, ["station", "charging_station", "charger", "location"])
        if not files:
            files = _find_csv(PROCESSED_DIR, ["station", "charger"])
    else:
        files = [path]
    
    if not files:
        raise FileNotFoundError(
            f"No station CSV found in {RAW_DIR}.\n"
            f"Run: python download_datasets.py"
        )
    
    dfs = []
    for p in files:
        print(f"  📂 Loading stations from: {os.path.basename(p)}")
        try:
            dfs.append(pd.read_csv(p))
        except Exception:
            pass # Skip empty/bad files
            
    if not dfs:
        raise FileNotFoundError("Could not load any station files.")

    df = pd.concat(dfs, ignore_index=True)
    print(f"     → {len(df)} rows (Total merged)")
    return df


def load_usage(path: Optional[str] = None) -> pd.DataFrame:
    """
    Load EV charging session/usage data.
    
    Looks for files containing: 'usage', 'session', 'pattern', 'charging_data'
    """
    if path is None:
        files = _find_csv(RAW_DIR, ["usage", "session", "pattern", "charging_data"])
        if not files:
            files = _find_csv(PROCESSED_DIR, ["usage", "session", "pattern"])
    else:
        files = [path]
    
    if not files:
        raise FileNotFoundError(
            f"No usage/session CSV found in {RAW_DIR}.\n"
            f"Run: python download_datasets.py"
        )
    
    dfs = []
    for p in files:
        print(f"  📂 Loading usage data from: {os.path.basename(p)}")
        try:
            dfs.append(pd.read_csv(p))
        except Exception:
            pass # Skip bad files

    if not dfs:
        raise FileNotFoundError("Could not load any usage files.")

    df = pd.concat(dfs, ignore_index=True)
    print(f"     → {len(df)} rows (Total merged)")
    return df


def load_all() -> Dict[str, pd.DataFrame]:
    """
    Load all available datasets.
    Returns a dict: {"ev_sales": df, "stations": df, "usage": df}
    Only includes datasets that are found on disk.
    """
    datasets = {}
    
    for name, loader in [("ev_sales", load_ev_sales), 
                          ("stations", load_stations), 
                          ("usage", load_usage)]:
        try:
            datasets[name] = loader()
        except FileNotFoundError as e:
            print(f"  ⚠️  {name}: {e}")
    
    print(f"\n  📊 Loaded {len(datasets)} / 3 datasets")
    return datasets


def list_available_files() -> None:
    """Print all CSV files available in data/raw/ and data/processed/."""
    print("\n  📁 Available Data Files:")
    print("  " + "─" * 50)
    
    for label, directory in [("raw", RAW_DIR), ("processed", PROCESSED_DIR)]:
        if os.path.exists(directory):
            csvs = [f for f in os.listdir(directory) if f.endswith(".csv")]
            if csvs:
                print(f"\n  [{label}]")
                for f in csvs:
                    size = os.path.getsize(os.path.join(directory, f))
                    print(f"    • {f}  ({size/1024:.1f} KB)")
            else:
                print(f"\n  [{label}] — No CSV files found")
        else:
            print(f"\n  [{label}] — Directory not found")


if __name__ == "__main__":
    print("=" * 60)
    print("  EV INFRASTRUCTURE — DATA INGESTION CHECK")
    print("=" * 60)
    list_available_files()
    print()
    datasets = load_all()
    
    for name, df in datasets.items():
        print(f"\n  {name} columns: {list(df.columns)}")
