# src/loader.py
import pandas as pd
import yfinance as yf

REQUIRED_COLUMNS = ["Date", "Open", "High", "Low", "Close", "Volume"]

def fetch_live_data(ticker, period="1mo", interval="1d"):
    """
    Fetch live stock data using yfinance.
    """
    try:
        # Download data
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        
        # Reset index to make Date a column
        df = df.reset_index()
        
        # Ensure column names are clean (Vectorized DataFrame from yf often has multi-index)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # Rename columns to match expected schema
        # yfinance columns are usually: Date, Open, High, Low, Close, Adj Close, Volume
        # We need to map them correctly and ensure proper case
        # Note: yfinance output is already Title Case usually, but let's be safe
        
        # Normalize: keep only required columns
        valid_cols = ["Date", "Open", "High", "Low", "Close", "Volume"]
        df = df[valid_cols].copy()
        
        return df
        
    except Exception as e:
        raise ValueError(f"Failed to fetch data for {ticker}: {str(e)}")

def load_stock_data(file):
    df = pd.read_csv(file)

    # Normalize column names
    df.columns = [c.strip().title() for c in df.columns]

    # Schema validation
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing columns: {missing}")

    # Data cleaning & Type Enforcement
    df["Date"] = pd.to_datetime(df["Date"])
    
    # Force numeric columns to be floats, coercing errors to NaN
    numeric_cols = ["Open", "High", "Low", "Close", "Volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    # Sort and reset
    df = df.sort_values("Date").reset_index(drop=True)
    
    if df.empty:
        raise ValueError("CSV contains no valid stock data after cleaning.")

    return df
