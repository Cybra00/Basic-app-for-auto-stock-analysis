# src/kpis.py
import pandas as pd
import numpy as np

def compute_kpis(df):
    """
    Compute key performance indicators from stock data.
    
    Returns a dictionary with:
    - latest_price: Last closing price
    - daily_return_pct: Percentage change from previous day
    - high_52w: Maximum high price in last 52 weeks (~252 trading days)
    - volatility_pct: Standard deviation of daily returns as percentage
    - avg_volume: Average trading volume
    """
    # Latest price (last Close value)
    latest_price = df["Close"].iloc[-1]
    
    # Daily return percentage (change from previous day)
    if len(df) > 1:
        daily_return_pct = ((df["Close"].iloc[-1] - df["Close"].iloc[-2]) / df["Close"].iloc[-2]) * 100
    else:
        daily_return_pct = 0.0
    
    # 52-week high (maximum High in last ~252 trading days)
    lookback_days = min(252, len(df))
    high_52w = df["High"].tail(lookback_days).max()
    
    # Volatility (standard deviation of daily returns as percentage)
    if len(df) > 1:
        daily_returns = df["Close"].pct_change().dropna()
        volatility_pct = daily_returns.std() * 100
    else:
        volatility_pct = 0.0
    
    # Average volume
    avg_volume = df["Volume"].mean()
    
    return {
        "latest_price": latest_price,
        "daily_return_pct": daily_return_pct,
        "high_52w": high_52w,
        "volatility_pct": volatility_pct,
        "avg_volume": avg_volume
    }

