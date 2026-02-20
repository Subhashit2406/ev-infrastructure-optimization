"""
=================================================================
  Geospatial Clustering — Find optimal station locations.
  
  Phase 2: Identifies "White Spaces" (high demand, low infrastructure)
  using K-Means and DBSCAN clustering on station coordinates.
  
  Usage:
    python -m src.models.clustering
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

from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.data.ingestion import load_stations, PROCESSED_DIR, PROJECT_ROOT
from src.data.processing import process_stations
from src.features.engineering import add_station_density


RESULTS_DIR = os.path.join(PROJECT_ROOT, "results", "phase2_geospatial")


# ──────────────────────────────────────────────────────
#  K-MEANS CLUSTERING
# ──────────────────────────────────────────────────────

def run_kmeans(df: pd.DataFrame, n_clusters: int = 6, features: list = None):
    """
    Cluster charging stations to find natural groups.
    
    Args:
        df: Station data with latitude, longitude
        n_clusters: Number of clusters
        features: Columns to cluster on (default: lat, lon)
    
    Returns:
        dict with cluster labels, centers, and metrics
    """
    if features is None:
        features = ["latitude", "longitude"]
    
    available = [f for f in features if f in df.columns]
    if len(available) < 2:
        print(f"  ❌ Need at least 2 features. Found: {available}")
        return None
    
    X = df[available].dropna()
    
    if len(X) < n_clusters:
        print(f"  ⚠️  Only {len(X)} stations, reducing clusters to {len(X) - 1}")
        n_clusters = max(2, len(X) - 1)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Find optimal K using elbow method
    inertias = []
    silhouettes = []
    K_range = range(2, min(12, len(X)))
    
    for k in K_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        inertias.append(km.inertia_)
        silhouettes.append(silhouette_score(X_scaled, labels))
    
    # Best K by silhouette
    best_k = list(K_range)[np.argmax(silhouettes)]
    best_silhouette = max(silhouettes)
    
    # Final model with best K
    km_final = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    df_result = df.loc[X.index].copy()
    df_result["cluster"] = km_final.fit_predict(X_scaled)
    
    # Cluster centers (unscaled)
    centers = scaler.inverse_transform(km_final.cluster_centers_)
    center_df = pd.DataFrame(centers, columns=available)
    
    # Cluster summary
    cluster_summary = df_result.groupby("cluster").agg(
        station_count=("cluster", "size"),
        avg_lat=("latitude", "mean"),
        avg_lon=("longitude", "mean"),
    ).reset_index()
    
    if "power_kw" in df_result.columns:
        power_summary = df_result.groupby("cluster")["power_kw"].mean().reset_index()
        power_summary.columns = ["cluster", "avg_power_kw"]
        cluster_summary = cluster_summary.merge(power_summary, on="cluster")
    
    print(f"  📊 K-Means Results:")
    print(f"     Optimal K:        {best_k}")
    print(f"     Silhouette Score: {best_silhouette:.4f}")
    print(f"     Cluster sizes:    {dict(df_result['cluster'].value_counts())}")
    
    return {
        "model": "K-Means",
        "optimal_k": best_k,
        "silhouette_score": round(best_silhouette, 4),
        "cluster_summary": cluster_summary.to_dict(orient="records"),
        "elbow_data": {"k": list(K_range), "inertia": inertias, "silhouette": silhouettes},
        "clustered_data": df_result,
        "centers": center_df.to_dict(orient="records"),
    }


# ──────────────────────────────────────────────────────
#  DBSCAN (Density-based — handles noise)
# ──────────────────────────────────────────────────────

def run_dbscan(df: pd.DataFrame, eps: float = 0.5, min_samples: int = 3):
    """
    DBSCAN clustering — finds arbitrarily-shaped clusters.
    Points not in any cluster = noise (label = -1).
    """
    features = ["latitude", "longitude"]
    available = [f for f in features if f in df.columns]
    
    if len(available) < 2:
        return None
    
    X = df[available].dropna()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    db = DBSCAN(eps=eps, min_samples=min_samples)
    labels = db.fit_predict(X_scaled)
    
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = (labels == -1).sum()
    
    df_result = df.loc[X.index].copy()
    df_result["cluster"] = labels
    
    sil = silhouette_score(X_scaled, labels) if n_clusters >= 2 else 0
    
    print(f"  📊 DBSCAN Results:")
    print(f"     Clusters found:   {n_clusters}")
    print(f"     Noise points:     {n_noise}")
    print(f"     Silhouette Score: {sil:.4f}")
    
    return {
        "model": "DBSCAN",
        "n_clusters": n_clusters,
        "n_noise": int(n_noise),
        "silhouette_score": round(sil, 4),
        "clustered_data": df_result,
    }


# ──────────────────────────────────────────────────────
#  WHITE SPACE ANALYSIS
# ──────────────────────────────────────────────────────

def find_white_spaces(stations_df: pd.DataFrame, sales_df: pd.DataFrame = None):
    """
    Identify areas with HIGH demand but LOW charger density.
    
    These are the optimal locations for new stations.
    """
    # Group stations by state
    if "state" in stations_df.columns:
        density = stations_df.groupby("state").agg(
            n_stations=("state", "size"),
        ).reset_index()
        
        # If we have sales data, merge to find gaps
        if sales_df is not None and "state" in sales_df.columns:
            # Get latest year's total sales per state
            if "year" in sales_df.columns:
                latest_year = sales_df["year"].max()
                recent = sales_df[sales_df["year"] == latest_year]
            else:
                recent = sales_df
            
            # Find sales column
            sales_col = None
            for candidate in ["ev_sales_count", "total", "count", "sales"]:
                if candidate in recent.columns:
                    sales_col = candidate
                    break
            
            if sales_col:
                state_sales = recent.groupby("state")[sales_col].sum().reset_index()
                state_sales.columns = ["state", "total_ev_sales"]
                
                merged = density.merge(state_sales, on="state", how="outer").fillna(0)
                merged["sales_per_station"] = merged["total_ev_sales"] / merged["n_stations"].replace(0, np.nan)
                merged["gap_score"] = merged["total_ev_sales"] / (merged["n_stations"] + 1)
                merged = merged.sort_values("gap_score", ascending=False)
                
                print(f"  🗺️  White Space Analysis (Top 10):")
                print(merged.head(10).to_string(index=False))
                
                return merged
    
    return None


# ──────────────────────────────────────────────────────
#  VISUALIZATION
# ──────────────────────────────────────────────────────

def plot_clusters(result: dict, save_dir: str):
    """Plot station clusters on a scatter map."""
    os.makedirs(save_dir, exist_ok=True)
    
    if "clustered_data" not in result:
        return
    
    df = result["clustered_data"]
    
    if "latitude" not in df.columns or "longitude" not in df.columns:
        return
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    scatter = ax.scatter(
        df["longitude"], df["latitude"],
        c=df["cluster"], cmap="Set2", s=50, alpha=0.7, edgecolors="white", linewidth=0.5,
    )
    
    ax.set_title(f"EV Charging Station Clusters ({result['model']})", fontsize=14, fontweight="bold")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    plt.colorbar(scatter, label="Cluster ID")
    
    # Plot centers if available
    if "centers" in result:
        for center in result["centers"]:
            ax.plot(center.get("longitude", 0), center.get("latitude", 0), 
                    "r*", markersize=15, markeredgecolor="black")
    
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, "station_clusters.png"), dpi=150)
    plt.close()
    print(f"  📈 Saved: station_clusters.png")


def plot_elbow(result: dict, save_dir: str):
    """Plot the elbow curve for K selection."""
    os.makedirs(save_dir, exist_ok=True)
    
    if "elbow_data" not in result:
        return
    
    data = result["elbow_data"]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    ax1.plot(data["k"], data["inertia"], "bo-", linewidth=2)
    ax1.set_title("Elbow Method", fontsize=13, fontweight="bold")
    ax1.set_xlabel("Number of Clusters (K)")
    ax1.set_ylabel("Inertia")
    
    ax2.plot(data["k"], data["silhouette"], "go-", linewidth=2)
    best_idx = np.argmax(data["silhouette"])
    ax2.axvline(data["k"][best_idx], color="red", linestyle="--", label=f"Best K={data['k'][best_idx]}")
    ax2.set_title("Silhouette Score", fontsize=13, fontweight="bold")
    ax2.set_xlabel("Number of Clusters (K)")
    ax2.set_ylabel("Silhouette Score")
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, "cluster_selection.png"), dpi=150)
    plt.close()
    print(f"  📊 Saved: cluster_selection.png")


# ──────────────────────────────────────────────────────
#  MAIN PIPELINE
# ──────────────────────────────────────────────────────

def run_clustering_pipeline():
    """Complete Phase 2 pipeline."""
    print("=" * 60)
    print("  PHASE 2: GEOSPATIAL OPTIMIZATION PIPELINE")
    print("=" * 60)
    
    # 1. Load station data
    try:
        processed_path = os.path.join(PROCESSED_DIR, "stations_processed.csv")
        if os.path.exists(processed_path):
            df = pd.read_csv(processed_path)
            print(f"  📂 Loaded processed data: {len(df)} rows")
        else:
            df = load_stations()
            df = process_stations(df)
    except FileNotFoundError as e:
        print(f"\n  ❌ {e}")
        return None
    
    # 2. Add density feature
    df = add_station_density(df)
    
    # 3. Run clustering
    all_results = {}
    
    print("\n" + "─" * 50)
    print("  MODEL: K-Means")
    print("─" * 50)
    kmeans_result = run_kmeans(df)
    if kmeans_result:
        all_results["kmeans"] = kmeans_result
    
    print("\n" + "─" * 50)
    print("  MODEL: DBSCAN")
    print("─" * 50)
    dbscan_result = run_dbscan(df)
    if dbscan_result:
        all_results["dbscan"] = dbscan_result
    
    # 4. White space analysis
    print("\n" + "─" * 50)
    print("  WHITE SPACE ANALYSIS")
    print("─" * 50)
    try:
        sales_path = os.path.join(PROCESSED_DIR, "ev_sales_processed.csv")
        if os.path.exists(sales_path):
            sales_df = pd.read_csv(sales_path)
            find_white_spaces(df, sales_df)
    except Exception:
        find_white_spaces(df)
    
    # 5. Save & visualize
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Save results (without DataFrames)
    save_results = {}
    for name, res in all_results.items():
        save_results[name] = {k: v for k, v in res.items() if k != "clustered_data"}
    
    with open(os.path.join(RESULTS_DIR, "clustering_results.json"), "w") as f:
        json.dump(save_results, f, indent=2, default=str)
    
    if kmeans_result:
        plot_clusters(kmeans_result, RESULTS_DIR)
        plot_elbow(kmeans_result, RESULTS_DIR)
    
    print("\n" + "=" * 60)
    print("  PHASE 2 COMPLETE")
    print("=" * 60)
    
    return all_results


if __name__ == "__main__":
    run_clustering_pipeline()
