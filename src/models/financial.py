"""
=================================================================
  Financial Modeling — Phase 4: ROI & Policy Analysis
  
  Calculates business viability of new charging stations
  incorporating FAME-II subsidies and state incentives.
  
  Usage:
    python -m src.models.financial
=================================================================
"""

import os
import sys
import json
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.data.ingestion import PROJECT_ROOT


RESULTS_DIR = os.path.join(PROJECT_ROOT, "results", "phase4_financial")


# ──────────────────────────────────────────────────────
#  CONSTANTS — Indian EV Economics
# ──────────────────────────────────────────────────────

# Average costs (INR)
STATION_SETUP_COST = {
    "slow_ac": 100_000,    # ₹1 Lakh for slow AC charger
    "fast_dc": 2_500_000,  # ₹25 Lakh for fast DC charger
    "ultra_fast": 5_000_000,  # ₹50 Lakh for 150kW+ charger
}

# Revenue assumptions
ELECTRICITY_COST_PER_KWH = 8.0   # ₹8/kWh (commercial rate)
SELLING_PRICE_PER_KWH = 15.0     # ₹15/kWh (charging price)
AVG_SESSIONS_PER_DAY = 10        # Moderate utilization
AVG_KWH_PER_SESSION = 25.0       # Average energy per session

# Government subsidies
FAME_II_SUBSIDY_PCT = 0.40       # 40% of equipment cost
STATE_SUBSIDIES = {
    "Delhi": {"per_charger": 10_000, "max_pct": 0.25},
    "Maharashtra": {"per_charger": 5_000, "max_pct": 0.20},
    "Karnataka": {"per_charger": 7_500, "max_pct": 0.20},
    "Tamil Nadu": {"per_charger": 5_000, "max_pct": 0.15},
    "Gujarat": {"per_charger": 8_000, "max_pct": 0.25},
    "UP": {"per_charger": 5_000, "max_pct": 0.15},
    "Default": {"per_charger": 3_000, "max_pct": 0.10},
}

# Environmental impact
CO2_SAVED_PER_KWH = 0.82  # kg CO2 saved per kWh (EV vs ICE equivalent)
TREES_EQUIVALENT_PER_TON_CO2 = 50  # 1 ton CO2 ≈ 50 trees/year


# ──────────────────────────────────────────────────────
#  ROI CALCULATOR
# ──────────────────────────────────────────────────────

def calculate_roi(
    station_type: str = "fast_dc",
    state: str = "Delhi",
    sessions_per_day: int = AVG_SESSIONS_PER_DAY,
    kwh_per_session: float = AVG_KWH_PER_SESSION,
    years: int = 10,
):
    """
    Calculate the financial ROI for a new charging station.
    
    Returns:
        dict with NPV, IRR, breakeven_months, yearly_cashflows
    """
    # Setup cost
    setup_cost = STATION_SETUP_COST.get(station_type, STATION_SETUP_COST["fast_dc"])
    
    # Subsidies
    fame_subsidy = setup_cost * FAME_II_SUBSIDY_PCT
    state_info = STATE_SUBSIDIES.get(state, STATE_SUBSIDIES["Default"])
    state_subsidy = min(state_info["per_charger"], setup_cost * state_info["max_pct"])
    
    net_cost = setup_cost - fame_subsidy - state_subsidy
    
    # Revenue per year
    daily_energy = sessions_per_day * kwh_per_session
    daily_revenue = daily_energy * (SELLING_PRICE_PER_KWH - ELECTRICITY_COST_PER_KWH)
    annual_revenue = daily_revenue * 365
    
    # Operating costs (maintenance, rent, internet)
    annual_opex = annual_revenue * 0.25  # 25% of revenue
    annual_profit = annual_revenue - annual_opex
    
    # Cash flows
    cashflows = [-net_cost]  # Year 0
    cumulative = [-net_cost]
    
    for year in range(1, years + 1):
        # 5% annual growth in sessions
        growth_factor = 1.05 ** (year - 1)
        profit = annual_profit * growth_factor
        cashflows.append(round(profit, 0))
        cumulative.append(round(cumulative[-1] + profit, 0))
    
    # Breakeven
    breakeven_year = None
    for i, c in enumerate(cumulative):
        if c >= 0:
            breakeven_year = i
            break
    
    breakeven_months = breakeven_year * 12 if breakeven_year else None
    
    # NPV (10% discount rate)
    discount_rate = 0.10
    npv = sum(cf / (1 + discount_rate) ** i for i, cf in enumerate(cashflows))
    
    # Simple IRR approximation
    total_return = sum(cashflows[1:])
    irr = (total_return / net_cost) / years * 100 if net_cost > 0 else 0
    
    # Environmental impact per year
    annual_kwh = daily_energy * 365
    annual_co2_saved = annual_kwh * CO2_SAVED_PER_KWH / 1000  # tons
    trees_equivalent = annual_co2_saved * TREES_EQUIVALENT_PER_TON_CO2
    
    result = {
        "station_type": station_type,
        "state": state,
        "setup_cost_inr": setup_cost,
        "fame_subsidy_inr": round(fame_subsidy, 0),
        "state_subsidy_inr": round(state_subsidy, 0),
        "net_investment_inr": round(net_cost, 0),
        "annual_revenue_inr": round(annual_revenue, 0),
        "annual_profit_inr": round(annual_profit, 0),
        "breakeven_months": breakeven_months,
        "npv_inr": round(npv, 0),
        "irr_pct": round(irr, 1),
        "yearly_cashflows": cashflows,
        "yearly_cumulative": cumulative,
        "environmental_impact": {
            "annual_co2_saved_tons": round(annual_co2_saved, 1),
            "trees_equivalent": int(trees_equivalent),
            "annual_kwh_delivered": round(annual_kwh, 0),
        },
    }
    
    return result


def run_financial_analysis():
    """Run ROI analysis for multiple scenarios."""
    print("=" * 60)
    print("  PHASE 4: FINANCIAL & POLICY MODELING")
    print("=" * 60)
    
    scenarios = [
        {"station_type": "slow_ac", "state": "Delhi", "sessions_per_day": 8},
        {"station_type": "fast_dc", "state": "Delhi", "sessions_per_day": 12},
        {"station_type": "fast_dc", "state": "Maharashtra", "sessions_per_day": 10},
        {"station_type": "fast_dc", "state": "Karnataka", "sessions_per_day": 10},
        {"station_type": "ultra_fast", "state": "Delhi", "sessions_per_day": 15},
    ]
    
    results = []
    
    for scenario in scenarios:
        print(f"\n  {'─' * 50}")
        print(f"  Scenario: {scenario['station_type']} in {scenario['state']}")
        roi = calculate_roi(**scenario)
        results.append(roi)
        
        print(f"     Setup Cost:      ₹{roi['setup_cost_inr']:,.0f}")
        print(f"     Net Investment:  ₹{roi['net_investment_inr']:,.0f} (after subsidies)")
        print(f"     Annual Profit:   ₹{roi['annual_profit_inr']:,.0f}")
        print(f"     Breakeven:       {roi['breakeven_months']} months")
        print(f"     NPV (10yr):      ₹{roi['npv_inr']:,.0f}")
        print(f"     CO₂ Saved/yr:    {roi['environmental_impact']['annual_co2_saved_tons']} tons")
    
    # Save
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, "financial_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n  💾 Saved: {RESULTS_DIR}/financial_results.json")
    
    # Summary table
    print("\n" + "=" * 60)
    print("  FINANCIAL SUMMARY")
    print("=" * 60)
    summary = pd.DataFrame([{
        "Type": r["station_type"],
        "State": r["state"],
        "Investment": f"₹{r['net_investment_inr']:,.0f}",
        "Annual Profit": f"₹{r['annual_profit_inr']:,.0f}",
        "Breakeven": f"{r['breakeven_months']}mo" if r["breakeven_months"] else "N/A",
        "NPV": f"₹{r['npv_inr']:,.0f}",
    } for r in results])
    print(summary.to_string(index=False))
    
    return results


if __name__ == "__main__":
    run_financial_analysis()
