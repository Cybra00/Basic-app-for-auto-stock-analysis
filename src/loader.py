# src/loader.py
import pandas as pd
import yfinance as yf

REQUIRED_COLUMNS = ["Date", "Open", "High", "Low", "Close", "Volume"]

def fetch_live_data(ticker, period="1mo", interval="1d"):
    """
    Fetch live stock data using yfinance.
    """
    try:
        # Validate constraints for yfinance to prevent "No data found" errors
        # Intraday data availability limits:
        # 1m = 7 days
        # 2m, 5m, 15m, 30m, 90m = 60 days
        # 1h = 730 days (approx 2 years)
        
        warning_msg = None
        original_period = period
        
        if interval == "1m":
            if period in ["1mo", "3mo", "1y", "max"]:
                period = "7d"
                warning_msg = f"⚠️ Limit reached: 1m data is restricted to last 7 days. Adjusted '{original_period}' to '7d'."
        elif interval in ["2m", "5m", "15m", "30m", "90m"]:
            if period in ["3mo", "1y", "max"]:
                period = "60d"
                warning_msg = f"⚠️ Limit reached: {interval} data is restricted to last 60 days. Adjusted '{original_period}' to '60d'."
        elif interval == "1h":
             if period == "max":
                 period = "2y"
                 warning_msg = f"⚠️ Limit reached: 1h data is restricted to last 730 days. Adjusted '{original_period}' to '2y'."
        
        # Download data
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        
        if df.empty:
            return df, None # Return empty to let app handle it with "No data found"

        # Reset index to make Date a column
        df = df.reset_index()
        
        # Ensure column names are clean (Vectorized DataFrame from yf often has multi-index)
        if isinstance(df.columns, pd.MultiIndex):
            try:
                # Try to drop the ticker level if it exists
                df.columns = df.columns.droplevel(1) 
            except:
                # Fallback to get level 0 
                df.columns = df.columns.get_level_values(0)
            
        # Rename columns to match expected schema
        # yfinance columns are usually: Date, Open, High, Low, Close, Adj Close, Volume
        # We need to map them correctly and ensure proper case
        # Note: yfinance output is already Title Case usually, but let's be safe
        
        # Normalize: keep only required columns
        valid_cols = ["Date", "Open", "High", "Low", "Close", "Volume"]
        
        # Check if we have the columns we need
        available_cols = [c for c in valid_cols if c in df.columns]
        if len(available_cols) < len(valid_cols):
             # Try checking if columns are lower case
             df.columns = [c.capitalize() for c in df.columns]
        
        # Final check
        if not all(col in df.columns for col in valid_cols):
             return pd.DataFrame(), None # Return empty if schema mismatch

        df = df[valid_cols].copy()
        
        return df, warning_msg
        
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
