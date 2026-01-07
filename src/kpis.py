# src/kpis.py
import pandas as pd
import numpy as np

def compute_kpis(df, metadata=None):
    """
    Compute key performance indicators from stock data.
    
    Args:
        df: DataFrame with stock data
        metadata: Optional dictionary containing 'previous_close'
    """
    if df.empty:
        return {
            "latest_price": 0.0,
            "daily_return_pct": 0.0,
            "high_value": 0.0,
            "high_label": "Period High",
            "volatility_pct": 0.0,
            "avg_volume": 0.0
        }

    # Latest price (last Close value)
    latest_price = df["Close"].iloc[-1]
    
    # Daily return percentage (change from previous day)
    # Priority: 1. Previous Close from API (most accurate for live data)
    #           2. Previous Row Close (if multi-day data)
    #           3. Open Price (fallback for single-day data without API)
    
    daily_return_pct = 0.0
    prev_close = metadata.get("previous_close") if metadata else None
    
    if prev_close and not pd.isna(prev_close):
        daily_return_pct = ((latest_price - prev_close) / prev_close) * 100
    elif len(df) > 1:
        # Check if previous row is actually from a different day? 
        # For simplicity, we assume standard daily bars OR continuous intraday.
        # Ideally we compare dates, but prev row is the standard fallback.
        prev_row_close = df["Close"].iloc[-2]
        daily_return_pct = ((latest_price - prev_row_close) / prev_row_close) * 100
    else:
        # Fallback for single row/day without API data (e.g. fresh CSV)
        # Use Open as the baseline ("Intraday Change")
        open_price = df["Open"].iloc[-1]
        if open_price != 0:
            daily_return_pct = ((latest_price - open_price) / open_price) * 100
    
    # Dynamic High Metric (52W vs Period)
    data_points = len(df)
    
    if data_points >= 200: 
        lookback = min(252, data_points)
        high_value = df["High"].tail(lookback).max()
        high_label = "52W High"
    else:
        high_value = df["High"].max()
        high_label = "Period High"
    
    # Annualized Volatility
    if len(df) > 1:
        daily_returns = df["Close"].pct_change().dropna()
        volatility_pct = daily_returns.std() * np.sqrt(252) * 100
    else:
        volatility_pct = 0.0
    
    # Average volume
    avg_volume = df["Volume"].mean()
    
    return {
        "latest_price": latest_price,
        "daily_return_pct": daily_return_pct,
        "high_value": high_value,
        "high_label": high_label,
        "volatility_pct": volatility_pct,
        "avg_volume": avg_volume
    }

