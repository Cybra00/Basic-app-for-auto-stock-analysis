# src/charts.py
import plotly.graph_objects as go
import plotly.express as px

def candlestick_chart(df):
    fig = go.Figure(data=[
        go.Candlestick(
            x=df["Date"],
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"]
        )
    ])
    fig.update_layout(title="Candlestick Chart")
    return fig

def volume_chart(df):
    return px.bar(df, x="Date", y="Volume", title="Trading Volume")

def close_trend(df):
    return px.line(df, x="Date", y="Close", title="Close Price Trend")