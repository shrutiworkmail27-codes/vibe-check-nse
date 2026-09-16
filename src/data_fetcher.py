import urllib.parse
from datetime import datetime
import feedparser
import pandas as pd
import yfinance as yf

TICKER_MAP = {
    "RELIANCE": ("RELIANCE.NS", "Reliance Industries"),
    "TCS": ("TCS.NS", "Tata Consultancy Services"),
    "INFY": ("INFY.NS", "Infosys"),
    "HDFCBANK": ("HDFCBANK.NS", "HDFC Bank"),
    "TATAMOTORS": ("TATAMOTORS.NS", "Tata Motors"),
    "SBIN": ("SBIN.NS", "State Bank of India"),
    "ITC": ("ITC.NS", "ITC Limited"),
}

def resolve_ticker(user_input: str):
    clean = user_input.strip().upper()
    if clean in TICKER_MAP:
        return TICKER_MAP[clean]
    return (f"{clean}.NS", clean)

def fetch_stock_technicals(symbol: str):
    stock = yf.Ticker(symbol)
    df = stock.history(period="6mo", interval="1d")
    if df.empty:
        return None, {}

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()

    latest = df.iloc[-1]
    metrics = {
        "current_price": round(latest['Close'], 2),
        "rsi": round(latest['RSI'], 2) if not pd.isna(latest['RSI']) else 50.0,
        "sma20": round(latest['SMA20'], 2) if not pd.isna(latest['SMA20']) else latest['Close'],
        "sma50": round(latest['SMA50'], 2) if not pd.isna(latest['SMA50']) else latest['Close'],
        "volume": int(latest['Volume']),
    }
    return df, metrics

def fetch_targeted_news(company_name: str, max_items: int = 15):
    query = urllib.parse.quote_plus(f"{company_name} share stock news")
    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)

    articles = []
    for entry in feed.entries[:max_items]:
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.get("published", datetime.now().strftime("%a, %d %b %Y")),
            "source": entry.get("source", {}).get("title", "Market News")
        })
    return articles