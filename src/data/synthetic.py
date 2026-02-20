"""
=================================================================
  Synthetic Data Generator — Realistic Indian Context
  
  Since external data links can be flaky, this module generates
  HIGH-QUALITY synthetic data that mirrors real-world patterns.
  
  Generates:
    1. EV Sales (State-wise, monthly, growing trend)
    2. Charging Stations (Real city lat/longs, clustered)
    3. Usage Data (Peak hours, realistic energy/session)
    
  Usage:
    python -m src.data.synthetic
=================================================================
"""

import os
import sys
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.data.ingestion import RAW_DIR

# ──────────────────────────────────────────────────────
#  CONSTANTS — REAL INDIAN DATA POINTS
# ──────────────────────────────────────────────────────

INDIAN_CITIES = {
    "Delhi": (28.7041, 77.1025),
    "Mumbai": (19.0760, 72.8777),
    "Bangalore": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Hyderabad": (17.3850, 78.4867),
    "Pune": (18.5204, 73.8567),
    "Ahmedabad": (23.0225, 72.5714),
    "Jaipur": (26.9124, 75.7873),
    "Lucknow": (26.8467, 80.9462),
    "Kolkata": (22.5726, 88.3639),
}

STATES = [
    "Maharashtra", "Karnataka", "Tamil Nadu", "Delhi", "Gujarat", 
    "Uttar Pradesh", "Rajasthan", "Telangana", "West Bengal", "Kerala"
]

OPERATORS = ["Tata Power", "Statiq", "Ather Grid", "ChargeZone", "Zeon Charging", "BluSmart"]
CONNECTOR_TYPES = ["CCS2", "Type 2", "Bharat DC-001", "GB/T"]


# ──────────────────────────────────────────────────────
#  GENERATORS
# ──────────────────────────────────────────────────────

def generate_ev_sales(years=[2022, 2023, 2024, 2025]):
    """Generate monthly EV sales data with realistic growth trends."""
    print("  🏭 Generating Synthetic EV Sales Data...")
    
    data = []
    
    # Base adoption rates (Maharashtra/Karnataka leads)
    state_weights = {
        "Maharashtra": 1.5, "Karnataka": 1.3, "Delhi": 1.4, 
        "Tamil Nadu": 1.2, "Gujarat": 1.1, "Uttar Pradesh": 0.8,
        "Rajasthan": 0.7, "Telangana": 1.1, "West Bengal": 0.6, "Kerala": 1.0
    }
    
    for year in years:
        for month in range(1, 13):
            # Seasonal factor (festival season spike in Q4)
            seasonality = 1.2 if month in [10, 11] else 1.0
            
            # Yearly growth factor (exponential adoption)
            growth = 1.5 ** (year - 2022)
            
            for state in STATES:
                base_sales = random.randint(500, 1500)
                weight = state_weights.get(state, 1.0)
                
                # Randomized categories
                sales_2w = int(base_sales * weight * growth * seasonality * 0.7)  # 70% 2W
                sales_3w = int(base_sales * weight * growth * seasonality * 0.2)  # 20% 3W
                sales_4w = int(base_sales * weight * growth * seasonality * 0.1)  # 10% 4W
                
                # Create row
                data.append({
                    "date": f"{year}-{month:02d}-01",
                    "state": state,
                    "vehicle_category": "2W",
                    "ev_sales_count": sales_2w,
                    "year": year,
                    "month": month
                })
                data.append({
                    "date": f"{year}-{month:02d}-01",
                    "state": state,
                    "vehicle_category": "3W",
                    "ev_sales_count": sales_3w,
                    "year": year,
                    "month": month
                })
                data.append({
                    "date": f"{year}-{month:02d}-01",
                    "state": state,
                    "vehicle_category": "4W",
                    "ev_sales_count": sales_4w,
                    "year": year,
                    "month": month
                })
    
    df = pd.DataFrame(data)
    save_path = os.path.join(RAW_DIR, "synthetic_ev_sales.csv")
    df.to_csv(save_path, index=False)
    print(f"     ✅ Saved {len(df)} rows to {save_path}")
    return df


def generate_stations(n_stations=500):
    """Generate station locations clustered around major cities."""
    print("  🏭 Generating Synthetic Charging Stations...")
    
    data = []
    
    for _ in range(n_stations):
        # Pick a city center
        city_name = random.choice(list(INDIAN_CITIES.keys()))
        base_lat, base_lon = INDIAN_CITIES[city_name]
        
        # Add random jitter (within ~10km)
        lat = base_lat + random.uniform(-0.1, 0.1)
        lon = base_lon + random.uniform(-0.1, 0.1)
        
        op = random.choice(OPERATORS)
        conn = random.choice(CONNECTOR_TYPES)
        power = random.choice([7.4, 22, 50, 60, 150]) if "DC" in conn or "CCS" in conn else 7.4
        
        # Determine state roughly based on city
        state = "Maharashtra" if city_name in ["Mumbai", "Pune"] else \
                "Karnataka" if city_name == "Bangalore" else \
                "Delhi" if city_name == "Delhi" else \
                "Tamil Nadu" if city_name == "Chennai" else "Other"
        
        data.append({
            "station_id": f"STN_{random.randint(1000, 9999)}",
            "operator": op,
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "city": city_name,
            "state": state,
            "connector_type": conn,
            "power_kw": power,
            "status": "Operational"
        })
        
    df = pd.DataFrame(data)
    save_path = os.path.join(RAW_DIR, "synthetic_stations.csv")
    df.to_csv(save_path, index=False)
    print(f"     ✅ Saved {len(df)} rows to {save_path}")
    return df


def generate_usage(n_sessions=5000):
    """Generate charging sessions with realistic load profiles."""
    print("  🏭 Generating Synthetic Usage Data...")
    
    data = []
    start_date = datetime(2024, 1, 1)
    
    for _ in range(n_sessions):
        # Realistic time of day (Peak: 6PM-9PM, Low: 2AM-5AM)
        hour_weight = [0.02]*6 + [0.05]*6 + [0.08]*6 + [0.10]*6  # biased towards evening
        hour = random.choices(range(24), weights=hour_weight)[0]
        
        day_offset = random.randint(0, 365)
        session_start = start_date + timedelta(days=day_offset, hours=hour, minutes=random.randint(0, 59))
        
        # Duration & Energy
        vehicle = random.choice(["2W", "3W", "4W"])
        if vehicle == "2W":
            energy = random.uniform(1.5, 3.5)  # kWh
            duration_mins = random.uniform(30, 120)
        elif vehicle == "4W":
            energy = random.uniform(20, 60)    # kWh
            duration_mins = random.uniform(45, 180)
        else:
            energy = random.uniform(5, 10)
            duration_mins = random.uniform(40, 90)
            
        session_end = session_start + timedelta(minutes=duration_mins)
        cost = energy * random.uniform(15, 18)  # ₹15-18 per unit
        
        data.append({
            "session_id": f"SES_{random.randint(10000, 99999)}",
            "start_time": session_start.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": session_end.strftime("%Y-%m-%d %H:%M:%S"),
            "energy_kwh": round(energy, 2),
            "duration_minutes": round(duration_mins, 1),
            "cost_inr": round(cost, 2),
            "vehicle_type": vehicle
        })
        
    df = pd.DataFrame(data)
    save_path = os.path.join(RAW_DIR, "synthetic_usage.csv")
    df.to_csv(save_path, index=False)
    print(f"     ✅ Saved {len(df)} rows to {save_path}")
    return df


def generate_all():
    print("=" * 60)
    print("  SYNTHETIC DATA GENERATOR — INDIA CONTEXT")
    print("=" * 60)
    os.makedirs(RAW_DIR, exist_ok=True)
    
    generate_ev_sales()
    generate_stations()
    generate_usage()
    
    print("\n  ✨ Synthetic data generation complete!")
    print("     You can now run: python main.py --process --all")


if __name__ == "__main__":
    generate_all()
