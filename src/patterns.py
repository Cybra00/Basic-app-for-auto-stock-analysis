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
    Detect common candlestick patterns in stock data using VOLATILITY-ADAPTIVE THRESHOLDS.
    Ensures OHLC values are calculated based on proper date ordering.
    Returns a DataFrame with pattern detections and insights.
    """
    # Ensure dataframe is sorted by date and reset index
    df_sorted = df.sort_values("Date").reset_index(drop=True).copy()
    
    # Verify required columns exist
    required_cols = ["Date", "Open", "High", "Low", "Close"]
    if not all(col in df_sorted.columns for col in required_cols):
        return pd.DataFrame(columns=["Date", "Pattern", "Type", "Signal", "Price"])
    
    # --- PRE-CALCULATION: Volatility-Adaptive Thresholds ---
    df_sorted['Body'] = (df_sorted['Close'] - df_sorted['Open']).abs()
    df_sorted['Range'] = df_sorted['High'] - df_sorted['Low']
    df_sorted['Avg_Body'] = df_sorted['Body'].rolling(window=14, min_periods=1).mean()
    df_sorted['Avg_Range'] = df_sorted['Range'].rolling(window=14, min_periods=1).mean()
    
    patterns = []
    
    for i in range(1, len(df_sorted)):
        # Get current and previous candles by date-ordered index
        current_row = df_sorted.iloc[i]
        prev_row = df_sorted.iloc[i-1]
        
        # Extract date and OHLC values explicitly
        current_date = current_row["Date"]
        
        # Current candle OHLC
        open_price = float(current_row["Open"])
        close_price = float(current_row["Close"])
        high_price = float(current_row["High"])
        low_price = float(current_row["Low"])
        
        # Previous candle OHLC
        prev_open = float(prev_row["Open"])
        prev_close = float(prev_row["Close"])
        prev_high = float(prev_row["High"])
        prev_low = float(prev_row["Low"])
        
        # Volatility context
        avg_body = float(current_row["Avg_Body"]) if current_row["Avg_Body"] > 0 else 0.001
        avg_range = float(current_row["Avg_Range"]) if current_row["Avg_Range"] > 0 else 0.001
        
        # ABSOLUTE MINIMUM: Body must be > 0.3% of price to be "significant"
        # This prevents tiny candles in consolidation zones from being detected
        min_body_pct = 0.003
        min_body_abs = close_price * min_body_pct
        
        # Validate data integrity
        if not (low_price <= min(open_price, close_price) <= high_price and
                low_price <= max(open_price, close_price) <= high_price):
            continue
        
        if not (prev_low <= min(prev_open, prev_close) <= prev_high and
                prev_low <= max(prev_open, prev_close) <= prev_high):
            continue
        
        body = abs(close_price - open_price)
        upper_shadow = high_price - max(open_price, close_price)
        lower_shadow = min(open_price, close_price) - low_price
        total_range = high_price - low_price
        
        if total_range == 0:
            continue
            
        body_ratio = body / total_range
        
        detected_pattern = None
        pattern_type = None
        signal = None
        
        # =================================================================
        # CHECK 3-CANDLE PATTERNS FIRST (Highest Priority)
        # =================================================================
        if i >= 2:
            prev_prev_row = df_sorted.iloc[i-2]
            prev_prev_open = float(prev_prev_row["Open"])
            prev_prev_close = float(prev_prev_row["Close"])
            prev_prev_body = abs(prev_prev_close - prev_prev_open)
            prev_body = abs(prev_close - prev_open)
            
            # STRICT Morning Star:
            # 1. First candle: Big bearish (Body > 0.8 * Avg)
            # 2. Star: Small body indecision (Body < 0.5 * Avg)
            # 3. Third: Big bullish reversal (Body > 0.8 * Avg)
            if (prev_prev_close < prev_prev_open and  # First bearish
                prev_prev_body > min_body_abs and  # ABSOLUTE: First must be meaningful
                prev_prev_body > 0.8 * avg_body and  # SIGNIFICANCE: First is big
                prev_body < 0.5 * avg_body and  # SIGNIFICANCE: Star is small
                close_price > open_price and  # Third bullish
                body > min_body_abs and  # ABSOLUTE: Third must be meaningful
                body > 0.8 * avg_body and  # SIGNIFICANCE: Third is big
                close_price > (prev_prev_open + prev_prev_close) / 2):
                detected_pattern = "Morning Star"
                pattern_type = "Bullish Reversal"
                signal = "Bullish"
            
            # STRICT Evening Star:
            elif (prev_prev_close > prev_prev_open and  # First bullish
                  prev_prev_body > min_body_abs and  # ABSOLUTE: First must be meaningful
                  prev_prev_body > 0.8 * avg_body and  # SIGNIFICANCE: First is big
                  prev_body < 0.5 * avg_body and  # SIGNIFICANCE: Star is small
                  close_price < open_price and  # Third bearish
                  body > min_body_abs and  # ABSOLUTE: Third must be meaningful
                  body > 0.8 * avg_body and  # SIGNIFICANCE: Third is big
                  close_price < (prev_prev_open + prev_prev_close) / 2):
                detected_pattern = "Evening Star"
                pattern_type = "Bearish Reversal"
                signal = "Bearish"
        
        # =================================================================
        # CHECK 2-CANDLE PATTERNS (Engulfing)
        # =================================================================
        if detected_pattern is None:
            prev_body_val = abs(prev_close - prev_open)
            
            # STRICT Bullish Engulfing:
            # 1. Geometry: Engulfs previous body
            # 2. Significance: Current body > 0.8 * Avg
            if (prev_close < prev_open and  # Previous bearish
                close_price > open_price and  # Current bullish
                open_price < prev_close and  # Opens below prev close
                close_price > prev_open and  # Closes above prev open
                body > min_body_abs and  # ABSOLUTE: Must be meaningful
                body > 0.8 * avg_body):  # SIGNIFICANCE CHECK
                detected_pattern = "Bullish Engulfing"
                pattern_type = "Bullish Reversal"
                signal = "Bullish"
            
            # STRICT Bearish Engulfing:
            elif (prev_close > prev_open and  # Previous bullish
                  close_price < open_price and  # Current bearish
                  open_price > prev_close and  # Opens above prev close
                  close_price < prev_open and  # Closes below prev open
                  body > min_body_abs and  # ABSOLUTE: Must be meaningful
                  body > 0.8 * avg_body):  # SIGNIFICANCE CHECK
                detected_pattern = "Bearish Engulfing"
                pattern_type = "Bearish Reversal"
                signal = "Bearish"
        
        # =================================================================
        # CHECK SINGLE-CANDLE PATTERNS
        # =================================================================
        if detected_pattern is None:
            # 1. Doji Pattern (Indecision) - very small body relative to range
            # No significance check needed (Dojis are inherently weak)
            if body_ratio < 0.1 and total_range > 0:
                detected_pattern = "Doji"
                pattern_type = "Indecision"
                signal = "Neutral"
            
            # 2. STRICT Hammer:
            # - Geometry: Lower shadow >= 2x body, upper shadow <= 10% of body
            # - Significance: Total Range > 0.8 * Avg Range AND Range > min threshold
            elif (body > 0 and 
                  total_range > min_body_abs and  # ABSOLUTE: Range must be meaningful
                  lower_shadow >= 2 * body and 
                  upper_shadow <= body * 0.1 and
                  total_range > 0.8 * avg_range):
                detected_pattern = "Hammer"
                pattern_type = "Bullish Reversal"
                signal = "Bullish"
            
            # 3. STRICT Shooting Star:
            # - Geometry: Upper shadow >= 2x body, lower shadow <= 10% of body
            # - Significance: Total Range > 0.8 * Avg Range AND Range > min threshold
            elif (body > 0 and 
                  total_range > min_body_abs and  # ABSOLUTE: Range must be meaningful
                  upper_shadow >= 2 * body and 
                  lower_shadow <= body * 0.1 and
                  total_range > 0.8 * avg_range):
                detected_pattern = "Shooting Star"
                pattern_type = "Bearish Reversal"
                signal = "Bearish"
            
            # 4. STRICT Marubozu:
            # - Shadows: Both < 3% of body (virtually zero wicks)
            # - Significance: Body > 1.2 * Avg Body AND Body > min threshold
            elif (body_ratio > 0.97 and
                  body > min_body_abs and  # ABSOLUTE: Body must be meaningful
                  upper_shadow < body * 0.03 and
                  lower_shadow < body * 0.03 and
                  body > 1.2 * avg_body):
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
                "Date": current_date,
                "Pattern": detected_pattern,
                "Type": pattern_type,
                "Signal": signal,
                "Price": close_price
            })
    
    if not patterns:
        return pd.DataFrame(columns=["Date", "Pattern", "Type", "Signal", "Price"])
    
    result_df = pd.DataFrame(patterns)
    result_df["Date"] = pd.to_datetime(result_df["Date"])
    return result_df


def calculate_pattern_accuracy(df, patterns_df):
    """
    Backtest: Calculate historical win rate for each pattern type.
    Win Condition: Price increases > 0.5% in next 3 bars (Bullish) or drops > 0.5% (Bearish)
    Returns: Dict {PatternName: "WinRate% (Count)"}
    """
    if patterns_df.empty or df.empty:
        return {}
        
    accuracy_map = {}
    pattern_types = patterns_df["Pattern"].unique()
    
    # Pre-calculate future returns for efficiency
    # checking 3-bar forward return
    future_return = df["Close"].shift(-3) / df["Close"] - 1
    
    # Create a mapping of Date -> Return
    returns_map = dict(zip(df["Date"], future_return))
    
    for p_name in pattern_types:
        subset = patterns_df[patterns_df["Pattern"] == p_name]
        wins = 0
        total = 0
        
        for _, row in subset.iterrows():
            date = row["Date"]
            signal = row["Signal"]
            
            # Skip if we can't check future outcome (e.g. today's pattern)
            if date not in returns_map or pd.isna(returns_map[date]):
                continue
                
            ret = returns_map[date]
            total += 1
            
            if signal == "Bullish" and ret > 0.005: # > 0.5% gain
                wins += 1
            elif signal == "Bearish" and ret < -0.005: # > 0.5% loss
                wins += 1
                
        if total >= 3: # Only report if we have significant history
            win_rate = int((wins / total) * 100)
            accuracy_map[p_name] = f"{win_rate}% (Based on {total} historic occurrences)"
        else:
            accuracy_map[p_name] = "Insufficient history"
            
    return accuracy_map

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
    
    # --- FILTERING LOGIC (Sync with Charts) ---
    # 1. Score Filter: Remove low-impact patterns (Score = 1, like Doji)
    def get_score(pat_name):
        return PATTERN_DESCRIPTIONS.get(pat_name, {}).get("score", 1)
    
    patterns_df = patterns_df.copy()
    patterns_df["Score"] = patterns_df["Pattern"].apply(get_score)
    filtered_patterns = patterns_df[patterns_df["Score"] > 1].copy()
    
    # 2. Trend Filter: Match visual chart logic
    if not filtered_patterns.empty:
        # Merge with indicators
        merge_cols = ['Date', 'Close']
        if "VWAP" in df.columns: merge_cols.append("VWAP")
        if "MA50" in df.columns: merge_cols.append("MA50")
        
        merged = filtered_patterns.merge(df[merge_cols], on='Date', how='left')
        
        # Apply Logic
        keep_mask = pd.Series(False, index=merged.index)
        
        for idx, row in merged.iterrows():
            signal = row['Signal']
            close = row['Close']
            
            if signal == 'Bullish':
                # Show Bullish if > VWAP (or if VWAP missing)
                vwap = row.get('VWAP', -1)
                if vwap == -1 or close > vwap:
                    keep_mask.at[idx] = True
            elif signal == 'Bearish':
                # Show Bearish if < MA50 (or if MA50 missing)
                ma50 = row.get('MA50', -1)
                if ma50 == -1 or close < ma50:
                    keep_mask.at[idx] = True
            else:
                # Keep Neutral? Using Score > 1 handled basics, but let's keep neutrals if score > 1
                keep_mask.at[idx] = True
                
        filtered_patterns = merged[keep_mask]
    
    # USE FILTERED PATTERNS FOR COUNTS AND INSIGHTS
    # 1. Count Totals (for basic UI display)
    total_bullish = len(filtered_patterns[filtered_patterns["Signal"] == "Bullish"])
    total_bearish = len(filtered_patterns[filtered_patterns["Signal"] == "Bearish"])
    total_neutral = len(filtered_patterns[filtered_patterns["Signal"] == "Neutral"])

    # 2. Get Recent Patterns (Focus on last 20 VALID patterns for scoring)
    recent_patterns = filtered_patterns.tail(20).copy()
    
    # --- WEIGHTED SCORING LOGIC ---
    sentiment_score = 0
    
    # Identify the VERY LATEST date in the data (for recency boost)
    latest_data_date = df["Date"].max()
    
    for _, row in recent_patterns.iterrows():
        pattern_name = row["Pattern"]
        signal = row["Signal"]
        
        # Get Pattern Score (already in row from filter step, but re-get to be safe or use row['Score'])
        p_score = row["Score"]
        
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
    is_red_candle = latest_close < latest_open
    is_green_candle = latest_close > latest_open
    
    # --- 5. MOMENTUM CONFIRMATION (MACD & RSI) ---
    macd_signal = "Neutral"
    if "MACD" in df.columns and "Signal_Line" in df.columns:
        macd_val = df["MACD"].iloc[-1]
        sig_val = df["Signal_Line"].iloc[-1]
        if macd_val > sig_val:
            macd_signal = "Bullish"
        else:
            macd_signal = "Bearish"
            
    rsi_signal = "Neutral"
    if "RSI" in df.columns:
        rsi_val = df["RSI"].iloc[-1]
        if rsi_val > 70:
            rsi_signal = "Overbought (Risk of Pullback)"
        elif rsi_val < 30:
            rsi_signal = "Oversold (Bounce Potential)"
        elif rsi_val > 50:
            rsi_signal = "Bullish Zone"
        else:
            rsi_signal = "Bearish Zone"

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
    
    # --- 6. HISTORICAL ACCURACY & RECOMMENDATIONS ---
    accuracy_stats = calculate_pattern_accuracy(df, patterns_df)
    
    latest_pattern = recent_patterns.iloc[-1] if not recent_patterns.empty else None
    recommendations = []
    
    if latest_pattern is not None:
        pattern_name = latest_pattern['Pattern']
        p_desc = PATTERN_DESCRIPTIONS.get(pattern_name, {})
        signal = latest_pattern['Signal']
        
        # Trend Context
        latest_close = df["Close"].iloc[-1]
        vwap = df["VWAP"].iloc[-1] if "VWAP" in df.columns else latest_close
        ma50 = df["MA50"].iloc[-1] if "MA50" in df.columns else latest_close
        
        is_uptrend = (latest_close > vwap) and (latest_close > ma50)
        is_downtrend = (latest_close < vwap) and (latest_close < ma50)
        
        action = "Watch for confirmation"
        
        if signal == 'Bullish':
            if is_uptrend:
                action = "✅ Strong Buy Signal (Trend Aligned) - Watch for confirmation"
            elif is_downtrend:
                action = "⚠️ Contratrend Buy Signal (High Risk) - Wait for strong reversal"
            else:
                action = "🤔 Tactical Buy (Mixed Trend) - Watch for confirmation"
        elif signal == 'Bearish':
            if is_downtrend:
                action = "✅ Strong Sell Signal (Trend Aligned) - Watch for confirmation"
            elif is_uptrend:
                action = "⚠️ Contratrend Sell Signal (High Risk) - Wait for confirmation"
            else:
                action = "🤔 Tactical Sell (Mixed Trend) - Watch for confirmation"
        
        # Momentum Warning
        if signal == 'Bullish' and macd_signal == 'Bearish':
            action += " (⚠️ Momentum Contradiction: Negative MACD)"
        if signal == 'Bearish' and macd_signal == 'Bullish':
            action += " (⚠️ Momentum Contradiction: Positive MACD)"
            
        # Add Accuracy Stats
        hist_acc = accuracy_stats.get(pattern_name, "N/A - Insufficient History")
        
        recommendations.append({
            "pattern": pattern_name,
            "action": action,
            "description": p_desc.get("description", ""),
            "meaning": p_desc.get("meaning", ""),
            "reliability": f"{p_desc.get('reliability', '')} | 📊 Historical Accuracy: {hist_acc}"
        })
        
    pattern_counts = recent_patterns["Pattern"].value_counts().to_dict()
    
    # Construct Summary
    summary_parts = []
    summary_parts.append(f"**Market Bias**: {sentiment}")
    summary_parts.append(f"**Trend Context**: {trend}")
    summary_parts.append(f"**Momentum**: {macd_signal} MACD, {rsi_signal} RSI")
    
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
