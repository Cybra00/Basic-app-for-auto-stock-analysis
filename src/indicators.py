# src/indicators.py
def add_indicators(df):
    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA50"] = df["Close"].rolling(50).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    
    # Prevent division by zero: if avg_loss is zero, RSI should be 100 (all gains)
    rs = avg_gain / avg_loss.replace(0, 1)  # Replace 0 with 1 to avoid division by zero
    df["RSI"] = 100 - (100 / (1 + rs))
    
    # Set RSI to 100 when avg_loss is zero (all gains, no losses)
    df.loc[avg_loss == 0, "RSI"] = 100.0
    # --- Volume & Trend Indicators ---
    
    # 1. Volume Moving Average (20)
    df["Volume_MA20"] = df["Volume"].rolling(20).mean()
    
    # 2. On-Balance Volume (OBV)
    # OBV = Cumulative sum of volume * direction (1 if close > prev_close, -1 if less, 0 if equal)
    # Using pandas apply/diff logic or numpy where
    # Note: First row of diff is NaN, fill with 0
    change = df["Close"].diff()
    direction = change.apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    df["OBV"] = (direction * df["Volume"]).cumsum()
    
    # 3. VWAP (Volume Weighted Average Price)
    # Typical Price = (High + Low + Close) / 3
    # VWAP = Cumulative(Typical Price * Volume) / Cumulative(Volume)
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
    df["VWAP"] = (typical_price * df["Volume"]).cumsum() / df["Volume"].cumsum()
    
    # 4. Volume Breakout Detection
    # Trader Standard: Volume > 3x Average AND Price Change > 0.5% (avoid churn)
    pct_change = df["Close"].pct_change().abs()
    df["Volume_Breakout"] = (df["Volume"] > (3.0 * df["Volume_MA20"])) & (pct_change > 0.005)
    
    # 5. Price-Volume Confirmation Signal
    # Bullish: Price Up + Volume Up
    # Bearish: Price Down + Volume Up (Selling pressure)
    vol_change = df["Volume"].diff()
    
    conditions = [
        (change > 0) & (vol_change > 0),
        (change < 0) & (vol_change > 0)
    ]
    choices = ["Bullish Confirmation", "Bearish Selling Pressure"]
    
    # We need numpy for 'select', but let's stick to pandas apply if we want to avoid extra imports if possible,
    # or just add 'import numpy as np' at top if not present. 
    # Actually, simpler to just start with empty and fill.
    df["Trend_Signal"] = "Neutral"
    df.loc[(change > 0) & (vol_change > 0), "Trend_Signal"] = "Bullish Confirmation"
    df.loc[(change < 0) & (vol_change > 0), "Trend_Signal"] = "Bearish Selling Pressure"

    return df
