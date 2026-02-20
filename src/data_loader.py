
from abc import ABC, abstractmethod
import pandas as pd
from typing import Tuple, Optional

class DataLoader(ABC):
    """
    Abstract base class for loading EV infrastructure data.
    Enforces a consistent interface for both Real (OpenChargeMap) and Synthetic data sources.
    """

    @abstractmethod
    def load_stations(self) -> pd.DataFrame:
        """
        Load charging stations data.
        
        Returns:
            pd.DataFrame: A DataFrame containing station information.
            Must include at least: ['station_id', 'latitude', 'longitude', 'power_kw']
        """
        pass

    @abstractmethod
    def load_sessions(self, stations_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Load or generate charging sessions data.
        
        Args:
            stations_df (pd.DataFrame, optional): Stations DataFrame to link sessions to.
                                                  Required for synthetic generation.
        
        Returns:
            pd.DataFrame: A DataFrame containing session logs.
            Must include: ['session_id', 'station_id', 'energy_delivered_kwh', 'start_time']
        """
        pass
    
    def validate_schema(self, df: pd.DataFrame, required_columns: list) -> bool:
        """
        Helper to validate that loaded data contains necessary columns.
        """
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Data missing required columns: {missing}")
        return True
