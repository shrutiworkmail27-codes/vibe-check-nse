import numpy as np
import pandas as pd
import requests
import yfinance as yf

def get_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "*/*",
    })
    return session

def fetch_indicator_suite(symbol: str, period: str = "6mo"):
    session = get_session()
    ticker = yf.Ticker(symbol, session=session)
    df = ticker.history(period=period, interval="1d")
    
    if df.empty:
        df = yf.download(symbol, period=period, interval="1d", progress=False, session=session)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

    if df.empty:
        return None, {}

    df = df.rename(columns={c: c.capitalize() for c in df.columns})

    # 1. RSI (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    # 2. Moving Averages
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA200'] = df['Close'].rolling(window=200).mean()

    # 3. MACD (12, 26, 9)
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

    # 4. Bollinger Bands (20, 2)
    df['BB_Std'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['SMA20'] + (df['BB_Std'] * 2)
    df['BB_Lower'] = df['SMA20'] - (df['BB_Std'] * 2)
    df['BB_Width'] = ((df['BB_Upper'] - df['BB_Lower']) / df['SMA20']) * 100

    # 5. Stochastic Oscillator (14, 3)
    low14 = df['Low'].rolling(14).min()
    high14 = df['High'].rolling(14).max()
    df['Stoch_K'] = 100 * ((df['Close'] - low14) / (high14 - low14 + 1e-9))
    df['Stoch_D'] = df['Stoch_K'].rolling(3).mean()

    # 6. Average True Range (ATR-14)
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    df['ATR'] = true_range.rolling(14).mean()

    latest = df.iloc[-1]
    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
    
    metrics = {
        "current_price": round(float(latest['Close']), 2),
        "rsi": round(float(latest['RSI']), 2) if not pd.isna(latest['RSI']) else 50.0,
        "macd": round(float(latest['MACD']), 2) if not pd.isna(latest['MACD']) else 0.0,
        "macd_signal": round(float(latest['MACD_Signal']), 2) if not pd.isna(latest['MACD_Signal']) else 0.0,
        "macd_hist": round(float(latest['MACD_Hist']), 2) if not pd.isna(latest['MACD_Hist']) else 0.0,
        "sma20": round(float(latest['SMA20']), 2) if not pd.isna(latest['SMA20']) else float(latest['Close']),
        "sma50": round(float(latest['SMA50']), 2) if not pd.isna(latest['SMA50']) else float(latest['Close']),
        "sma200": round(float(latest['SMA200']), 2) if not pd.isna(latest['SMA200']) else float(latest['Close']),
        "bb_upper": round(float(latest['BB_Upper']), 2) if not pd.isna(latest['BB_Upper']) else float(latest['Close']),
        "bb_lower": round(float(latest['BB_Lower']), 2) if not pd.isna(latest['BB_Lower']) else float(latest['Close']),
        "bb_width": round(float(latest['BB_Width']), 2) if not pd.isna(latest['BB_Width']) else 0.0,
        "stoch_k": round(float(latest['Stoch_K']), 2) if not pd.isna(latest['Stoch_K']) else 50.0,
        "stoch_d": round(float(latest['Stoch_D']), 2) if not pd.isna(latest['Stoch_D']) else 50.0,
        "atr": round(float(latest['ATR']), 2) if not pd.isna(latest['ATR']) else 0.0,
        "volume": int(latest['Volume']),
        "volume_surge": bool(latest['Volume'] > (avg_vol * 1.5)) if not pd.isna(avg_vol) else False
    }
    
    return df, metrics