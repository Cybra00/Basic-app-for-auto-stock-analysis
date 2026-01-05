# src/charts.py
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

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
            whiskerwidth=0.8
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
    
    # Add pattern annotations if provided and enabled
    if show_patterns and patterns_df is not None and not patterns_df.empty:
        # Get recent patterns for annotation - INCREASED LIMIT for visibility
        recent_patterns = patterns_df.tail(50)  # Increased from 15 to 50
        
        annotations = []
        for _, pattern in recent_patterns.iterrows():
            date = pattern["Date"]
            pattern_name = pattern["Pattern"]
            signal = pattern["Signal"]
            
            # Find the index in df for this date
            date_mask = df["Date"] == date
            if date_mask.any():
                idx = df[date_mask].index[0]
                high_price = df.iloc[idx]["High"]
                low_price = df.iloc[idx]["Low"]
                
                # Color based on signal
                if signal == "Bullish":
                    color = "#00c853"  # Brighter green
                    y_pos = low_price * 0.985  # Below the candle for bullish
                    ay_offset = 40  # Arrow points UP
                    symbol_arrow = 1  # Arrow pointing up
                    anchor = "top"
                elif signal == "Bearish":
                    color = "#d50000"  # Brighter red
                    y_pos = high_price * 1.015  # Above the candle for bearish
                    ay_offset = 40  # Arrow points DOWN
                    symbol_arrow = 5 # Arrow pointing down
                    anchor = "bottom"
                else:
                    color = "#ffab00" # Amber
                    y_pos = high_price * 1.015
                    ay_offset = 40
                    anchor = "bottom"
                
                # Create a more visible annotation
                annotations.append(
                    dict(
                        x=date,
                        y=y_pos,
                        text=f"<b>{pattern_name}</b>",
                        showarrow=True,
                        arrowhead=2,
                        arrowcolor=color,
                        bgcolor="rgba(255, 255, 255, 0.7)", # Semi-transparent background
                        bordercolor=color,
                        borderwidth=2,
                        font=dict(color="black", size=11, family="Arial Black"),
                        arrowwidth=2.5,  # Thicker arrow
                        arrowsize=1.5,   # Larger arrow head
                        ax=0,
                        ay=-ay_offset if signal == "Bullish" else -ay_offset # Adjust based on position
                    )
                )
        
        fig.update_layout(annotations=annotations)
    
    # Update layout for better visibility
    fig.update_layout(
        title=dict(
            text="<b>Candlestick Chart with Technical Indicators</b>",
            x=0.5,
            font=dict(size=20, color="#1f1f1f")
        ),
        height=700,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="rgba(0,0,0,0.2)",
            borderwidth=1
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
            spikethickness=1
        ),
        yaxis=dict(
            title="Price",
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            side="right"
        ),
        yaxis2=dict(
            title="Volume",
            showgrid=True,
            gridcolor='rgba(128,128,128,0.1)',
            side="right"
        )
    )
    
    # Update x-axis for volume subplot
    fig.update_xaxes(
        showgrid=True,
        gridcolor='rgba(128,128,128,0.2)',
        row=2, col=1
    )
    
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
    
    return fig

def volume_chart(df):
    return px.bar(df, x="Date", y="Volume", title="Trading Volume")

def close_trend(df):
    return px.line(df, x="Date", y="Close", title="Close Price Trend")