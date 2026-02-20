"""
=================================================================
  Demand Forecasting — Predict future EV adoption by state.
  
  Models:
    1. ARIMA (baseline — univariate time-series)
    2. XGBoost (advanced — uses all engineered features)
    3. Prophet (optional — Meta's time-series library)
  
  Usage:
    python -m src.models.forecasting
=================================================================
"""

import os
import sys
import json
import warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder

warnings.filterwarnings("ignore")

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.data.ingestion import load_ev_sales, PROCESSED_DIR, PROJECT_ROOT
from src.data.processing import process_ev_sales
from src.features.engineering import add_time_features, calculate_ev_penetration, add_lag_features


RESULTS_DIR = os.path.join(PROJECT_ROOT, "results", "phase1_forecasting")


# ──────────────────────────────────────────────────────
#  MODEL 1: ARIMA BASELINE
# ──────────────────────────────────────────────────────

def run_arima(series: pd.Series, forecast_periods: int = 12):
    """
    Fit ARIMA model on a univariate time series.
    
    Args:
        series: Monthly EV sales (indexed by date or sequential)
        forecast_periods: How many months to forecast
    
    Returns:
        dict with predictions, metrics, and model info
    """
    try:
        from statsmodels.tsa.arima.model import ARIMA
    except ImportError:
        print("  ⚠️  statsmodels not installed. Run: pip install statsmodels")
        return None
    
    # Train/test split (last `forecast_periods` months = test)
    train = series[:-forecast_periods] if len(series) > forecast_periods else series
    test = series[-forecast_periods:] if len(series) > forecast_periods else series
    
    try:
        model = ARIMA(train, order=(2, 1, 2))
        fitted = model.fit()
        
        forecast = fitted.forecast(steps=len(test))
        
        if len(test) > 0 and len(forecast) > 0:
            rmse = np.sqrt(mean_squared_error(test.values, forecast.values[:len(test)]))
            mae = mean_absolute_error(test.values, forecast.values[:len(test)])
            
            return {
                "model": "ARIMA(2,1,2)",
                "rmse": round(rmse, 2),
                "mae": round(mae, 2),
                "forecast": forecast.tolist(),
                "actual": test.tolist(),
            }
    except Exception as e:
        print(f"  ⚠️  ARIMA failed: {e}")
    
    return None


# ──────────────────────────────────────────────────────
#  MODEL 2: XGBOOST (Advanced)
# ──────────────────────────────────────────────────────

def run_xgboost(df: pd.DataFrame, target_col: str = "ev_sales_count"):
    """
    Train XGBoost model using all engineered features.
    
    This is the PRIMARY model — it uses:
      - Time features (month, quarter, festival season)
      - Lag features (1, 2, 3, 6, 12 month lags)
      - Rolling averages
      - State encoding
      - EV penetration rate
    
    Returns:
        dict with predictions, metrics, feature importances
    """
    try:
        from xgboost import XGBRegressor
    except ImportError:
        print("  ⚠️  xgboost not installed. Run: pip install xgboost")
        return None
    
    df = df.copy()
    
    if target_col not in df.columns:
        print(f"  ❌ Target column '{target_col}' not found!")
        return None
    
    # Drop rows with NaN in target
    df = df.dropna(subset=[target_col])
    
    # Encode categorical columns
    label_encoders = {}
    for col in df.select_dtypes(include=["object", "category"]).columns:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        label_encoders[col] = le
    
    # Select features (exclude target and non-predictive columns)
    exclude = [target_col, "year_month", "topics"]
    feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c not in exclude]
    
    if not feature_cols:
        print("  ❌ No numeric features found!")
        return None
    
    X = df[feature_cols]
    y = df[target_col]
    
    # Drop rows with NaN features (from lag calculations)
    mask = X.notna().all(axis=1)
    X = X[mask]
    y = y[mask]
    
    if len(X) < 20:
        print(f"  ⚠️  Only {len(X)} samples — too few for XGBoost. Need more data.")
        return None
    
    # Time-aware split (last 20% = test)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    # Train
    model = XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=0,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    
    # Predict
    y_pred = model.predict(X_test)
    
    # Metrics
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    # Feature importance
    importance = dict(zip(feature_cols, model.feature_importances_.tolist()))
    importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10])
    
    print(f"  📊 XGBoost Results:")
    print(f"     R² Score:  {r2:.4f}  ({r2*100:.1f}% accuracy)")
    print(f"     RMSE:      {rmse:.2f}")
    print(f"     MAE:       {mae:.2f}")
    print(f"     Features:  {len(feature_cols)}")
    print(f"     Train/Test: {len(X_train)}/{len(X_test)} samples")
    print(f"     Top 3 features: {list(importance.keys())[:3]}")
    
    return {
        "model": "XGBoost",
        "r2": round(r2, 4),
        "rmse": round(rmse, 2),
        "mae": round(mae, 2),
        "n_features": len(feature_cols),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "feature_importance": importance,
        "predictions": y_pred.tolist(),
        "actuals": y_test.tolist(),
        "xgb_model": model,
        "feature_cols": feature_cols,
    }


# ──────────────────────────────────────────────────────
#  VISUALIZATION
# ──────────────────────────────────────────────────────

def plot_results(results: dict, save_dir: str):
    """Generate publication-quality charts for forecasting results."""
    os.makedirs(save_dir, exist_ok=True)
    
    # Style
    plt.style.use("seaborn-v0_8-whitegrid")
    colors = {"actual": "#2196F3", "predicted": "#FF5722", "bar": "#4CAF50"}
    
    # ── Chart 1: Actual vs Predicted ──
    if "actuals" in results and "predictions" in results:
        fig, ax = plt.subplots(figsize=(12, 6))
        x = range(len(results["actuals"]))
        ax.plot(x, results["actuals"], "o-", color=colors["actual"], label="Actual", linewidth=2)
        ax.plot(x, results["predictions"], "s--", color=colors["predicted"], label="Predicted", linewidth=2)
        ax.fill_between(x, results["actuals"], results["predictions"], alpha=0.15, color=colors["predicted"])
        ax.set_title(f"EV Demand: Actual vs Predicted (R² = {results.get('r2', 'N/A')})", fontsize=14, fontweight="bold")
        ax.set_xlabel("Test Samples")
        ax.set_ylabel("EV Sales Count")
        ax.legend(fontsize=12)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        plt.tight_layout()
        plt.savefig(os.path.join(save_dir, "actual_vs_predicted.png"), dpi=150)
        plt.close()
        print(f"  📈 Saved: actual_vs_predicted.png")
    
    # ── Chart 2: Feature Importance ──
    if "feature_importance" in results:
        fi = results["feature_importance"]
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(list(fi.keys()), list(fi.values()), color=colors["bar"], edgecolor="white")
        ax.set_title("Top 10 Feature Importances", fontsize=14, fontweight="bold")
        ax.set_xlabel("Importance Score")
        ax.invert_yaxis()
        plt.tight_layout()
        plt.savefig(os.path.join(save_dir, "feature_importance.png"), dpi=150)
        plt.close()
        print(f"  📊 Saved: feature_importance.png")


# ──────────────────────────────────────────────────────
#  MAIN PIPELINE
# ──────────────────────────────────────────────────────

def run_forecasting_pipeline():
    """
    Complete Phase 1 pipeline:
      1. Load data
      2. Process & engineer features
      3. Train ARIMA (baseline)
      4. Train XGBoost (advanced)
      5. Save results & visualizations
    """
    print("=" * 60)
    print("  PHASE 1: DEMAND FORECASTING PIPELINE")
    print("=" * 60)
    
    # 1. Load
    try:
        # Try processed first, then raw
        processed_path = os.path.join(PROCESSED_DIR, "ev_sales_processed.csv")
        if os.path.exists(processed_path):
            df = pd.read_csv(processed_path)
            print(f"  📂 Loaded processed data: {len(df)} rows")
        else:
            df = load_ev_sales()
            df = process_ev_sales(df)
    except FileNotFoundError as e:
        print(f"\n  ❌ {e}")
        print("  → Please download datasets first: python download_datasets.py")
        return None
    
    # 2. Feature Engineering
    print("\n  🔧 Engineering features...")
    df = add_time_features(df)
    df = calculate_ev_penetration(df)
    df = add_lag_features(df)
    
    print(f"\n  📊 Final dataset: {len(df)} rows × {len(df.columns)} columns")
    print(f"     Columns: {list(df.columns)}")
    
    # 3. Find the best target column
    target_col = None
    for candidate in ["ev_sales_count", "total", "count", "quantity", "sales", "number_of_vehicles"]:
        if candidate in df.columns:
            target_col = candidate
            break
    
    # If no standard name found, look for the largest numeric column
    if target_col is None:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            # Pick the column with the highest mean as the likely "count" column
            means = df[numeric_cols].mean()
            target_col = means.idxmax()
            print(f"  🎯 Auto-detected target column: '{target_col}' (highest mean)")
    
    if target_col is None:
        print("  ❌ Could not find a suitable target column!")
        return None
    
    print(f"\n  🎯 Target: '{target_col}'")
    
    # 4. Run Models
    all_results = {}
    
    # --- XGBoost ---
    print("\n" + "─" * 50)
    print("  MODEL: XGBoost")
    print("─" * 50)
    xgb_result = run_xgboost(df, target_col)
    if xgb_result:
        all_results["xgboost"] = {k: v for k, v in xgb_result.items() if k not in ["xgb_model", "feature_cols"]}
    
    # --- ARIMA (on aggregated national data) ---
    print("\n" + "─" * 50)
    print("  MODEL: ARIMA (National Aggregate)")
    print("─" * 50)
    
    # Aggregate to national monthly
    if "year" in df.columns:
        if "month" in df.columns:
            national = df.groupby(["year", "month"])[target_col].sum().reset_index()
            national = national.sort_values(["year", "month"])
        else:
            national = df.groupby("year")[target_col].sum().reset_index()
            national = national.sort_values("year")
        
        series = national[target_col]
        arima_result = run_arima(series, forecast_periods=min(12, len(series) // 5))
        if arima_result:
            all_results["arima"] = arima_result
    
    # 5. Save Results
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Save metrics
    results_path = os.path.join(RESULTS_DIR, "forecasting_results.json")
    with open(results_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n  💾 Results saved: {results_path}")
    
    # Save processed data with features
    featured_path = os.path.join(PROCESSED_DIR, "ev_sales_featured.csv")
    df.to_csv(featured_path, index=False)
    print(f"  💾 Featured data saved: {featured_path}")
    
    # 6. Visualize
    if xgb_result:
        plot_results(xgb_result, RESULTS_DIR)
    
    # 7. Summary
    print("\n" + "=" * 60)
    print("  PHASE 1 SUMMARY")
    print("=" * 60)
    for model_name, result in all_results.items():
        r2 = result.get("r2", "N/A")
        rmse = result.get("rmse", "N/A")
        print(f"  • {model_name}: R²={r2}, RMSE={rmse}")
    print()
    
    return all_results


if __name__ == "__main__":
    run_forecasting_pipeline()
