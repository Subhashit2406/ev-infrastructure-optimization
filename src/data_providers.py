
import requests
import pandas as pd
import numpy as np
from .data_loader import DataLoader
from typing import Optional
import time
from datetime import datetime, timedelta

class OpenChargeMapLoader(DataLoader):
    """
    Loads real EV station data from OpenChargeMap API.
    Ref: https://openchargemap.org/site/develop/api
    """
    
    BASE_URL = "https://api.openchargemap.io/v3/poi"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        # Default to India ID = 103 if no country specified, but we'll use 'IN' iso code usually
        self.country_code = 'IN' 

    def load_stations(self) -> pd.DataFrame:
        params = {
            'output': 'json',
            'countrycode': self.country_code,
            'maxresults': 500,  # Cap to avoid overload vs finding all
            'compact': True,
            'verbose': False
        }
        if self.api_key:
            params['key'] = self.api_key
            
        print(f"Fetching data from OpenChargeMap for {self.country_code}...")
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            stations = []
            for item in data:
                addr = item.get('AddressInfo', {})
                # Extract relevant fields
                station = {
                    'station_id': str(item.get('ID', 'UNKNOWN')),
                    'name': addr.get('Title', 'Unknown Station'),
                    'operator': item.get('OperatorInfo', {}).get('Title', 'Unknown Operator'),
                    'city': addr.get('Town', 'Unknown City'),
                    'state': addr.get('StateOrProvince', 'Unknown State'),
                    'latitude': addr.get('Latitude'),
                    'longitude': addr.get('Longitude'),
                    'power_kw': self._extract_power(item),
                    'status': item.get('StatusType', {}).get('Title', 'Unknown'),
                    'source': 'OpenChargeMap (Real)'
                }
                stations.append(station)
                
            df = pd.DataFrame(stations)
            # Fill missing power with a reasonable default for analysis if missing
            df['power_kw'] = df['power_kw'].fillna(22.0) 
            return df
            
        except Exception as e:
            print(f"⚠️ Error fetching OpenChargeMap data: {e}")
            print("Falling back to Synthetic Loader...")
            return SyntheticLoader().load_stations()

    def _extract_power(self, item):
        """Helper to get max power from connections list"""
        conns = item.get('Connections', [])
        if not conns:
            return None
        # Return max power found in any connection
        powers = [c.get('PowerKW') for c in conns if c.get('PowerKW') is not None]
        return max(powers) if powers else None

    def load_sessions(self, stations_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        OpenChargeMap doesn't provide session/usage data (privacy).
        We MUST generate synthetic sessions based on the REAL stations.
        """
        print("ℹ️ Generating realistic synthetic sessions for Real Stations...")
        return SyntheticLoader().load_sessions(stations_df)


class SyntheticLoader(DataLoader):
    """
    Generates high-quality synthetic data using REAL city coordinates.
    Used as fallback or for simulation.
    """
    
    # Real coordinates for major Indian EV hubs
    CITIES = {
        'New Delhi': (28.6139, 77.2090),
        'Mumbai': (19.0760, 72.8777),
        'Bangalore': (12.9716, 77.5946),
        'Chennai': (13.0827, 80.2707),
        'Hyderabad': (17.3850, 78.4867),
        'Pune': (18.5204, 73.8567),
        'Ahmedabad': (23.0225, 72.5714),
        'Kolkata': (22.5726, 88.3639)
    }
    
    OPERATORS = ['TATA Power', 'Ather', 'Statiq', 'ChargePoint', 'Zeon Charging']

    def load_stations(self) -> pd.DataFrame:
        print("Generating Synthetic Stations...")
        stations = []
        count = 0
        for city, (lat, lon) in self.CITIES.items():
            # Generate 5-10 stations per city
            n_stations = np.random.randint(5, 10)
            for _ in range(n_stations):
                count += 1
                # Gaussian noise for location spread (approx 5-10km radius)
                s_lat = lat + np.random.normal(0, 0.05)
                s_lon = lon + np.random.normal(0, 0.05)
                
                stations.append({
                    'station_id': f'SYN_{count:04d}',
                    'name': f"{np.random.choice(self.OPERATORS)} - {city} #{np.random.randint(1, 99)}",
                    'operator': np.random.choice(self.OPERATORS),
                    'city': city,
                    'state': 'India', # Simplified
                    'latitude': s_lat,
                    'longitude': s_lon,
                    'power_kw': np.random.choice([7.2, 11, 22, 50, 60, 150], p=[0.2, 0.2, 0.3, 0.2, 0.05, 0.05]),
                    'status': 'Operational',
                    'source': 'Synthetic (Realistic)'
                })
        return pd.DataFrame(stations)

    def load_sessions(self, stations_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        if stations_df is None:
            raise ValueError("Stations DataFrame required to generate sessions.")
            
        print(f"Generating Synthetic Sessions for {len(stations_df)} stations...")
        sessions = []
        
        # Simulation parameters
        start_date = datetime.now() - timedelta(days=90)
        
        for _, station in stations_df.iterrows():
            # Base Demand
            daily_sessions_base = np.random.poisson(3 if station['power_kw'] > 40 else 1.5)
            
            for day in range(90):
                current_day = start_date + timedelta(days=day)
                
                # INFRASTRUCTURE GROWTH FACTOR
                # EV adoption is growing! Demand increases over time.
                # Factor: 0.8 at start -> 1.2 at end (50% growth over 90 days)
                growth_factor = 0.8 + (0.4 * (day / 90))
                
                # Seasonality: varied by week
                seasonality = 1.0 + (0.2 * np.sin(day / 7))
                
                scaled_rate = daily_sessions_base * growth_factor * seasonality
                n_sessions = np.random.poisson(scaled_rate)
                
                for _ in range(n_sessions):
                    # Peak hours preference (morning 9-11, evening 17-20)
                    hour_prob = [0.02]*6 + [0.05]*3 + [0.1]*3 + [0.05]*5 + [0.1]*4 + [0.03]*3
                    hour_prob = np.array(hour_prob) / sum(hour_prob)
                    hour = np.random.choice(range(24), p=hour_prob)
                    
                    session_start = current_day.replace(hour=hour, minute=np.random.randint(0, 60))
                    
                    # Duration depends on charger speed primarily
                    if station['power_kw'] >= 50:
                        duration_mins = np.random.normal(40, 10) # Fast charging
                    else:
                        duration_mins = np.random.normal(120, 30) # Slow charging
                    
                    duration_mins = max(10, duration_mins) # Min 10 mins
                    
                    energy = (station['power_kw'] * 0.8) * (duration_mins / 60) # 80% efficiency avg
                    
                    sessions.append({
                        'session_id': f"SES_{len(sessions):06d}",
                        'station_id': station['station_id'],
                        'session_start': session_start,
                        'session_end': session_start + timedelta(minutes=duration_mins),
                        'duration_minutes': round(duration_mins, 1),
                        'energy_delivered_kwh': round(energy, 2),
                        'cost_inr': round(energy * np.random.uniform(12, 18), 2), # 12-18 INR per unit
                        'vehicle_type': np.random.choice(['2W', '4W', 'Commercial'], p=[0.3, 0.6, 0.1])
                    })
                    
        return pd.DataFrame(sessions)

    def load_demand_hotspots(self) -> pd.DataFrame:
        """
        Generates potential demand centers (Residential, Commercial, Highways).
        Used for Gap Analysis.
        """
        print("Generating Demand Hotspots...")
        hotspots = []
        
        for city, (lat, lon) in self.CITIES.items():
            # Residential clusters (High density, night charging)
            n_res = np.random.randint(20, 40)
            for _ in range(n_res):
                # Spread out more than stations
                h_lat = lat + np.random.normal(0, 0.08) 
                h_lon = lon + np.random.normal(0, 0.08)
                hotspots.append({
                    'city': city,
                    'latitude': h_lat,
                    'longitude': h_lon,
                    'type': 'Residential',
                    'demand_score': np.random.randint(1, 10)
                })
                
            # Commercial clusters (City center, day charging)
            n_com = np.random.randint(10, 20)
            for _ in range(n_com):
                h_lat = lat + np.random.normal(0, 0.03) 
                h_lon = lon + np.random.normal(0, 0.03)
                hotspots.append({
                    'city': city,
                    'latitude': h_lat,
                    'longitude': h_lon,
                    'type': 'Commercial',
                    'demand_score': np.random.randint(5, 10) # Higher intensity
                })
                
        return pd.DataFrame(hotspots)
