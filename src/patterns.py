# src/patterns.py
import pandas as pd
import numpy as np

# Pattern descriptions for end users with ADDED SCORES (1=Weak, 2=Medium, 3=Strong)
PATTERN_DESCRIPTIONS = {
    "Doji": {
        "description": "A Doji represents market indecision. The open and close prices are nearly equal, creating a cross-like appearance.",
        "meaning": "Indicates uncertainty and potential reversal. Traders should wait for confirmation before making decisions.",
        "reliability": "Medium - Requires confirmation from next candle",
        "score": 1
    },
    "Hammer": {
        "description": "A bullish reversal pattern with a small body at the top and a long lower shadow (at least twice the body size).",
        "meaning": "Suggests buyers are stepping in after a decline. Often signals a potential upward reversal, especially after a downtrend.",
        "reliability": "High - Strong bullish reversal signal",
        "score": 3
    },
    "Shooting Star": {
        "description": "A bearish reversal pattern with a small body at the bottom and a long upper shadow (at least twice the body size).",
        "meaning": "Indicates sellers are taking control after an uptrend. Suggests potential downward reversal.",
        "reliability": "High - Strong bearish reversal signal",
        "score": 3
    },
    "Bullish Engulfing": {
        "description": "A two-candle pattern where a large bullish candle completely engulfs the previous bearish candle.",
        "meaning": "Shows strong buying pressure overwhelming sellers. Indicates potential trend reversal from bearish to bullish.",
        "reliability": "High - Very strong bullish reversal signal",
        "score": 3
    },
    "Bearish Engulfing": {
        "description": "A two-candle pattern where a large bearish candle completely engulfs the previous bullish candle.",
        "meaning": "Shows strong selling pressure overwhelming buyers. Indicates potential trend reversal from bullish to bearish.",
        "reliability": "High - Very strong bearish reversal signal",
        "score": 3
    },
    "Bullish Marubozu": {
        "description": "A strong bullish candle with no shadows - opens at the low and closes at the high.",
        "meaning": "Indicates strong buying pressure throughout the session. Suggests continuation of upward momentum.",
        "reliability": "Medium - Strong continuation signal",
        "score": 2
    },
    "Bearish Marubozu": {
        "description": "A strong bearish candle with no shadows - opens at the high and closes at the low.",
        "meaning": "Indicates strong selling pressure throughout the session. Suggests continuation of downward momentum.",
        "reliability": "Medium - Strong continuation signal",
        "score": 2
    },
    "Morning Star": {
        "description": "A three-candle bullish reversal pattern: bearish candle, small body (star), then large bullish candle.",
        "meaning": "Signals potential reversal from downtrend to uptrend. The 'star' represents indecision before the bullish move.",
        "reliability": "High - Strong bullish reversal signal",
        "score": 3
    },
    "Evening Star": {
        "description": "A three-candle bearish reversal pattern: bullish candle, small body (star), then large bearish candle.",
        "meaning": "Signals potential reversal from uptrend to downtrend. The 'star' represents indecision before the bearish move.",
        "reliability": "High - Strong bearish reversal signal",
        "score": 3
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
        
        # Check 3-candle patterns first (they have priority)
        if i >= 2:
            prev_prev_row = df_sorted.iloc[i-2]
            prev_prev_open = float(prev_prev_row["Open"])
            prev_prev_close = float(prev_prev_row["Close"])
            prev_prev_body = abs(prev_prev_close - prev_prev_open)
            prev_body = abs(prev_close - prev_open)
            
            # 7. Morning Star (3-candle pattern - highest priority)
            if (prev_prev_close < prev_prev_open and  # First candle bearish
                prev_body < prev_prev_body * 0.5 and  # Second candle has small body (star)
                close_price > open_price and  # Third candle bullish
                close_price > (prev_prev_open + prev_prev_close) / 2):  # Closes above midpoint
                detected_pattern = "Morning Star"
                pattern_type = "Bullish Reversal"
                signal = "Bullish"
            
            # 8. Evening Star (3-candle pattern - highest priority)
            elif (prev_prev_close > prev_prev_open and  # First candle bullish
                  prev_body < prev_prev_body * 0.5 and  # Second candle has small body (star)
                  close_price < open_price and  # Third candle bearish
                  close_price < (prev_prev_open + prev_prev_close) / 2):  # Closes below midpoint
                detected_pattern = "Evening Star"
                pattern_type = "Bearish Reversal"
                signal = "Bearish"
        
        # Check 2-candle patterns (engulfing patterns)
        if detected_pattern is None:
            # 4. Bullish Engulfing
            if (prev_close < prev_open and  # Previous was bearish
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
        
        # Check single-candle patterns
        if detected_pattern is None:
            # 1. Doji Pattern (Indecision) - very small body
            if body_ratio < 0.1 and total_range > 0:
                detected_pattern = "Doji"
                pattern_type = "Indecision"
                signal = "Neutral"
            
            # 2. Hammer (Bullish Reversal) - long lower shadow, small upper shadow
            elif (body > 0 and lower_shadow >= 2 * body and 
                  upper_shadow <= body * 0.5):
                detected_pattern = "Hammer"
                pattern_type = "Bullish Reversal"
                signal = "Bullish"
            
            # 3. Shooting Star (Bearish Reversal) - long upper shadow, small lower shadow
            elif (body > 0 and upper_shadow >= 2 * body and 
                  lower_shadow <= body * 0.5):
                detected_pattern = "Shooting Star"
                pattern_type = "Bearish Reversal"
                signal = "Bearish"
            
            # 6. Marubozu (Strong Trend) - very large body, minimal shadows
            elif body_ratio > 0.9:
                if close_price > open_price:
                    detected_pattern = "Bullish Marubozu"
                    pattern_type = "Strong Bullish"
                    signal = "Bullish"
                else:
                    detected_pattern = "Bearish Marubozu"
                    pattern_type = "Strong Bearish"
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
    Generate comprehensive insights from detected candlestick patterns using WEIGHTED SCORING.
    Returns a dictionary with insights and statistics.
    """
    if patterns_df.empty:
        return {
            "summary": "No significant candlestick patterns detected in the current data window.",
            "sentiment": "Neutral",
            "bullish_count": 0,
            "bearish_count": 0,
            "neutral_count": 0,
            "latest_pattern": None,
            "pattern_counts": {},
            "recommendations": []
        }
    
    # 1. Count Totals (for basic UI display)
    total_bullish = len(patterns_df[patterns_df["Signal"] == "Bullish"])
    total_bearish = len(patterns_df[patterns_df["Signal"] == "Bearish"])
    total_neutral = len(patterns_df[patterns_df["Signal"] == "Neutral"])

    # 2. Get Recent Patterns (Focus on last 20 for scoring)
    recent_patterns = patterns_df.tail(20).copy()
    
    # --- WEIGHTED SCORING LOGIC ---
    sentiment_score = 0
    
    # Identify the VERY LATEST date in the data (for recency boost)
    latest_data_date = df["Date"].max()
    
    for _, row in recent_patterns.iterrows():
        pattern_name = row["Pattern"]
        signal = row["Signal"]
        
        # Get Pattern Score (Default to 1 if not found)
        p_info = PATTERN_DESCRIPTIONS.get(pattern_name, {"score": 1})
        p_score = p_info.get("score", 1)
        
        # Recency Multiplier: Double points if pattern is on the LATEST candle
        recency_mult = 1.0
        if row["Date"] == latest_data_date:
            recency_mult = 2.0
        
        # Calculate contribution
        if signal == "Bullish":
            sentiment_score += (p_score * recency_mult)
        elif signal == "Bearish":
            sentiment_score -= (p_score * recency_mult)
            
    # --- 3. TREND & MOMENTUM ANALYSIS ---
    # Safe Trend Calculation (Handles short CSVs)
    latest_close = df.iloc[-1]["Close"]
    latest_open = df.iloc[-1]["Open"]
    
    trend = "Neutral"
    trend_score_mod = 0
    
    if len(df) >= 50:
        ma_50 = df["Close"].rolling(window=50).mean().iloc[-1]
        if latest_close > ma_50:
            trend = "Bullish"
            trend_score_mod = 3
        else:
            trend = "Bearish"
            trend_score_mod = -3
    elif len(df) >= 20: # Fallback for shorter data
        ma_20 = df["Close"].rolling(window=20).mean().iloc[-1]
        if latest_close > ma_20:
            trend = "Bullish (Short-term)"
            trend_score_mod = 2
        else:
            trend = "Bearish (Short-term)"
            trend_score_mod = -2
            
    # Add Trend modifier to sentiment
    sentiment_score += trend_score_mod
    
    # --- 4. MOMENTUM VETO (CRITICAL FIX) ---
    # If the latest candle receives a strong negative move (Red Candle), 
    # we CANNOT call it "Strongly Bullish" regardless of history.
    
    is_red_candle = latest_close < latest_open
    is_green_candle = latest_close > latest_open
    
    # --- Final Sentiment Classification ---
    if sentiment_score >= 8:
        sentiment = "Strongly Bullish"
        # VETO: Downgrade if today is RED
        if is_red_candle:
            sentiment = "Bullish (but Short-term Pullback)"
            
    elif sentiment_score >= 3:
        sentiment = "Bullish"
         # VETO check
        if is_red_candle:
            sentiment = "Bullish (Weak Follow-through)"
            
    elif sentiment_score <= -8:
        sentiment = "Strongly Bearish"
        # VETO: Downgrade if today is GREEN (Dead cat bounce potential)
        if is_green_candle:
             sentiment = "Bearish (with Short-term Bounce)"
             
    elif sentiment_score <= -3:
        sentiment = "Bearish"
    else:
        sentiment = "Mixed/Neutral"
    
    # Recommendations Logic
    latest_pattern = recent_patterns.iloc[-1] if not recent_patterns.empty else None
    recommendations = []
    
    if latest_pattern is not None:
        pattern_name = latest_pattern['Pattern']
        p_desc = PATTERN_DESCRIPTIONS.get(pattern_name, {})
        
        action = "Watch for confirmation"
        signal = latest_pattern['Signal']
        
        # Context-Aware Advise
        # Context-Aware Advise
        # Check Trend Alignment (Price > VWAP and Price > MA50)
        # Note: df contains the full data with indicators
        latest_close = df["Close"].iloc[-1]
        vwap = df["VWAP"].iloc[-1] if "VWAP" in df.columns else latest_close
        ma50 = df["MA50"].iloc[-1] if "MA50" in df.columns else latest_close
        
        is_uptrend = (latest_close > vwap) and (latest_close > ma50)
        is_downtrend = (latest_close < vwap) and (latest_close < ma50)
        
        if signal == 'Bullish':
            if is_uptrend:
                action = "✅ Strong Buy Signal (Pattern aligns with Trend) - Watch for confirmation"
            elif is_downtrend:
                action = "⚠️ Contratrend Buy Signal (Down Trend - High Risk) - Wait for strong reversal"
            else:
                action = "🤔 Tactical Buy (Neutral/Mixed Trend) - Watch for confirmation"
                
        elif signal == 'Bearish':
            if is_downtrend:
                action = "✅ Strong Sell Signal (Pattern aligns with Trend) - Watch for confirmation"
            elif is_uptrend:
                action = "⚠️ Contratrend Sell Signal (Up Trend - Potential Pullback) - Wait for confirmation"
            else:
                action = "🤔 Tactical Sell (Neutral/Mixed Trend) - Watch for confirmation"
        
        recommendations.append({
            "pattern": pattern_name,
            "action": action,
            "description": p_desc.get("description", ""),
            "meaning": p_desc.get("meaning", ""),
            "reliability": p_desc.get("reliability", "")
        })
        
    # Pattern frequency for chart
    pattern_counts = recent_patterns["Pattern"].value_counts().to_dict()
    
    # Construct Summary
    summary_parts = []
    summary_parts.append(f"**Market Bias**: {sentiment}")
    summary_parts.append(f"**Trend Context**: {trend}")
    summary_parts.append(f"**Momentum**: {'Bearish (Price Drop)' if is_red_candle else 'Bullish (Price Rise)' if is_green_candle else 'Neutral'}")
    
    return {
        "summary": "\n\n".join(summary_parts),
        "sentiment": sentiment,
        "bullish_count": total_bullish,
        "bearish_count": total_bearish,
        "neutral_count": total_neutral,
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
