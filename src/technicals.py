import numpy as np
import pandas as pd
import yfinance as yf

def fetch_indicator_suite(symbol: str, period="6mo"):
    stock = yf.Ticker(symbol)
    df = stock.history(period=period, interval="1d")
    if df.empty:
        return None, {}

    # RSI (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    # Moving Averages
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA200'] = df['Close'].rolling(window=200).mean()

    # MACD (12, 26, 9)
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # Bollinger Bands
    df['BB_Std'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['SMA20'] + (df['BB_Std'] * 2)
    df['BB_Lower'] = df['SMA20'] - (df['BB_Std'] * 2)

    latest = df.iloc[-1]
    metrics = {
        "current_price": round(float(latest['Close']), 2),
        "rsi": round(float(latest['RSI']), 2) if not pd.isna(latest['RSI']) else 50.0,
        "macd": round(float(latest['MACD']), 2) if not pd.isna(latest['MACD']) else 0.0,
        "macd_signal": round(float(latest['MACD_Signal']), 2) if not pd.isna(latest['MACD_Signal']) else 0.0,
        "sma20": round(float(latest['SMA20']), 2) if not pd.isna(latest['SMA20']) else latest['Close'],
        "sma50": round(float(latest['SMA50']), 2) if not pd.isna(latest['SMA50']) else latest['Close'],
        "volume": int(latest['Volume']),
        "volume_surge": bool(latest['Volume'] > df['Volume'].rolling(20).mean().iloc[-1] * 1.5)
    }
    return df, metrics