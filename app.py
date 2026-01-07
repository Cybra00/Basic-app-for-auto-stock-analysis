import streamlit as st
import pandas as pd

import time
from src.loader import load_stock_data, fetch_live_data
from src.kpis import compute_kpis
from src.indicators import add_indicators
from src.charts import candlestick_chart, volume_chart, close_trend, volume_analysis_chart, obv_chart
from src.patterns import detect_candlestick_patterns, get_pattern_insights, get_pattern_description, PATTERN_DESCRIPTIONS

st.set_page_config(page_title="Stock Auto Analysis", layout="wide")

st.title("📈 Stock KPI Auto-Analysis Dashboard (v2.1 DEBUG)")

# --- CSV Upload ---
# --- Data Source Selection ---
data_source = st.sidebar.radio("Data Source", ["Upload CSV", "Live Ticker"], index=0)

if 'stock_data' not in st.session_state:
    st.session_state['stock_data'] = pd.DataFrame()
df = st.session_state['stock_data']

if data_source == "Upload CSV":
    uploaded_file = st.sidebar.file_uploader("Upload Stock OHLCV CSV", type=["csv"])
    if uploaded_file is not None:
        try:
            df = load_stock_data(uploaded_file)
            st.session_state['stock_data'] = df
        except Exception as e:
            st.error(str(e))
            st.stop()
    else:
        st.warning("Please upload a stock CSV file to begin analysis.")
        st.stop()
        
else: # Live Ticker
    ticker = st.sidebar.text_input("Enter Ticker Symbol (e.g. RELIANCE.NS)", value="")
    # Valid intervals and periods map
    valid_periods = {
        "1m": ["1d", "5d", "7d"],
        "5m": ["1d", "5d", "1mo", "60d"],
        "15m": ["1d", "5d", "1mo", "60d"],
        "30m": ["1d", "5d", "1mo", "60d"],
        "1h": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y"],
        "1d": ["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
    }
    
    interval = st.sidebar.selectbox("Interval", list(valid_periods.keys()), index=5)
    
    # Dynamic period selection based on interval
    available_periods = valid_periods[interval]
    # Default to a reasonable period (e.g., 1mo for daily, 1d for 1m)
    default_index = len(available_periods) - 1 if interval == "1m" else 2 if len(available_periods) > 2 else 0
    if interval == "1m": default_index = 0 # Default 1m to 1d for speed
    if interval == "1d": default_index = 3 # Default 1d to 1y (index 3 in new list: 1mo, 3mo, 6mo, 1y)

    period = st.sidebar.selectbox("Period", available_periods, index=default_index)
    
    auto_refresh = st.sidebar.checkbox("Enable Live Auto-Refresh (60s)", value=False)
    
    if st.sidebar.button("Fetch Data") or auto_refresh:
        try:
            with st.spinner(f"Fetching data for {ticker}..."):
                df, warning_msg = fetch_live_data(ticker, period=period, interval=interval)
                st.session_state['stock_data'] = df
            
            if warning_msg:
                st.warning(warning_msg)
            
            if df.empty:
                st.error(f"No data found for {ticker} with {interval} interval. Try using a larger interval (e.g., 5m, 15m) or checking the ticker symbol.")
                st.stop()
                
            st.success(f"Fetched {len(df)} rows for {ticker}")
            
        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")
            st.stop()
    
    if df.empty:
        st.info("Enter ticker and click 'Fetch Data'")
        st.stop()

    # Auto-refresh logic moved to end



# --- Auto Analysis Pipeline ---
df = add_indicators(df)
kpis = compute_kpis(df)

# Detect patterns with error handling
try:
    patterns_df = detect_candlestick_patterns(df)
    
    # Add Status column
    if not patterns_df.empty:
        patterns_df["Status"] = "Confirmed"
        
        # In Live Mode, mark patterns on the last candle as Unconfirmed
        if data_source == "Live Ticker" and not df.empty:
            last_date = df["Date"].iloc[-1]
            patterns_df.loc[patterns_df["Date"] == last_date, "Status"] = "Unconfirmed"
            
    # Debug: Show pattern count in sidebar
    with st.sidebar:
        st.write(f"**Patterns Detected**: {len(patterns_df)}")
except Exception as e:
    patterns_df = pd.DataFrame(columns=["Date", "Pattern", "Type", "Signal", "Price", "Status"])
    st.error(f"Error detecting patterns: {str(e)}")



# --- KPI Cards ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Latest Price", f"₹{kpis['latest_price']:.2f}")
col2.metric("Daily Return", f"{kpis['daily_return_pct']:.2f}%")
col3.metric("52W High", f"₹{kpis['high_52w']:.2f}")
col4.metric("Volatility", f"{kpis['volatility_pct']:.2f}%")

# --- Candlestick Pattern Detection (Summary) ---
st.subheader("🕯️ Candlestick Pattern Detection & Analysis")

if not patterns_df.empty:
    st.success(f"✅ **{len(patterns_df)} Patterns Detected**")

# Calculate insights early for summary
insights = None
if not patterns_df.empty:
    insights = get_pattern_insights(patterns_df, df)

# Always show pattern detection status/summary
if patterns_df.empty:
    st.warning("⚠️ No candlestick patterns detected in the current data.")
    st.info("💡 **Tips to see patterns:**\n"
            "- Ensure your CSV has sufficient data (at least 20+ rows)\n"
            "- Patterns are detected based on OHLC relationships\n"
            "- Try uploading a different stock data file\n"
            "- Some patterns require specific market conditions")
    
    # Show data summary for debugging
    with st.expander("🔍 Data Summary (Debug)", expanded=False):
        st.write(f"**Total Rows**: {len(df)}")
        st.write(f"**Date Range**: {df['Date'].min()} to {df['Date'].max()}")
        st.write(f"**Columns**: {', '.join(df.columns.tolist())}")
        if len(df) > 0:
            st.write("**Sample Data (First 5 rows):**")
            st.dataframe(df[["Date", "Open", "High", "Low", "Close"]].head(), use_container_width=True)
else:
    # Display sentiment summary in columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Bullish Patterns", insights["bullish_count"], delta=None)
    with col2:
        st.metric("Bearish Patterns", insights["bearish_count"], delta=None)
    with col3:
        sentiment_color = "🟢" if "Bullish" in insights["sentiment"] else "🔴" if "Bearish" in insights["sentiment"] else "🟡"
        st.metric("Market Sentiment", f"{sentiment_color} {insights['sentiment']}")

# --- Auto Insight ---
st.subheader("📌 Auto Insight")
if kpis["daily_return_pct"] > 0 and df["Volume"].iloc[-1] > kpis["avg_volume"]:
    st.success("Bullish move supported by strong volume.")
elif kpis["daily_return_pct"] < 0:
    st.warning("Stock closed lower – short-term weakness.")
else:
    st.info("Stock is consolidating.")

# --- Charts ---
# Add toggle for patterns
show_patterns = st.checkbox("Show Patterns on Chart", value=True, help="Toggle to show/hide candlestick pattern markers")

st.plotly_chart(candlestick_chart(df, patterns_df, show_patterns=show_patterns), use_container_width=True)
st.plotly_chart(close_trend(df), use_container_width=True)
st.plotly_chart(volume_chart(df), use_container_width=True)

# --- Advanced Analysis ---
st.subheader("🔬 Advanced Volume & Trend Analysis")
tab1, tab2 = st.tabs(["Volume Analysis", "On-Balance Volume (OBV)"])

with tab1:
    st.plotly_chart(volume_analysis_chart(df), use_container_width=True)
    
    # Display Trend Signal if available
    if "Trend_Signal" in df.columns:
        latest_signal = df["Trend_Signal"].iloc[-1]
        if latest_signal == "Bullish Confirmation":
            st.success(f"🚀 **Trend Signal**: {latest_signal} (Price ↑ + Vol ↑)")
        elif latest_signal == "Bearish Selling Pressure":
            st.error(f"⚠️ **Trend Signal**: {latest_signal} (Price ↓ + Vol ↑)")
        else:
            st.info(f"ℹ️ **Trend Signal**: {latest_signal}")

    if "Volume_Breakout" in df.columns and df["Volume_Breakout"].any():
        st.info("💡 **Insight**: High volume breakouts detected (marked with stars). These often precede significant price moves.")

with tab2:
    st.plotly_chart(obv_chart(df), use_container_width=True)
    st.caption("On-Balance Volume (OBV) tracks buying vs selling pressure. Rising OBV + Flat Price = Accumulation (Bullish).")

# --- Detailed Pattern Analysis (Bottom) ---
if not patterns_df.empty and insights:
    st.markdown("---")
    st.subheader("📊 Detailed Pattern Analysis")
    
    # Display recent patterns table with enhanced formatting
    st.write("### Recent Detected Patterns")
    display_patterns = patterns_df.tail(15)[["Date", "Pattern", "Type", "Signal", "Price", "Status"]].copy()
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
    if insights["latest_pattern"] is not None:
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

# Auto-refresh logic moved to end
if "auto_refresh" in locals() and auto_refresh:
    time.sleep(60)
    st.rerun()
