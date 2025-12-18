import numpy as np
import pandas as pd
from datetime import datetime, timedelta


class Utils:

    def get_ax_by_label(fig, target_label):
        """
        Finds and returns the Axes object within a Figure that has a specific x or y label.
        """
        for ax in fig.axes:
            # Check x-axis label
            if ax.get_xlabel() == target_label:
                return ax
            # Check y-axis label
            if ax.get_ylabel() == target_label:
                return ax
        return None 
    
    def busday_diff(start, end):
        """Calculate business days between two dates using NumPy."""
        # Convert to date if datetime object (removes time component)
        if isinstance(start, datetime):
            start = start.date()
        if isinstance(end, datetime):
            end = end.date()
        return np.busday_count(start, end)


    def calculate_sma(data, period):
        """
        Calculate Simple Moving Average (SMA).
        
        Parameters:
        - data: pandas Series or DataFrame column with price data
        - period: lookback period for SMA calculation
        
        Returns:
        - pandas Series with SMA values
        """
        return data.rolling(window=period).mean()

    
    def calculate_rsi(data, period=14):
        """
        Calculate the Relative Strength Index (RSI) for a given dataset.
        
        Parameters:
        - data: pandas Series or DataFrame column with price data
        - period: lookback period for RSI calculation (default: 14)
        
        Returns:
        - pandas Series with RSI values
        """
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        
        avg_gain = gain.ewm(com=period-1, min_periods=period).mean()
        avg_loss = loss.ewm(com=period-1, min_periods=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi


    def calculate_macd(data, fast=12, slow=26, signal=9):
        """
        Calculate MACD (Moving Average Convergence Divergence) indicator.
        
        Parameters:
        - data: pandas Series or DataFrame column with price data
        - fast: fast EMA period (default: 12)
        - slow: slow EMA period (default: 26)
        - signal: signal line EMA period (default: 9)
        
        Returns:
        - tuple: (macd_line, signal_line, histogram)
        """
        ema_fast = data.ewm(span=fast, adjust=False).mean()
        ema_slow = data.ewm(span=slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram




