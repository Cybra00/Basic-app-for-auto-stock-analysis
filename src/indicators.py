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

    return df
