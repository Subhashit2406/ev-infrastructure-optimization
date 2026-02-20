"""
=================================================================
  EV Infrastructure Project — Dataset Downloader
  Downloads real-world datasets from Kaggle using opendatasets.
  
  Usage:
    python download_datasets.py
  
  You will be prompted for your Kaggle username and API key.
  Get your key from: https://www.kaggle.com/settings → API → Create New Token
=================================================================
"""

import os
import sys
import shutil

def check_dependencies():
    """Install opendatasets if not present."""
    try:
        import opendatasets
    except ImportError:
        print("Installing opendatasets...")
        os.system(f"{sys.executable} -m pip install opendatasets -q")

def download_all():
    import opendatasets as od
    
    RAW_DIR = os.path.join("data", "raw")
    os.makedirs(RAW_DIR, exist_ok=True)
    
    # ─────────────────────────────────────────────
    # Dataset 1: Indian EV Sales / Registrations
    #   Source: Vahan Dashboard (cleaned)
    #   Contents: State-wise, category-wise (2W/3W/4W), monthly EV registrations
    # ─────────────────────────────────────────────
    DATASETS = {
        "ev_sales": {
            "url": "https://www.kaggle.com/datasets/srinrealyf/indian-ev-market-data",
            "description": "Indian EV Market Data (2001-2024) — Vahan Dashboard source"
        },
        "ev_stations": {
            "url": "https://www.kaggle.com/datasets/saketpradhan/electric-vehicle-charging-stations-in-india",
            "description": "EV Charging Stations in India — Lat/Long, Type, Operator"
        },
        "ev_usage": {
            "url": "https://www.kaggle.com/datasets/valakhorasani/electric-vehicle-charging-patterns",
            "description": "EV Charging Patterns — Session duration, energy, user behavior"
        },
    }
    
    print("=" * 60)
    print("  EV INFRASTRUCTURE PROJECT — DATA DOWNLOADER")
    print("=" * 60)
    print()
    print("You will need your Kaggle credentials.")
    print("Get them from: https://www.kaggle.com/settings → API")
    print()
    
    for key, info in DATASETS.items():
        print(f"\n{'─' * 50}")
        print(f"  Downloading: {info['description']}")
        print(f"  URL: {info['url']}")
        print(f"{'─' * 50}")
        try:
            od.download(info["url"], data_dir=RAW_DIR)
            print(f"  ✅ {key} downloaded successfully!")
        except Exception as e:
            print(f"  ❌ Error downloading {key}: {e}")
            print(f"  → You can manually download from: {info['url']}")
    
    # Move files from subfolders to raw/ for easy access
    print("\n\nOrganizing downloaded files...")
    for subfolder in os.listdir(RAW_DIR):
        subfolder_path = os.path.join(RAW_DIR, subfolder)
        if os.path.isdir(subfolder_path):
            for fname in os.listdir(subfolder_path):
                src = os.path.join(subfolder_path, fname)
                dst = os.path.join(RAW_DIR, fname)
                if os.path.isfile(src) and not os.path.exists(dst):
                    shutil.move(src, dst)
                    print(f"  Moved: {fname}")
    
    print("\n" + "=" * 60)
    print("  DOWNLOAD COMPLETE!")
    print("=" * 60)
    print(f"\n  Files are in: {os.path.abspath(RAW_DIR)}")
    print("\n  Next step: Run the data processing pipeline")
    print("    python -m src.data.processing")
    print()

if __name__ == "__main__":
    check_dependencies()
    download_all()
