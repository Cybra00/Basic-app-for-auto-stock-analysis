# src/charts.py
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from src.patterns import PATTERN_DESCRIPTIONS

def candlestick_chart(df, patterns_df=None, show_patterns=True):
    """
    Create optimized candlestick chart with moving averages, volume, and pattern annotations.
    
    Args:
        df: DataFrame with OHLCV data and indicators (MA20, MA50)
        patterns_df: Optional DataFrame with detected patterns
        show_patterns: Boolean to toggle pattern annotations (default: True)
    """
    # Create subplots: candlestick on top, volume on bottom
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=('Price Action with Moving Averages', 'Volume')
    )
    
    # Add candlestick chart with enhanced colors
    fig.add_trace(
        go.Candlestick(
            x=df["Date"],
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price",
            increasing_line_color='#26a69a',  # Green for bullish
            decreasing_line_color='#ef5350',   # Red for bearish
            increasing_fillcolor='#26a69a',
            decreasing_fillcolor='#ef5350',
            line=dict(width=1.5),
            whiskerwidth=0.8,
            
        ),
        row=1, col=1
    )
    
    # Add Moving Averages if available
    if "MA20" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["MA20"],
                name="MA20",
                line=dict(color='#ff9800', width=2),
                opacity=0.8
            ),
            row=1, col=1
        )
    
    if "MA50" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["MA50"],
                name="MA50",
                line=dict(color='#2196f3', width=2),
                opacity=0.8
            ),
            row=1, col=1
        )
    
    # Add VWAP if available
    if "VWAP" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["VWAP"],
                name="VWAP",
                line=dict(color='#9c27b0', width=2, dash='dot'),
                opacity=0.8
            ),
            row=1, col=1
        )
    
    # Add Volume bars with color based on price direction
    # More efficient: use vectorized operation
    volume_colors = ['#26a69a' if close >= open_price 
                     else '#ef5350' 
                     for close, open_price in zip(df["Close"], df["Open"])]
    
    fig.add_trace(
        go.Bar(
            x=df["Date"],
            y=df["Volume"],
            name="Volume",
            marker_color=volume_colors,
            opacity=0.7,
            marker_line_width=0
        ),
        row=2, col=1
    )
    
    # Add Volume MA if available
    if "Volume_MA20" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["Volume_MA20"],
                name="Vol MA20",
                line=dict(color='#ff9800', width=1.5),
                opacity=0.8
            ),
            row=2, col=1
        )
    
    # Add pattern annotations if provided and enabled
    # Add pattern markers if provided and enabled
    if show_patterns and patterns_df is not None and not patterns_df.empty:
        # Get recent patterns from the same dataframe scope as the chart
        recent_patterns = patterns_df[patterns_df['Date'].isin(df['Date'])].copy()
        
        if not recent_patterns.empty:
            # --- FILTERING LOGIC ---
            # 1. Score Filter: Remove low-impact patterns (Score = 1, like Doji)
            # 2. Trend Filter: Only show Bullish if > VWAP, Bearish if < MA50
            
            # Helper to check score
            def get_score(pat_name):
                return PATTERN_DESCRIPTIONS.get(pat_name, {}).get("score", 1)
            
            recent_patterns["Score"] = recent_patterns["Pattern"].apply(get_score)
            
            # Filter 1: Remove weak patterns
            strong_patterns = recent_patterns[recent_patterns["Score"] > 1]
            
            # Merge with indicators for Trend Filter
            # Ensure we have the necessary columns in df
            merge_cols = ['Date', 'Close']
            if "VWAP" in df.columns: merge_cols.append("VWAP")
            if "MA50" in df.columns: merge_cols.append("MA50")
            
            merged = strong_patterns.merge(df[merge_cols], on='Date', how='left')
            
            # Filter 2: separate and apply trend logic
            bullish_mask = (merged['Signal'] == 'Bullish')
            bearish_mask = (merged['Signal'] == 'Bearish')
            
            # Apply Trend Context (User Request: Bull > VWAP, Bear < MA50)
            if "VWAP" in df.columns:
                bullish_mask = bullish_mask & (merged['Close'] > merged['VWAP'])
                
            if "MA50" in df.columns:
                bearish_mask = bearish_mask & (merged['Close'] < merged['MA50'])
            
            bullish_filtered = merged[bullish_mask]
            bearish_filtered = merged[bearish_mask]
            
            # Trace for Bullish Patterns (Green Up Triangles)
            if not bullish_filtered.empty:
                # Get Low price for positioning (merge again or use what we have? we need Low)
                # Optimization: We only merged 'Close' above. Let's grab 'Low' in a mini-merge or map.
                # Actually simpler to just map it since dates are unique
                date_to_low = df.set_index('Date')['Low']
                bull_y = bullish_filtered['Date'].map(date_to_low) * 0.995 # Closer to candle
                
                fig.add_trace(
                    go.Scatter(
                        x=bullish_filtered['Date'],
                        y=bull_y,
                        mode='markers',
                        name='Bullish ▲', # Simplified Legend
                        marker=dict(
                            symbol='triangle-up',
                            size=10, # Smaller
                            color='rgba(0, 200, 83, 0.7)', # Transparent Green
                            line=dict(width=1, color='rgba(0, 100, 0, 0.5)')
                        ),
                        text=bullish_filtered['Pattern'],
                        customdata=np.stack((bullish_filtered['Signal'], bullish_filtered['Status']), axis=-1),
                        hovertemplate="<b>%{text}</b><br>Signal: %{customdata[0]}<br>Status: %{customdata[1]}<extra></extra>"
                    ),
                    row=1, col=1
                )

            # Trace for Bearish Patterns (Red Down Triangles)
            if not bearish_filtered.empty:
                date_to_high = df.set_index('Date')['High']
                bear_y = bearish_filtered['Date'].map(date_to_high) * 1.005 # Closer to candle
                
                fig.add_trace(
                    go.Scatter(
                        x=bearish_filtered['Date'],
                        y=bear_y,
                        mode='markers',
                        name='Bearish ▼', # Simplified Legend
                        marker=dict(
                            symbol='triangle-down',
                            size=10, # Smaller
                            color='rgba(213, 0, 0, 0.7)', # Transparent Red
                            line=dict(width=1, color='rgba(100, 0, 0, 0.5)')
                        ),
                        text=bearish_filtered['Pattern'],
                        customdata=np.stack((bearish_filtered['Signal'], bearish_filtered['Status']), axis=-1),
                        hovertemplate="<b>%{text}</b><br>Signal: %{customdata[0]}<br>Status: %{customdata[1]}<extra></extra>"
                    ),
                    row=1, col=1
                )
    
    # Update layout for better visibility
    fig.update_layout(
        title=dict(
            text="<b>Candlestick Chart with Technical Indicators</b>",
            y=0.98,
            x=0.5,
            xanchor='center',
            yanchor='top',
            font=dict(size=20, color="#1f1f1f")
        ),
        margin=dict(t=160, l=50, r=50, b=50),
        font=dict(color="black"),  # Force global font color to black
        height=750,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.08,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="rgba(0,0,0,0.2)",
            borderwidth=1,
            font=dict(color="black")
        ),
        plot_bgcolor='#ffffff',
        paper_bgcolor='#ffffff',
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            showspikes=True,
            spikecolor="grey",
            spikesnap="cursor",
            spikemode="across",
            spikethickness=1,
            title_font=dict(color="black"),
            tickfont=dict(color="black")
        ),
        yaxis=dict(
            title="Price",
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            side="right",
            title_font=dict(color="black"),
            tickfont=dict(color="black")
        ),
        yaxis2=dict(
            title="Volume",
            showgrid=True,
            gridcolor='rgba(128,128,128,0.1)',
            side="right",
            title_font=dict(color="black"),
            tickfont=dict(color="black")
        ),
        # Preserve user state (zoom, pan, etc.) on refresh
        uirevision='static' 
    )
    
    # Update x-axis for volume subplot
    fig.update_xaxes(
        showgrid=True,
        gridcolor='rgba(128,128,128,0.2)',
        row=2, col=1
    )
    
    # Ensure subplot titles are black
    fig.for_each_annotation(lambda a: a.update(font=dict(color="black")))
    
    # Customize hover template
    fig.update_traces(
        hovertemplate="<b>%{fullData.name}</b><br>" +
                      "Date: %{x}<br>" +
                      "Value: %{y:,.2f}<extra></extra>",
        row=1, col=1
    )
    
    # Update candlestick hover template
    fig.data[0].hovertemplate = (
        "<b>Price</b><br>" +
        "Date: %{x}<br>" +
        "Open: %{open:,.2f}<br>" +
        "High: %{high:,.2f}<br>" +
        "Low: %{low:,.2f}<br>" +
        "Close: %{close:,.2f}<extra></extra>"
    )
    
    # Ensure X-axis label is visible
    # Ensure X-axis label is visible
    fig.update_xaxes(title_text="Date", title_font=dict(color="black"), tickfont=dict(color="black"), row=2, col=1)

    return fig

def volume_analysis_chart(df):
    """
    Creates a dedicated volume analysis chart with MA20 and color-coded breakouts.
    """
    # Base volume bars
    colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(df['Close'], df['Open'])]
    
    # Highlight breakouts with a different border or distinct color if desired
    # For now, we stick to red/green but maybe add a marker for 'Breakout'
    
    fig = go.Figure()
    
    # Volume Bars
    fig.add_trace(go.Bar(
        x=df['Date'],
        y=df['Volume'],
        name='Volume',
        marker_color=colors,
        opacity=0.6
    ))
    
    # Volume MA
    if "Volume_MA20" in df.columns:
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['Volume_MA20'],
            name='Vol MA (20)',
            line=dict(color='#ffa726', width=2)
        ))
        
    # Breakout Markers
    if "Volume_Breakout" in df.columns:
        breakouts = df[df["Volume_Breakout"]]
        if not breakouts.empty:
            fig.add_trace(go.Scatter(
                x=breakouts['Date'],
                y=breakouts['Volume'] * 1.05,
                mode='markers',
                name='High Vol Breakout',
                marker=dict(symbol='star', size=10, color='purple')
            ))

    fig.update_layout(
        title="<b>Volume Analysis & Breakouts</b>",
        xaxis_title="Date",
        yaxis_title="Volume",
        template="plotly_white",
        height=400,
        legend=dict(orientation="h", y=1.1),
        uirevision='static'
    )
    return fig

def obv_chart(df):
    """
    Creates an On-Balance Volume (OBV) chart.
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # OBV Line
    fig.add_trace(
        go.Scatter(x=df['Date'], y=df['OBV'], name='OBV', line=dict(color='#7e57c2', width=2)),
        secondary_y=False
    )
    
    # Overlay Close Price for comparison
    fig.add_trace(
        go.Scatter(x=df['Date'], y=df['Close'], name='Price', line=dict(color='gray', width=1, dash='dot'), opacity=0.5),
        secondary_y=True
    )
    
    fig.update_layout(
        title="<b>On-Balance Volume (OBV) vs Price</b>",
        xaxis_title="Date",
        template="plotly_white",
        height=400,
        legend=dict(orientation="h", y=1.1),
        uirevision='static'
    )
    
    fig.update_yaxes(title_text="OBV", secondary_y=False)
    fig.update_yaxes(title_text="Price", secondary_y=True, showgrid=False)
    
    return fig

def volume_chart(df):
    fig = px.bar(df, x="Date", y="Volume", title="Trading Volume")
    fig.update_layout(uirevision='static')
    return fig

def close_trend(df):
    fig = px.line(df, x="Date", y="Close", title="Close Price Trend")
    fig.update_layout(uirevision='static')
    return fig