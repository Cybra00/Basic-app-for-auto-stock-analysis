import sys
import os
import pandas as pd
import numpy as np

# Ensure we can import from src
sys.path.append(os.getcwd())

try:
    from src.charts import candlestick_chart
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

# Create dummy data
dates = pd.date_range(start="2023-01-01", periods=10)
df = pd.DataFrame({
    "Date": dates,
    "Open": np.random.rand(10) * 100 + 100,
    "High": np.random.rand(10) * 10 + 110,
    "Low": np.random.rand(10) * 10 + 90,
    "Close": np.random.rand(10) * 100 + 100,
    "Volume": np.random.randint(100, 1000, 10),
    "MA50": np.random.rand(10) * 100 + 100,
    "Volume_Breakout": [False, False, True, False, False, True, False, False, False, False] # Simulate breakouts
})

print("Testing candlestick_chart...")
try:
    fig = candlestick_chart(df)
    print("Chart created successfully.")
    
    # Check if annotation exists
    found = False
    for annotation in fig.layout.annotations:
        if annotation.text == "Price Action with Moving Averages":
            found = True
            break
    
    if not found:
        print("Warning: Annotation 'Price Action with Moving Averages' not found in layout.")

    # --- Verify Enhancements ---
    # 1. Range Selector
    if fig.layout.xaxis.rangeselector:
        print("✅ Range Selector found.")
    else:
        print("❌ Range Selector NOT found.")

    # 2. Breakout Highlights (Shapes)
    vrect_count = len([s for s in fig.layout.shapes if s.type == "rect" and s.fillcolor == "yellow"])
    if vrect_count > 0:
        print(f"✅ Breakout Highlights found: {vrect_count} vrects.")
    else:
        print("❌ Breakout Highlights NOT found (Expected yellow vrects).")
    
except Exception as e:
    print(f"Error creating chart: {e}")
    # Print full traceback
    import traceback
    traceback.print_exc()
    sys.exit(1)
