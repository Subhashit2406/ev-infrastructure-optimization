
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from datetime import datetime

class DataPreprocessor:
    """
    Handles cleaning, merging, and feature engineering for EV data.
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        
    def preprocess(self, stations: pd.DataFrame, sessions: pd.DataFrame) -> pd.DataFrame:
        """
        Main pipeline: Clean -> Merge -> Feature Engineer
        """
        print("⚙️ Starting Data Preprocessing...")
        
        # 1. Clean Data
        stations = self._clean_stations(stations)
        sessions = self._clean_sessions(sessions)
        
        # 2. Merge
        merged = pd.merge(sessions, stations, on='station_id', how='left')
        print(f"   Merged data shape: {merged.shape}")
        
        # 3. Feature Engineering
        processed = self._engineer_features(merged)
        
        return processed

    def _clean_stations(self, df: pd.DataFrame) -> pd.DataFrame:
        # Fill missing numeric values with median
        numeric_cols = ['power_kw', 'latitude', 'longitude']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].fillna(df[col].median())
        return df

    def _clean_sessions(self, df: pd.DataFrame) -> pd.DataFrame:
        # Convert timestamps
        df['session_start'] = pd.to_datetime(df['session_start'])
        df['session_end'] = pd.to_datetime(df['session_end'])
        
        # Remove negative durations/energy
        df = df[df['duration_minutes'] > 0]
        df = df[df['energy_delivered_kwh'] > 0]
        return df

    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        # Temporal Features
        df['hour'] = df['session_start'].dt.hour
        df['day_of_week'] = df['session_start'].dt.dayofweek
        df['month'] = df['session_start'].dt.month
        df['is_weekend'] = df['day_of_week'].apply(lambda x: 1 if x >= 5 else 0)
        
        # Interaction Features
        # Utilization Rate (Energy / (Power * Duration))
        # Note: Duration is in minutes, so convert to hours
        df['utilization_factor'] = df['energy_delivered_kwh'] / (df['power_kw'] * (df['duration_minutes'] / 60))
        df['utilization_factor'] = df['utilization_factor'].clip(0, 1) # Cap at 100%
        
        # Station Busy Score (Proxy)
        # Count sessions per station in the last 24h window (Rolling window would be better but complex for this stage)
        station_counts = df.groupby('station_id')['session_id'].transform('count')
        df['station_popularity'] = station_counts
        
        return df
