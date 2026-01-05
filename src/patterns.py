# src/patterns.py
import pandas as pd
import numpy as np

# Pattern descriptions for end users
PATTERN_DESCRIPTIONS = {
    "Doji": {
        "description": "A Doji represents market indecision. The open and close prices are nearly equal, creating a cross-like appearance.",
        "meaning": "Indicates uncertainty and potential reversal. Traders should wait for confirmation before making decisions.",
        "reliability": "Medium - Requires confirmation from next candle"
    },
    "Hammer": {
        "description": "A bullish reversal pattern with a small body at the top and a long lower shadow (at least twice the body size).",
        "meaning": "Suggests buyers are stepping in after a decline. Often signals a potential upward reversal, especially after a downtrend.",
        "reliability": "High - Strong bullish reversal signal"
    },
    "Shooting Star": {
        "description": "A bearish reversal pattern with a small body at the bottom and a long upper shadow (at least twice the body size).",
        "meaning": "Indicates sellers are taking control after an uptrend. Suggests potential downward reversal.",
        "reliability": "High - Strong bearish reversal signal"
    },
    "Bullish Engulfing": {
        "description": "A two-candle pattern where a large bullish candle completely engulfs the previous bearish candle.",
        "meaning": "Shows strong buying pressure overwhelming sellers. Indicates potential trend reversal from bearish to bullish.",
        "reliability": "High - Very strong bullish reversal signal"
    },
    "Bearish Engulfing": {
        "description": "A two-candle pattern where a large bearish candle completely engulfs the previous bullish candle.",
        "meaning": "Shows strong selling pressure overwhelming buyers. Indicates potential trend reversal from bullish to bearish.",
        "reliability": "High - Very strong bearish reversal signal"
    },
    "Bullish Marubozu": {
        "description": "A strong bullish candle with no shadows - opens at the low and closes at the high.",
        "meaning": "Indicates strong buying pressure throughout the session. Suggests continuation of upward momentum.",
        "reliability": "Medium - Strong continuation signal"
    },
    "Bearish Marubozu": {
        "description": "A strong bearish candle with no shadows - opens at the high and closes at the low.",
        "meaning": "Indicates strong selling pressure throughout the session. Suggests continuation of downward momentum.",
        "reliability": "Medium - Strong continuation signal"
    },
    "Morning Star": {
        "description": "A three-candle bullish reversal pattern: bearish candle, small body (star), then large bullish candle.",
        "meaning": "Signals potential reversal from downtrend to uptrend. The 'star' represents indecision before the bullish move.",
        "reliability": "High - Strong bullish reversal signal"
    },
    "Evening Star": {
        "description": "A three-candle bearish reversal pattern: bullish candle, small body (star), then large bearish candle.",
        "meaning": "Signals potential reversal from uptrend to downtrend. The 'star' represents indecision before the bearish move.",
        "reliability": "High - Strong bearish reversal signal"
    }
}

def detect_candlestick_patterns(df):
    """
    Detect common candlestick patterns in stock data.
    Ensures OHLC values are calculated based on proper date ordering.
    Returns a DataFrame with pattern detections and insights.
    """
    # Ensure dataframe is sorted by date and reset index
    df_sorted = df.sort_values("Date").reset_index(drop=True)
    
    # Verify required columns exist
    required_cols = ["Date", "Open", "High", "Low", "Close"]
    if not all(col in df_sorted.columns for col in required_cols):
        return pd.DataFrame(columns=["Date", "Pattern", "Type", "Signal", "Price"])
    
    patterns = []
    
    for i in range(1, len(df_sorted)):
        # Get current and previous candles by date-ordered index
        current_row = df_sorted.iloc[i]
        prev_row = df_sorted.iloc[i-1]
        
        # Extract date and OHLC values explicitly
        current_date = current_row["Date"]
        prev_date = prev_row["Date"]
        
        # Current candle OHLC (calculated from date-ordered data)
        open_price = float(current_row["Open"])
        close_price = float(current_row["Close"])
        high_price = float(current_row["High"])
        low_price = float(current_row["Low"])
        
        # Previous candle OHLC (calculated from date-ordered data)
        prev_open = float(prev_row["Open"])
        prev_close = float(prev_row["Close"])
        prev_high = float(prev_row["High"])
        prev_low = float(prev_row["Low"])
        
        # Validate data integrity
        if not (low_price <= min(open_price, close_price) <= high_price and
                low_price <= max(open_price, close_price) <= high_price):
            continue  # Skip invalid OHLC data
        
        if not (prev_low <= min(prev_open, prev_close) <= prev_high and
                prev_low <= max(prev_open, prev_close) <= prev_high):
            continue  # Skip if previous candle has invalid data
        
        body = abs(close_price - open_price)
        upper_shadow = high_price - max(open_price, close_price)
        lower_shadow = min(open_price, close_price) - low_price
        total_range = high_price - low_price
        
        # Avoid division by zero
        if total_range == 0:
            continue
            
        body_ratio = body / total_range if total_range > 0 else 0
        
        detected_pattern = None
        pattern_type = None
        signal = None
        
        # 1. Doji Pattern (Indecision)
        if body_ratio < 0.1 and total_range > 0:
            detected_pattern = "Doji"
            pattern_type = "Indecision"
            signal = "Neutral"
        
        # 2. Hammer (Bullish Reversal)
        elif (lower_shadow > 2 * body and 
              upper_shadow < body * 0.3 and 
              close_price > open_price * 0.95):
            detected_pattern = "Hammer"
            pattern_type = "Bullish Reversal"
            signal = "Bullish"
        
        # 3. Shooting Star (Bearish Reversal)
        elif (upper_shadow > 2 * body and 
              lower_shadow < body * 0.3 and 
              close_price < open_price * 1.05):
            detected_pattern = "Shooting Star"
            pattern_type = "Bearish Reversal"
            signal = "Bearish"
        
        # 4. Bullish Engulfing
        elif (prev_close < prev_open and  # Previous was bearish
              close_price > open_price and  # Current is bullish
              open_price < prev_close and  # Current opens below prev close
              close_price > prev_open):  # Current closes above prev open
            detected_pattern = "Bullish Engulfing"
            pattern_type = "Bullish Reversal"
            signal = "Bullish"
        
        # 5. Bearish Engulfing
        elif (prev_close > prev_open and  # Previous was bullish
              close_price < open_price and  # Current is bearish
              open_price > prev_close and  # Current opens above prev close
              close_price < prev_open):  # Current closes below prev open
            detected_pattern = "Bearish Engulfing"
            pattern_type = "Bearish Reversal"
            signal = "Bearish"
        
        # 6. Marubozu (Strong Trend)
        elif body_ratio > 0.9:
            if close_price > open_price:
                detected_pattern = "Bullish Marubozu"
                pattern_type = "Strong Bullish"
                signal = "Bullish"
            else:
                detected_pattern = "Bearish Marubozu"
                pattern_type = "Strong Bearish"
                signal = "Bearish"
        
        # 7. Morning Star (if we have 3 candles)
        if i >= 2:
            prev_prev_row = df_sorted.iloc[i-2]
            prev_prev_open = float(prev_prev_row["Open"])
            prev_prev_close = float(prev_prev_row["Close"])
            
            if (prev_prev_close < prev_prev_open and  # First candle bearish
                prev_close < prev_open and  # Second candle bearish (small body)
                close_price > open_price and  # Third candle bullish
                close_price > (prev_prev_open + prev_prev_close) / 2):  # Closes above midpoint
                detected_pattern = "Morning Star"
                pattern_type = "Bullish Reversal"
                signal = "Bullish"
        
        # 8. Evening Star (if we have 3 candles)
        if i >= 2:
            prev_prev_row = df_sorted.iloc[i-2]
            prev_prev_open = float(prev_prev_row["Open"])
            prev_prev_close = float(prev_prev_row["Close"])
            
            if (prev_prev_close > prev_prev_open and  # First candle bullish
                prev_close > prev_open and  # Second candle bullish (small body)
                close_price < open_price and  # Third candle bearish
                close_price < (prev_prev_open + prev_prev_close) / 2):  # Closes below midpoint
                detected_pattern = "Evening Star"
                pattern_type = "Bearish Reversal"
                signal = "Bearish"
        
        if detected_pattern:
            patterns.append({
                "Date": current_date,  # Use explicitly extracted date
                "Pattern": detected_pattern,
                "Type": pattern_type,
                "Signal": signal,
                "Price": close_price
            })
    
    if not patterns:
        return pd.DataFrame(columns=["Date", "Pattern", "Type", "Signal", "Price"])
    
    result_df = pd.DataFrame(patterns)
    # Ensure dates are datetime type
    result_df["Date"] = pd.to_datetime(result_df["Date"])
    return result_df


def get_pattern_insights(patterns_df, df):
    """
    Generate comprehensive insights from detected candlestick patterns.
    Returns a dictionary with insights and statistics.
    """
    if patterns_df.empty:
        return {
            "summary": "No significant candlestick patterns detected in recent data.",
            "sentiment": "Neutral",
            "bullish_count": 0,
            "bearish_count": 0,
            "neutral_count": 0,
            "latest_pattern": None,
            "pattern_counts": {},
            "recommendations": []
        }
    
    # Get recent patterns (last 20 for better analysis)
    recent_patterns = patterns_df.tail(20)
    
    # Count pattern types
    bullish_count = len(recent_patterns[recent_patterns["Signal"] == "Bullish"])
    bearish_count = len(recent_patterns[recent_patterns["Signal"] == "Bearish"])
    neutral_count = len(recent_patterns[recent_patterns["Signal"] == "Neutral"])
    
    # Overall sentiment
    if bullish_count > bearish_count * 1.5:
        sentiment = "Strongly Bullish"
    elif bullish_count > bearish_count:
        sentiment = "Bullish"
    elif bearish_count > bullish_count * 1.5:
        sentiment = "Strongly Bearish"
    elif bearish_count > bullish_count:
        sentiment = "Bearish"
    else:
        sentiment = "Mixed/Neutral"
    
    # Latest pattern
    latest_pattern = recent_patterns.iloc[-1] if not recent_patterns.empty else None
    
    # Pattern frequency
    pattern_counts = recent_patterns["Pattern"].value_counts().to_dict()
    
    # Generate recommendations
    recommendations = []
    if latest_pattern:
        pattern_name = latest_pattern['Pattern']
        if pattern_name in PATTERN_DESCRIPTIONS:
            desc = PATTERN_DESCRIPTIONS[pattern_name]
            recommendations.append({
                "pattern": pattern_name,
                "action": "Watch for confirmation" if latest_pattern['Signal'] == 'Neutral' 
                         else "Consider buying opportunity" if latest_pattern['Signal'] == 'Bullish'
                         else "Consider selling/caution",
                "description": desc["description"],
                "meaning": desc["meaning"],
                "reliability": desc["reliability"]
            })
    
    # Summary text
    summary_parts = []
    if bullish_count > 0 or bearish_count > 0:
        summary_parts.append(f"**Market Sentiment**: {sentiment}")
        summary_parts.append(f"Detected {bullish_count} bullish, {bearish_count} bearish, and {neutral_count} neutral patterns in recent data.")
    
    if latest_pattern:
        summary_parts.append(f"**Latest Pattern**: {latest_pattern['Pattern']} on {latest_pattern['Date'].strftime('%Y-%m-%d')} at ₹{latest_pattern['Price']:.2f}")
    
    return {
        "summary": "\n\n".join(summary_parts),
        "sentiment": sentiment,
        "bullish_count": bullish_count,
        "bearish_count": bearish_count,
        "neutral_count": neutral_count,
        "latest_pattern": latest_pattern,
        "pattern_counts": pattern_counts,
        "recommendations": recommendations,
        "all_patterns": recent_patterns
    }


def get_pattern_description(pattern_name):
    """
    Get description for a specific pattern.
    """
    return PATTERN_DESCRIPTIONS.get(pattern_name, {
        "description": "Pattern description not available.",
        "meaning": "Unknown pattern meaning.",
        "reliability": "Unknown"
    })

