
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import xgboost as xgb
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
except Exception:
    PROPHET_AVAILABLE = False # Catch other init errors like stan_backend

import matplotlib.pyplot as plt
import seaborn as sns
import io
from datetime import timedelta

class StationClusterer:
    """
    Gap Analysis Engine: Finds underserved high-demand zones.
    """
    def __init__(self, n_new_stations=5, coverage_radius_km=5.0):
        self.n_new_stations = n_new_stations
        self.coverage_radius_km = coverage_radius_km
        self.model = KMeans(n_clusters=n_new_stations, random_state=42, n_init=10)
        
    def find_gaps(self, existing_stations, demand_hotspots):
        """
        Identifies demand points that are outside the coverage radius of any existing station.
        """
        # Convert lat/lon to radians for distance calculation
        stations_rad = np.radians(existing_stations[['latitude', 'longitude']].values)
        demand_rad = np.radians(demand_hotspots[['latitude', 'longitude']].values)
        
        # Calculate distance matrix (using Haversine approx via sklearn if needed, but manual for now)
        # Simplified: Filter points that are far from ALL stations
        underserved_points = []
        
        # This is a simple O(N*M) check, acceptable for small datasets (<10k points)
        # For production: Use BallTree or KDTree
        from sklearn.neighbors import BallTree
        
        tree = BallTree(stations_rad, metric='haversine')
        
        # Query radius (radius / earth_radius_km)
        earth_radius_km = 6371.0
        radius_rad = self.coverage_radius_km / earth_radius_km
        
        # query_radius returns array of arrays of indices
        counts = tree.query_radius(demand_rad, r=radius_rad, count_only=True)
        
        # Points with 0 stations nearby are "Gaps"
        gap_mask = counts == 0
        self.gap_points = demand_hotspots[gap_mask].copy()
        
        return self.gap_points
        
    def recommend_locations(self):
        """Classes underserved points to find best new locations"""
        if not hasattr(self, 'gap_points') or self.gap_points.empty:
            return pd.DataFrame(columns=['latitude', 'longitude', 'priority_score'])
            
        coords = self.gap_points[['latitude', 'longitude']]
        
        # If fewer gaps than requested stations, just return gaps
        n_clusters = min(self.n_new_stations, len(coords))
        if n_clusters == 0:
             return pd.DataFrame(columns=['latitude', 'longitude', 'priority_score'])
             
        self.model.n_clusters = n_clusters
        self.gap_points['cluster'] = self.model.fit_predict(coords)
        
        # Calculate centers
        centers = self.model.cluster_centers_
        
        # Calculate priority (sum of demand scores in cluster)
        cluster_scores = self.gap_points.groupby('cluster')['demand_score'].sum()
        
        recommendations = pd.DataFrame(centers, columns=['latitude', 'longitude'])
        recommendations['priority_score'] = cluster_scores.values if len(cluster_scores) == len(centers) else 0
        recommendations = recommendations.sort_values('priority_score', ascending=False)
        
        return recommendations

class DemandForecaster:
    """
    Predicts energy demand using XGBoost.
    """
    def __init__(self):
        self.model = xgb.XGBRegressor(
            objective='reg:squarederror',
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        self.feature_cols = [
            'hour', 'day_of_week', 'month', 'is_weekend', 
            'power_kw', 'latitude', 'longitude'
        ]
        
    def fit(self, df):
        # Prepare data
        X = df[self.feature_cols]
        y = df['energy_delivered_kwh']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        preds = self.model.predict(X_test)
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        r2 = r2_score(y_test, preds)
        
        return {'rmse': rmse, 'r2': r2}
        
    def predict(self, input_data):
        return self.model.predict(input_data[self.feature_cols])

class TimeSeriesForecaster:
    """
    Forecasts aggregated demand using Facebook Prophet (with fallback).
    """
    def __init__(self):
        self.prohet_available = PROPHET_AVAILABLE
        if self.prohet_available:
            try:
                self.model = Prophet(yearly_seasonality=True, weekly_seasonality=True)
            except:
                self.prohet_available = False
                print("⚠️ Prophet init failed, using fallback.")
        
    def fit_predict(self, df, periods=365):
        # Aggregate daily demand
        daily_demand = df.groupby(df['session_start'].dt.date)['energy_delivered_kwh'].sum().reset_index()
        daily_demand.columns = ['ds', 'y']
        
        if self.prohet_available:
            try:
                self.model.fit(daily_demand)
                future = self.model.make_future_dataframe(periods=periods)
                forecast = self.model.predict(future)
                return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
            except Exception as e:
                print(f"⚠️ Prophet failed during fit/predict: {e}")
                return self._fallback_forecast(daily_demand, periods)
        else:
            return self._fallback_forecast(daily_demand, periods)

    def _fallback_forecast(self, daily_demand, periods):
        """Simple Moving Average Fallback"""
        print("ℹ️ Using Moving Average Fallback for Forecasting")
        df = daily_demand.copy()
        df['ds'] = pd.to_datetime(df['ds'])
        
        # Calculate trend
        df['yhat'] = df['y'].rolling(window=7, min_periods=1).mean()
        last_val = df['yhat'].iloc[-1]
        
        # Generate future dates
        last_date = df['ds'].iloc[-1]
        future_dates = [last_date + timedelta(days=x) for x in range(1, periods + 1)]
        
        future_df = pd.DataFrame({
            'ds': future_dates,
            'yhat': [last_val] * periods,
            'yhat_lower': [last_val * 0.8] * periods,
            'yhat_upper': [last_val * 1.2] * periods
        })
        
        # Combine history and future
        forecast = pd.concat([
            df[['ds', 'yhat']].assign(yhat_lower=df['yhat']*0.9, yhat_upper=df['yhat']*1.1), 
            future_df
        ])
        return forecast
