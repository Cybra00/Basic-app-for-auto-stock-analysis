# src/loader.py
import pandas as pd

REQUIRED_COLUMNS = ["Date", "Open", "High", "Low", "Close", "Volume"]

def load_stock_data(file):
    df = pd.read_csv(file)

    # Normalize column names
    df.columns = [c.strip().title() for c in df.columns]

    # Schema validation
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing columns: {missing}")

    # Data cleaning
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)

    return df
