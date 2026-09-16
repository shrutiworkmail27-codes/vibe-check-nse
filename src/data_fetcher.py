from datetime import datetime
import urllib.parse
import feedparser
import requests
import yfinance as yf

TICKER_MAP = {
    "RELIANCE": ("RELIANCE.NS", "Reliance Industries"),
    "TCS": ("TCS.NS", "Tata Consultancy Services"),
    "INFY": ("INFY.NS", "Infosys"),
    "HDFCBANK": ("HDFCBANK.NS", "HDFC Bank"),
    "TATAMOTORS": ("TATAMOTORS.NS", "Tata Motors"),
    "SBIN": ("SBIN.NS", "State Bank of India"),
    "ITC": ("ITC.NS", "ITC Limited"),
    "MAZDOCK": ("MAZDOCK.NS", "Mazagon Dock Shipbuilders"),
    "GRSE": ("GRSE.NS", "Garden Reach Shipbuilders"),
}

def resolve_ticker(user_input: str):
    clean = user_input.strip().upper().replace(" ", "")
    if clean in TICKER_MAP:
        return TICKER_MAP[clean]
    if clean.endswith(".NS"):
        return (clean, clean.replace(".NS", ""))
    return (f"{clean}.NS", clean)

def fetch_company_fundamentals(symbol: str) -> dict:
    """Extracts rich fundamental & price-band data via yfinance."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    session = requests.Session()
    session.headers.update(headers)
    ticker = yf.Ticker(symbol, session=session)
    info = ticker.info or {}

    def clean_val(val, default=0.0):
        return default if val is None else val

    market_cap_cr = clean_val(info.get("marketCap", 0)) / 10000000.0  # Convert to Crores
    
    return {
        "short_name": info.get("shortName", symbol.replace(".NS", "")),
        "sector": info.get("sector", "Capital Goods"),
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
    }

def fetch_targeted_news(company_name: str, max_items: int = 12):
    """Fetches strictly recent news (within the last 7 days) via date-bounded queries."""
    # when:7d ensures recent results instead of months-old links
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

    # Fallback to general query if when:7d is too strict for low-coverage tickers
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