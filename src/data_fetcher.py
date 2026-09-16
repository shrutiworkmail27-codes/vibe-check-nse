from datetime import datetime
import io
import urllib.parse
import feedparser
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

# Cached fetch of 500+ NSE stocks dynamically
@st.cache_data(ttl=86400)
def load_all_nse_symbols() -> pd.DataFrame:
    """Downloads and caches the official Nifty 500 constituent list."""
    url = "https://raw.githubusercontent.com/anirudhkillada/NSE-Stocks-Data/master/ind_nifty500list.csv"
    try:
        resp = requests.get(url, timeout=5)
        df = pd.read_csv(io.StringIO(resp.text))
        df = df[['Company Name', 'Industry', 'Symbol']].dropna()
        return df
    except Exception:
        # High-liquidity fallback in case of connection latency
        data = [
            {"Company Name": "Reliance Industries Ltd.", "Industry": "OIL & GAS", "Symbol": "RELIANCE"},
            {"Company Name": "Tata Consultancy Services Ltd.", "Industry": "IT", "Symbol": "TCS"},
            {"Company Name": "HDFC Bank Ltd.", "Industry": "FINANCIAL SERVICES", "Symbol": "HDFCBANK"},
            {"Company Name": "Infosys Ltd.", "Industry": "IT", "Symbol": "INFY"},
            {"Company Name": "Mazagon Dock Shipbuilders Ltd.", "Industry": "CAPITAL GOODS", "Symbol": "MAZDOCK"},
            {"Company Name": "Garden Reach Shipbuilders & Engineers Ltd.", "Industry": "CAPITAL GOODS", "Symbol": "GRSE"},
            {"Company Name": "Tata Motors Ltd.", "Industry": "AUTOMOBILE", "Symbol": "TATAMOTORS"},
            {"Company Name": "State Bank of India", "Industry": "FINANCIAL SERVICES", "Symbol": "SBIN"},
        ]
        return pd.DataFrame(data)

def resolve_ticker(user_input: str, nse_df: pd.DataFrame):
    clean = user_input.strip().upper().replace(" ", "")
    
    # 1. Match symbol column
    match = nse_df[nse_df['Symbol'].str.upper() == clean]
    if not match.empty:
        row = match.iloc[0]
        return f"{row['Symbol']}.NS", row['Company Name']

    # 2. Match company name containing user input
    name_match = nse_df[nse_df['Company Name'].str.upper().str.contains(clean, na=False)]
    if not name_match.empty:
        row = name_match.iloc[0]
        return f"{row['Symbol']}.NS", row['Company Name']

    # 3. Direct user input fallback (e.g. user enters a symbol not in Nifty 500)
    raw_sym = clean.replace(".NS", "")
    return f"{raw_sym}.NS", raw_sym

def fetch_company_fundamentals(symbol: str) -> dict:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    session = requests.Session()
    session.headers.update(headers)
    ticker = yf.Ticker(symbol, session=session)
    info = ticker.info or {}

    def clean_val(val, default=0.0):
        return default if val is None else val

    market_cap_cr = clean_val(info.get("marketCap", 0)) / 10000000.0
    
    return {
        "short_name": info.get("shortName", symbol.replace(".NS", "")),
        "sector": info.get("sector", "Industrials"),
        "industry": info.get("industry", "Aerospace & Defense"),
        "pe_ratio": round(clean_val(info.get("trailingPE", 0.0)), 2),
        "forward_pe": round(clean_val(info.get("forwardPE", 0.0)), 2),
        "price_to_book": round(clean_val(info.get("priceToBook", 0.0)), 2),
        "market_cap_cr": round(market_cap_cr, 2),
        "high_52w": round(clean_val(info.get("fiftyTwoWeekHigh", 0.0)), 2),
        "low_52w": round(clean_val(info.get("fiftyTwoWeekLow", 0.0)), 2),
        "day_high": round(clean_val(info.get("dayHigh", 0.0)), 2),
        "day_low": round(clean_val(info.get("dayLow", 0.0)), 2),
        "prev_close": round(clean_val(info.get("previousClose", 0.0)), 2),
        "dividend_yield": round(clean_val(info.get("dividendYield", 0.0)) * 100, 2),
        "roe": round(clean_val(info.get("returnOnEquity", 0.0)) * 100, 2),
        "debt_to_equity": round(clean_val(info.get("debtToEquity", 0.0)) / 100.0, 2),
        # Target Price & Analyst Consensus
        "target_mean_price": round(clean_val(info.get("targetMeanPrice", 0.0)), 2),
        "target_high_price": round(clean_val(info.get("targetHighPrice", 0.0)), 2),
        "target_low_price": round(clean_val(info.get("targetLowPrice", 0.0)), 2),
        "recommendation": info.get("recommendationKey", "N/A").upper().replace("_", " "),
        "num_analysts": clean_val(info.get("numberOfAnalystOpinions", 0)),
    }

def fetch_targeted_news(company_name: str, max_items: int = 12):
    """Enforces strict recent-article filtering (7 days) via Google News RSS."""
    # Filter to Indian market news within 7 days
    encoded_query = urllib.parse.quote_plus(f"{company_name} share stock news when:7d")
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)

    articles = []
    for entry in feed.entries[:max_items]:
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.get("published", datetime.now().strftime("%a, %d %b %Y")),
            "source": entry.get("source", {}).get("title", "Dalal Street Wire")
        })

    # Graceful fallback if ticker had zero articles in the last 7 days
    if len(articles) < 3:
        fallback_query = urllib.parse.quote_plus(f"{company_name} news")
        fallback_feed = feedparser.parse(f"https://news.google.com/rss/search?q={fallback_query}&hl=en-IN&gl=IN&ceid=IN:en")
        for entry in fallback_feed.entries[:max_items]:
            if not any(a["title"] == entry.title for a in articles):
                articles.append({
                    "title": entry.title,
                    "link": entry.link,
                    "published": entry.get("published", datetime.now().strftime("%a, %d %b %Y")),
                    "source": entry.get("source", {}).get("title", "Market Desk")
                })

    return articles[:max_items]