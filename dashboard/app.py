import streamlit as st

from src.loader import load_stock_data
from src.kpis import compute_kpis
from src.indicators import add_indicators
from src.charts import candlestick_chart, volume_chart, close_trend

st.set_page_config(page_title="Stock Auto Analysis", layout="wide")

st.title("📈 Stock KPI Auto-Analysis Dashboard")

# --- CSV Upload ---
uploaded_file = st.sidebar.file_uploader(
    "Upload Stock OHLCV CSV",
    type=["csv"]
)

if uploaded_file is None:
    st.warning("Please upload a stock CSV file to begin analysis.")
    st.stop()

# --- Load & Validate ---
try:
    df = load_stock_data(uploaded_file)
except Exception as e:
    st.error(str(e))
    st.stop()

# --- Auto Analysis Pipeline ---
df = add_indicators(df)
kpis = compute_kpis(df)

# --- KPI Cards ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Latest Price", f"₹{kpis['latest_price']:.2f}")
col2.metric("Daily Return", f"{kpis['daily_return_pct']:.2f}%")
col3.metric("52W High", f"₹{kpis['high_52w']:.2f}")
col4.metric("Volatility", f"{kpis['volatility_pct']:.2f}%")

# --- Charts ---
st.plotly_chart(candlestick_chart(df), use_container_width=True)
st.plotly_chart(close_trend(df), use_container_width=True)
st.plotly_chart(volume_chart(df), use_container_width=True)

# --- Insight ---
st.subheader("📌 Auto Insight")
if kpis["daily_return_pct"] > 0 and df["Volume"].iloc[-1] > kpis["avg_volume"]:
    st.success("Bullish move supported by strong volume.")
elif kpis["daily_return_pct"] < 0:
    st.warning("Stock closed lower – short-term weakness.")
else:
    st.info("Stock is consolidating.")
