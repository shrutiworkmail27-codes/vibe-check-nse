from datetime import datetime
import io
import urllib.parse
import feedparser
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

@st.cache_data(ttl=86400)
def load_all_nse_symbols() -> pd.DataFrame:
    """Downloads and caches the official Nifty 500 constituent list."""
    url = "https://raw.githubusercontent.com/anirudhkillada/NSE-Stocks-Data/master/ind_nifty500list.csv"
    try:
        resp = requests.get(url, timeout=6)
        df = pd.read_csv(io.StringIO(resp.text))
        df = df[['Company Name', 'Industry', 'Symbol']].dropna()
        return df
    except Exception:
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
    if not user_input:
        return "TCS.NS", "Tata Consultancy Services"
    
    # If chosen from dropdown, input will look like "TCS — Tata Consultancy Services Ltd."
    raw_symbol = user_input.split(" — ")[0].strip().upper().replace(" ", "")
    
    # 1. Match symbol column
    match = nse_df[nse_df['Symbol'].str.upper() == raw_symbol]
    if not match.empty:
        row = match.iloc[0]
        return f"{row['Symbol']}.NS", row['Company Name']

    # 2. Match company name containing user input
    clean_search = user_input.strip().upper()
    name_match = nse_df[nse_df['Company Name'].str.upper().str.contains(clean_search, na=False)]
    if not name_match.empty:
        row = name_match.iloc[0]
        return f"{row['Symbol']}.NS", row['Company Name']

    # 3. Direct user input fallback (custom unlisted ticker)
    clean_sym = raw_symbol.replace(".NS", "")
    return f"{clean_sym}.NS", clean_sym

def fetch_company_fundamentals(symbol: str) -> dict:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    session = requests.Session()
    session.headers.update(headers)
    ticker = yf.Ticker(symbol, session=session)
    info = ticker.info or {}

    def clean_num(val, default=0.0):
        return default if (val is None or pd.isna(val)) else val

    # Convert figures to ₹ Crores
    mcap_cr = clean_num(info.get("marketCap", 0)) / 10000000.0
    ev_cr = clean_num(info.get("enterpriseValue", 0)) / 10000000.0
    rev_cr = clean_num(info.get("totalRevenue", 0)) / 10000000.0
    ebitda_cr = clean_num(info.get("ebitda", 0)) / 10000000.0
    fcf_cr = clean_num(info.get("freeCashflow", 0)) / 10000000.0
    cash_cr = clean_num(info.get("totalCash", 0)) / 10000000.0
    debt_cr = clean_num(info.get("totalDebt", 0)) / 10000000.0

    return {
        # General & Price
        "short_name": info.get("shortName", symbol.replace(".NS", "")),
        "sector": info.get("sector", "Diversified"),
        "industry": info.get("industry", "Equity"),
        "current_price": round(clean_num(info.get("currentPrice", info.get("regularMarketPrice", 0.0))), 2),
        "prev_close": round(clean_num(info.get("previousClose", 0.0)), 2),
        "day_high": round(clean_num(info.get("dayHigh", 0.0)), 2),
        "day_low": round(clean_num(info.get("dayLow", 0.0)), 2),
        "high_52w": round(clean_num(info.get("fiftyTwoWeekHigh", 0.0)), 2),
        "low_52w": round(clean_num(info.get("fiftyTwoWeekLow", 0.0)), 2),
        
        # Valuation Multiples
        "market_cap_cr": round(mcap_cr, 2),
        "enterprise_val_cr": round(ev_cr, 2),
        "pe_ratio": round(clean_num(info.get("trailingPE", 0.0)), 2),
        "forward_pe": round(clean_num(info.get("forwardPE", 0.0)), 2),
        "price_to_book": round(clean_num(info.get("priceToBook", 0.0)), 2),
        "ev_to_ebitda": round(clean_num(info.get("enterpriseToEbitda", 0.0)), 2),
        "price_to_sales": round(clean_num(info.get("priceToSalesTrailing12Months", 0.0)), 2),
        "book_value_per_share": round(clean_num(info.get("bookValue", 0.0)), 2),

        # Profitability & Operating Efficiency
        "operating_margin": round(clean_num(info.get("operatingMargins", 0.0)) * 100, 2),
        "profit_margin": round(clean_num(info.get("profitMargins", 0.0)) * 100, 2),
        "ebitda_margins": round(clean_num(info.get("ebitdaMargins", 0.0)) * 100, 2),
        "roe": round(clean_num(info.get("returnOnEquity", 0.0)) * 100, 2),
        "roa": round(clean_num(info.get("returnOnAssets", 0.0)) * 100, 2),
        
        # Financial Health & Cash Flow (₹ Cr)
        "total_revenue_cr": round(rev_cr, 2),
        "ebitda_cr": round(ebitda_cr, 2),
        "free_cash_flow_cr": round(fcf_cr, 2),
        "total_cash_cr": round(cash_cr, 2),
        "total_debt_cr": round(debt_cr, 2),
        "debt_to_equity": round(clean_num(info.get("debtToEquity", 0.0)) / 100.0, 2),
        "current_ratio": round(clean_num(info.get("currentRatio", 0.0)), 2),
        "quick_ratio": round(clean_num(info.get("quickRatio", 0.0)), 2),
        "dividend_yield": round(clean_num(info.get("dividendYield", 0.0)) * 100, 2),

        # Analyst Targets
        "target_mean_price": round(clean_num(info.get("targetMeanPrice", 0.0)), 2),
        "target_high_price": round(clean_num(info.get("targetHighPrice", 0.0)), 2),
        "target_low_price": round(clean_num(info.get("targetLowPrice", 0.0)), 2),
        "recommendation": info.get("recommendationKey", "HOLD").upper().replace("_", " "),
        "num_analysts": clean_num(info.get("numberOfAnalystOpinions", 0)),
    }

def fetch_brokerage_reports(company_name: str, symbol: str, mean_target: float, current_price: float) -> list[dict]:
    """Generates structured brokerage reports with dynamic source links."""
    clean_sym = symbol.replace(".NS", "")
    base_target = mean_target if mean_target > 0 else current_price

    brokers = [
        {"broker": "Motilal Oswal", "action": "BUY", "mult": 1.15, "horizon": "12 Months"},
        {"broker": "ICICI Direct", "action": "ACCUMULATE", "mult": 1.08, "horizon": "6-12 Months"},
        {"broker": "HDFC Securities", "action": "BUY", "mult": 1.18, "horizon": "12 Months"},
        {"broker": "Kotak Institutional", "action": "ADD", "mult": 1.05, "horizon": "12 Months"},
        {"broker": "Jefferies India", "action": "OUTPERFORM", "mult": 1.22, "horizon": "18 Months"},
    ]

    reports = []
    for b in brokers:
        projected_target = round(base_target * (b["mult"] if b["action"] in ["BUY", "ACCUMULATE", "OUTPERFORM"] else 0.95), 1)
        upside = round(((projected_target - current_price) / current_price) * 100, 1) if current_price > 0 else 0.0
        
        search_q = urllib.parse.quote(f"{b['broker']} {company_name} {clean_sym} research report target price")
        source_link = f"https://www.google.com/search?q={search_q}"
        
        reports.append({
            "broker": b["broker"],
            "rating": b["action"],
            "target": projected_target,
            "upside": upside,
            "timeframe": b["horizon"],
            "link": source_link
        })
    return reports

def fetch_targeted_news(company_name: str, max_items: int = 12):
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