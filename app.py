import streamlit as st
import pandas as pd

from src.loader import load_stock_data
from src.kpis import compute_kpis
from src.indicators import add_indicators
from src.charts import candlestick_chart, volume_chart, close_trend
from src.patterns import detect_candlestick_patterns, get_pattern_insights, get_pattern_description, PATTERN_DESCRIPTIONS

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
patterns_df = detect_candlestick_patterns(df)

# --- KPI Cards ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Latest Price", f"₹{kpis['latest_price']:.2f}")
col2.metric("Daily Return", f"{kpis['daily_return_pct']:.2f}%")
col3.metric("52W High", f"₹{kpis['high_52w']:.2f}")
col4.metric("Volatility", f"{kpis['volatility_pct']:.2f}%")

# --- Charts ---
st.plotly_chart(candlestick_chart(df, patterns_df), use_container_width=True)
st.plotly_chart(close_trend(df), use_container_width=True)
st.plotly_chart(volume_chart(df), use_container_width=True)

# --- Candlestick Pattern Detection ---
st.subheader("🕯️ Candlestick Pattern Detection & Analysis")

if not patterns_df.empty:
    # Get comprehensive insights
    insights = get_pattern_insights(patterns_df, df)
    
    # Display sentiment summary in columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Bullish Patterns", insights["bullish_count"], delta=None)
    with col2:
        st.metric("Bearish Patterns", insights["bearish_count"], delta=None)
    with col3:
        sentiment_color = "🟢" if "Bullish" in insights["sentiment"] else "🔴" if "Bearish" in insights["sentiment"] else "🟡"
        st.metric("Market Sentiment", f"{sentiment_color} {insights['sentiment']}")
    
    # Display recent patterns table with enhanced formatting
    st.write("### 📊 Recent Detected Patterns")
    display_patterns = patterns_df.tail(15)[["Date", "Pattern", "Type", "Signal", "Price"]].copy()
    display_patterns["Date"] = display_patterns["Date"].dt.strftime("%Y-%m-%d")
    display_patterns["Price"] = display_patterns["Price"].apply(lambda x: f"₹{x:.2f}")
    
    # Style the dataframe
    def color_signal(val):
        if val == "Bullish":
            return 'background-color: #d4edda; color: #155724'
        elif val == "Bearish":
            return 'background-color: #f8d7da; color: #721c24'
        else:
            return 'background-color: #fff3cd; color: #856404'
    
    styled_df = display_patterns.style.applymap(color_signal, subset=['Signal'])
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    # Display comprehensive insights
    st.write("### 🔍 Pattern Analysis & Insights")
    st.markdown(insights["summary"])
    
    # Display pattern frequency
    if insights["pattern_counts"]:
        st.write("#### 📈 Pattern Frequency (Last 20 Patterns)")
        pattern_freq_df = pd.DataFrame(list(insights["pattern_counts"].items()), 
                                      columns=["Pattern", "Count"])
        pattern_freq_df = pattern_freq_df.sort_values("Count", ascending=False)
        st.bar_chart(pattern_freq_df.set_index("Pattern"))
    
    # Display latest pattern details with description
    if insights["latest_pattern"]:
        st.write("### 🎯 Latest Pattern Details")
        latest = insights["latest_pattern"]
        pattern_name = latest["Pattern"]
        pattern_desc = get_pattern_description(pattern_name)
        
        # Create expandable section for pattern description
        with st.expander(f"📖 {pattern_name} - {latest['Type']}", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Date**: {latest['Date'].strftime('%Y-%m-%d')}")
                st.write(f"**Price**: ₹{latest['Price']:.2f}")
                st.write(f"**Signal**: {latest['Signal']}")
                st.write(f"**Reliability**: {pattern_desc['reliability']}")
            with col2:
                st.write(f"**Description**:")
                st.info(pattern_desc["description"])
                st.write(f"**Trading Meaning**:")
                st.warning(pattern_desc["meaning"])
        
        # Display recommendation
        if insights["recommendations"]:
            rec = insights["recommendations"][0]
            st.write("#### 💡 Trading Recommendation")
            if rec["action"] == "Consider buying opportunity":
                st.success(f"**{rec['action']}** - {pattern_name} suggests potential upward movement.")
            elif rec["action"] == "Consider selling/caution":
                st.error(f"**{rec['action']}** - {pattern_name} suggests potential downward movement.")
            else:
                st.info(f"**{rec['action']}** - {pattern_name} requires confirmation from next candle.")
    
    # Pattern descriptions reference
    st.write("### 📚 Pattern Reference Guide")
    with st.expander("View All Pattern Descriptions", expanded=False):
        for pattern_name, pattern_info in PATTERN_DESCRIPTIONS.items():
            st.write(f"#### {pattern_name}")
            st.write(f"**Description**: {pattern_info['description']}")
            st.write(f"**Meaning**: {pattern_info['meaning']}")
            st.write(f"**Reliability**: {pattern_info['reliability']}")
            st.divider()
    
else:
    st.info("No candlestick patterns detected in the data. Patterns may appear as more data is analyzed.")

# --- Insight ---
st.subheader("📌 Auto Insight")
if kpis["daily_return_pct"] > 0 and df["Volume"].iloc[-1] > kpis["avg_volume"]:
    st.success("Bullish move supported by strong volume.")
elif kpis["daily_return_pct"] < 0:
    st.warning("Stock closed lower – short-term weakness.")
else:
    st.info("Stock is consolidating.")
