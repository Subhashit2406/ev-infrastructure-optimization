"""
=================================================================
  Grid Load Optimization — Phase 3
  
  Models the impact of EV charging on the grid and finds
  the optimal charging schedule to reduce peak load.
  
  Uses Linear Programming (PuLP) to minimize peak demand.
  
  Usage:
    python -m src.models.optimization
=================================================================
"""

import os
import sys
import json
import warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.data.ingestion import load_usage, PROCESSED_DIR, PROJECT_ROOT
from src.data.processing import process_usage
from src.features.engineering import add_usage_features


RESULTS_DIR = os.path.join(PROJECT_ROOT, "results", "phase3_optimization")


# ──────────────────────────────────────────────────────
#  LOAD PROFILE ANALYSIS
# ──────────────────────────────────────────────────────

def analyze_load_profile(df: pd.DataFrame):
    """
    Analyze the hourly charging load profile.
    
    Returns peak hour, off-peak hours, and utilization metrics.
    """
    if "hour_of_day" not in df.columns:
        print("  ⚠️  No 'hour_of_day' column. Cannot create load profile.")
        return None
    
    energy_col = None
    for candidate in ["energy_kwh", "energy", "kwh", "power"]:
        if candidate in df.columns:
            energy_col = candidate
            break
    
    if energy_col is None:
        # Use session count as proxy
        hourly = df.groupby("hour_of_day").size().reset_index(name="load")
    else:
        hourly = df.groupby("hour_of_day")[energy_col].sum().reset_index()
        hourly.columns = ["hour_of_day", "load"]
    
    # Normalize to percentage
    hourly["load_pct"] = (hourly["load"] / hourly["load"].sum() * 100).round(2)
    
    peak_hour = hourly.loc[hourly["load"].idxmax(), "hour_of_day"]
    off_peak = hourly.loc[hourly["load"].idxmin(), "hour_of_day"]
    peak_to_avg = hourly["load"].max() / hourly["load"].mean()
    
    print(f"  ⚡ Load Profile Analysis:")
    print(f"     Peak Hour:        {int(peak_hour)}:00 ({hourly['load_pct'].max():.1f}% of daily load)")
    print(f"     Off-Peak Hour:    {int(off_peak)}:00 ({hourly['load_pct'].min():.1f}% of daily load)")
    print(f"     Peak/Avg Ratio:   {peak_to_avg:.2f}x")
    
    return {
        "hourly_profile": hourly.to_dict(orient="records"),
        "peak_hour": int(peak_hour),
        "off_peak_hour": int(off_peak),
        "peak_to_avg_ratio": round(peak_to_avg, 2),
    }


# ──────────────────────────────────────────────────────
#  LINEAR PROGRAMMING OPTIMIZATION (PuLP)
# ──────────────────────────────────────────────────────

def optimize_charging_schedule(hourly_profile: list, shift_pct: float = 0.3):
    """
    Use Linear Programming to find optimal charging schedule.
    
    Goal: Shift `shift_pct` of peak-hour load to off-peak hours.
    
    Args:
        hourly_profile: list of {"hour_of_day": int, "load": float}
        shift_pct: fraction of peak load to shift (0.3 = 30%)
    
    Returns:
        Optimized profile and savings metrics
    """
    try:
        from pulp import LpProblem, LpMinimize, LpVariable, lpSum, value
    except ImportError:
        print("  ⚠️  PuLP not installed. Run: pip install pulp")
        print("  → Falling back to heuristic optimization...")
        return _heuristic_optimization(hourly_profile, shift_pct)
    
    hours = len(hourly_profile)
    original_load = [h["load"] for h in hourly_profile]
    total_load = sum(original_load)
    
    # Decision variables: how much load to assign to each hour
    prob = LpProblem("ChargingSchedule", LpMinimize)
    x = [LpVariable(f"load_{i}", lowBound=0) for i in range(hours)]
    
    # Objective: minimize peak load (minimize max load)
    peak = LpVariable("peak_load", lowBound=0)
    prob += peak  # minimize peak
    
    # Constraints
    for i in range(hours):
        prob += x[i] <= peak  # each hour's load <= peak
    
    prob += lpSum(x) == total_load  # total energy must be conserved
    
    # Each hour must have at least some minimum load (can't be zero)
    for i in range(hours):
        prob += x[i] >= original_load[i] * (1 - shift_pct)
    
    prob.solve()
    
    if prob.status == 1:  # Optimal
        optimized_load = [value(x[i]) for i in range(hours)]
        
        original_peak = max(original_load)
        optimized_peak = max(optimized_load)
        reduction = (1 - optimized_peak / original_peak) * 100
        
        print(f"  ✅ LP Optimization Results:")
        print(f"     Original Peak:   {original_peak:.0f}")
        print(f"     Optimized Peak:  {optimized_peak:.0f}")
        print(f"     Peak Reduction:  {reduction:.1f}%")
        
        return {
            "method": "Linear Programming (PuLP)",
            "original_load": original_load,
            "optimized_load": optimized_load,
            "original_peak": round(original_peak, 2),
            "optimized_peak": round(optimized_peak, 2),
            "peak_reduction_pct": round(reduction, 2),
        }
    else:
        print("  ⚠️  LP solver did not find optimal solution. Using heuristic.")
        return _heuristic_optimization(hourly_profile, shift_pct)


def _heuristic_optimization(hourly_profile: list, shift_pct: float = 0.3):
    """Fallback: simple rule-based load shifting."""
    original_load = [h["load"] for h in hourly_profile]
    avg_load = np.mean(original_load)
    
    optimized = []
    excess = 0
    
    # Pass 1: Shave peaks
    for load in original_load:
        if load > avg_load * 1.2:
            shaved = load * shift_pct
            optimized.append(load - shaved)
            excess += shaved
        else:
            optimized.append(load)
    
    # Pass 2: Fill valleys
    for i in range(len(optimized)):
        if optimized[i] < avg_load * 0.8 and excess > 0:
            fill = min(excess, avg_load - optimized[i])
            optimized[i] += fill
            excess -= fill
    
    original_peak = max(original_load)
    optimized_peak = max(optimized)
    reduction = (1 - optimized_peak / original_peak) * 100
    
    print(f"  ✅ Heuristic Optimization Results:")
    print(f"     Original Peak:   {original_peak:.0f}")
    print(f"     Optimized Peak:  {optimized_peak:.0f}")
    print(f"     Peak Reduction:  {reduction:.1f}%")
    
    return {
        "method": "Heuristic (Peak Shaving)",
        "original_load": original_load,
        "optimized_load": optimized,
        "original_peak": round(original_peak, 2),
        "optimized_peak": round(optimized_peak, 2),
        "peak_reduction_pct": round(reduction, 2),
    }


# ──────────────────────────────────────────────────────
#  VISUALIZATION
# ──────────────────────────────────────────────────────

def plot_load_comparison(opt_result: dict, save_dir: str):
    """Plot before vs after optimization."""
    os.makedirs(save_dir, exist_ok=True)
    
    hours = list(range(24))
    orig = opt_result["original_load"]
    opt = opt_result["optimized_load"]
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    width = 0.35
    x = np.arange(len(hours))
    
    bars1 = ax.bar(x - width/2, orig, width, label="Before Optimization", color="#FF5722", alpha=0.8)
    bars2 = ax.bar(x + width/2, opt, width, label="After Optimization", color="#4CAF50", alpha=0.8)
    
    ax.axhline(y=np.mean(orig), color="#FF5722", linestyle="--", alpha=0.5, label="Avg (Before)")
    ax.axhline(y=np.mean(opt), color="#4CAF50", linestyle="--", alpha=0.5, label="Avg (After)")
    
    ax.set_title(
        f"Grid Load: Before vs After Optimization ({opt_result['peak_reduction_pct']:.1f}% peak reduction)",
        fontsize=14, fontweight="bold",
    )
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Load (kWh)")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{h}:00" for h in hours], rotation=45, ha="right")
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, "load_optimization.png"), dpi=150)
    plt.close()
    print(f"  📈 Saved: load_optimization.png")


# ──────────────────────────────────────────────────────
#  MAIN PIPELINE
# ──────────────────────────────────────────────────────

def run_optimization_pipeline():
    """Complete Phase 3 pipeline."""
    print("=" * 60)
    print("  PHASE 3: GRID IMPACT & LOAD OPTIMIZATION")
    print("=" * 60)
    
    # 1. Load usage data
    try:
        processed_path = os.path.join(PROCESSED_DIR, "usage_processed.csv")
        if os.path.exists(processed_path):
            df = pd.read_csv(processed_path)
            print(f"  📂 Loaded processed data: {len(df)} rows")
        else:
            df = load_usage()
            df = process_usage(df)
    except FileNotFoundError as e:
        print(f"\n  ❌ {e}")
        return None
    
    # 2. Add usage features
    df = add_usage_features(df)
    
    # 3. Analyze load profile
    print("\n" + "─" * 50)
    print("  LOAD PROFILE ANALYSIS")
    print("─" * 50)
    profile = analyze_load_profile(df)
    
    if profile is None:
        return None
    
    # 4. Optimize
    print("\n" + "─" * 50)
    print("  CHARGING SCHEDULE OPTIMIZATION")
    print("─" * 50)
    opt_result = optimize_charging_schedule(profile["hourly_profile"])
    
    # 5. Save & visualize
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    all_results = {"load_profile": profile, "optimization": opt_result}
    
    with open(os.path.join(RESULTS_DIR, "optimization_results.json"), "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    
    if opt_result:
        plot_load_comparison(opt_result, RESULTS_DIR)
    
    print("\n" + "=" * 60)
    print("  PHASE 3 COMPLETE")
    print("=" * 60)
    
    return all_results


if __name__ == "__main__":
    run_optimization_pipeline()
