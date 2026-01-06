# src/charts.py
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np

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
    # Add pattern markers if provided and enabled
    if show_patterns and patterns_df is not None and not patterns_df.empty:
        # Get recent patterns from the same dataframe scope as the chart
        recent_patterns = patterns_df[patterns_df['Date'].isin(df['Date'])]
        
        if not recent_patterns.empty:
            # Separate patterns by signal for different markers
            bullish_patterns = recent_patterns[recent_patterns['Signal'] == 'Bullish']
            bearish_patterns = recent_patterns[recent_patterns['Signal'] == 'Bearish']
            
            # Trace for Bullish Patterns (Green Up Triangles)
            if not bullish_patterns.empty:
                # Align prices with the main dataframe to get accurate High/Low
                # We merge with df to get the Low price for positioning
                bull_merged = bullish_patterns.merge(df[['Date', 'Low']], on='Date', how='left')
                
                fig.add_trace(
                    go.Scatter(
                        x=bull_merged['Date'],
                        y=bull_merged['Low'] * 0.99, # Slightly below low
                        mode='markers',
                        name='Bullish Patterns',
                        marker=dict(
                            symbol='triangle-up',
                            size=12,
                            color='#00c853',
                            line=dict(width=1, color='white')
                        ),
                        text=bull_merged['Pattern'],

                        customdata=np.stack((bull_merged['Signal'], bull_merged['Status']), axis=-1),
                        hovertemplate="<b>%{text}</b><br>Signal: %{customdata[0]}<br>Status: %{customdata[1]}<extra></extra>"
                    ),
                    row=1, col=1
                )

            # Trace for Bearish Patterns (Red Down Triangles)
            if not bearish_patterns.empty:
                # Merge to get High price for positioning
                bear_merged = bearish_patterns.merge(df[['Date', 'High']], on='Date', how='left')
                
                fig.add_trace(
                    go.Scatter(
                        x=bear_merged['Date'],
                        y=bear_merged['High'] * 1.01, # Slightly above high
                        mode='markers',
                        name='Bearish Patterns',
                        marker=dict(
                            symbol='triangle-down',
                            size=12,
                            color='#d50000',
                            line=dict(width=1, color='white')
                        ),
                        text=bear_merged['Pattern'],
                        customdata=np.stack((bear_merged['Signal'], bear_merged['Status']), axis=-1),
                        hovertemplate="<b>%{text}</b><br>Signal: %{customdata[0]}<br>Status: %{customdata[1]}<extra></extra>"
                    ),
                    row=1, col=1
                )
    
    # Update layout for better visibility
    fig.update_layout(
        title=dict(
            text="<b>Candlestick Chart with Technical Indicators</b>",
            x=0.5,
            font=dict(size=20, color="#1f1f1f")
        ),
        font=dict(color="black"),  # Force global font color to black
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
        uirevision=True 
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

def volume_chart(df):
    return px.bar(df, x="Date", y="Volume", title="Trading Volume")

def close_trend(df):
    return px.line(df, x="Date", y="Close", title="Close Price Trend")