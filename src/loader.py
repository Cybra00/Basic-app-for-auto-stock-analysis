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
            if period in ["1mo", "3mo", "1y", "max", "7d"]: # added 7d as it can be flaky
                period = "5d" # 5d is more reliable for 1m data than 7d
                warning_msg = f"⚠️ Limit reached: 1m data is restricted to last 5 days (stable). Adjusted '{original_period}' to '5d'."
        elif interval in ["2m", "5m", "15m", "30m", "90m"]:
            if period in ["3mo", "1y", "max"]:
                period = "60d"
                warning_msg = f"⚠️ Limit reached: {interval} data is restricted to last 60 days. Adjusted '{original_period}' to '60d'."
        elif interval == "1h":
             if period == "max":
                 period = "2y"
                 warning_msg = f"⚠️ Limit reached: 1h data is restricted to last 730 days. Adjusted '{original_period}' to '2y'."
        
        # Download data using Ticker.history which is more reliable for single tickers and granular intervals
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(period=period, interval=interval)
        
        # Fallback logic for 1m data
        if df.empty and interval == "1m" and period != "1d":
             fallback_period = "1d"
             df = ticker_obj.history(period=fallback_period, interval=interval)
             if not df.empty:
                 if warning_msg:
                     warning_msg += f" (Note: Adjusted period returned no data, fell back to '{fallback_period}' which worked.)"
                 else:
                     warning_msg = f"⚠️ Request for '{period}' returned no data. Automatically fell back to '{fallback_period}'."

        if df.empty:
            return df, None, {} # Return empty to let app handle it with "No data found"

        # Try to get previous close from fast_info
        previous_close = None
        try:
            previous_close = ticker_obj.fast_info.previous_close
        except:
            pass # Fail silently if not available
            
        metadata = {"previous_close": previous_close}

        # Reset index to make Date a column
        df = df.reset_index()
        
        # Ticker.history returns clean columns (Open, High, Low, Close, Volume, Dividends, Stock Splits)
        # No MultiIndex processing needed usually.
        
        # Standardize Date column name (yfinance returns 'Datetime' for intraday, 'Date' for daily)
        if "Datetime" in df.columns:
            df = df.rename(columns={"Datetime": "Date"})
            
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
             return pd.DataFrame(), None, {} # Return empty if schema mismatch

        df = df[valid_cols].copy()
        
        return df, warning_msg, metadata
        
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

    return df, {}, {} # Return empty metadata for consistency (extra dict for future use)
