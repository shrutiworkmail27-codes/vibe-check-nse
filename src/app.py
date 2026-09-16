import plotly.graph_objects as go
import streamlit as st
import pandas as pd
from data_fetcher import (
    load_all_nse_symbols,
    resolve_ticker,
    fetch_company_fundamentals,
    fetch_brokerage_reports,
    fetch_targeted_news,
)
from event_classifier import classify_event
from fii_dii import fetch_fii_dii_activity
from scorer import calculate_confluence
from sentiment_engine import analyze_sentiment
from technicals import fetch_indicator_suite

st.set_page_config(page_title="vibe-check-nse | Institutional Terminal", layout="wide")

# Modern High-Impact Fintech CSS Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
    }
    
    .stApp {
        background-color: #F8FAFC;
    }

    /* Hero Card Styling */
    .hero-card {
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 1px solid #E2E8F0;
        border-radius: 20px;
        padding: 28px 32px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.06), 0 8px 10px -6px rgba(15, 23, 42, 0.04);
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }

    .hero-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #0284C7, #38BDF8, #6366F1);
    }

    /* Interactive Stat Micro-Cards */
    .hero-stat-box {
        background: #FFFFFF;
        border: 1px solid #EEF2F6;
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    }

    .hero-stat-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(15, 23, 42, 0.06);
        border-color: #CBD5E1;
    }

    .stat-label {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #64748B;
        margin-bottom: 6px;
    }

    .stat-val {
        font-size: 20px;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.02em;
    }

    /* Range Progress Bar */
    .range-bar-track {
        width: 100%;
        height: 8px;
        background: #E2E8F0;
        border-radius: 9999px;
        position: relative;
        margin-top: 10px;
        margin-bottom: 4px;
        overflow: visible;
    }

    .range-bar-fill {
        height: 100%;
        background: linear-gradient(90deg, #38BDF8, #0284C7);
        border-radius: 9999px;
    }

    .range-indicator {
        position: absolute;
        top: -4px;
        width: 16px;
        height: 16px;
        background: #0284C7;
        border: 2px solid #FFFFFF;
        border-radius: 50%;
        box-shadow: 0 2px 6px rgba(2, 132, 199, 0.4);
        transform: translateX(-50%);
    }

    /* Standard Card Elevation */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 12px -2px rgba(15, 23, 42, 0.04) !important;
        padding: 16px 20px !important;
    }

    /* Badges */
    .pill-tag {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 600;
        background: #F1F5F9;
        color: #334155;
        border: 1px solid #E2E8F0;
        margin-right: 6px;
    }

    .badge-bullish {
        background: #DCFCE7;
        color: #15803D;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 12px;
        display: inline-block;
    }

    .badge-bearish {
        background: #FEE2E2;
        color: #B91C1C;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 12px;
        display: inline-block;
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
        padding: 6px 0;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important;
        padding: 8px 18px !important;
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        color: #475569 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
    }

    .stTabs [aria-selected="true"] {
        background-color: #0284C7 !important;
        color: #FFFFFF !important;
        border-color: #0284C7 !important;
        box-shadow: 0 4px 10px rgba(2, 132, 199, 0.25) !important;
    }
</style>
""", unsafe_allow_html=True)

# Header Title
st.title("⚡ vibe-check-nse")
st.markdown("<p style='color: #64748B; font-size: 14px; margin-top: -12px; font-weight: 500;'>Institutional Equity Terminal • FinBERT NLP • Technical Confluence • Fundamental Radar</p>", unsafe_allow_html=True)

# 1. Top Institutional FII/DII Status Bar
fii_dii = fetch_fii_dii_activity()
with st.container(border=True):
    col_date, col_fii, col_dii, col_bias = st.columns(4)
    col_date.metric("Market Session", fii_dii['date'])
    col_fii.metric("FII Net Flow", f"₹{fii_dii['fii_net_crores']:,.2f} Cr")
    col_dii.metric("DII Net Flow", f"₹{fii_dii['dii_net_crores']:,.2f} Cr")
    col_bias.metric("Institutional Bias", fii_dii['institutional_sentiment'])

st.write("")

# 2. Unified Single Search Bar (All NSE Companies & Symbols in One)
nse_df = load_all_nse_symbols()
stock_options = [f"{row['Symbol']} — {row['Company Name']}" for _, row in nse_df.iterrows()]

# Default to TCS
default_idx = next((i for i, s in enumerate(stock_options) if s.startswith("TCS —")), 0)

selected_stock = st.selectbox(
    "Search any NSE Company name or Symbol (e.g. TCS, Tata Motors, Mazagon, GRSE, HDFC)",
    options=stock_options,
    index=default_idx,
    help="Type any company name or ticker to filter through all listed NSE equities."
)

symbol, company_name = resolve_ticker(selected_stock, nse_df)

if symbol:
    with st.spinner(f"Aggregating real-time telemetry for {symbol}..."):
        df, tech = fetch_indicator_suite(symbol)
        fund = fetch_company_fundamentals(symbol)
        raw_news = fetch_targeted_news(company_name, max_items=12)
        analyzed_news = analyze_sentiment(raw_news)
        confluence = calculate_confluence(analyzed_news, tech)

    if df is None:
        st.error(f"Could not load market data for {symbol}. Verify the symbol.")
    else:
        # Price Action & Range Calculations
        ltp = tech['current_price']
        prev_close = fund['prev_close'] or ltp
        chg = ltp - prev_close
        chg_pct = (chg / prev_close) * 100 if prev_close else 0.0

        range_52w = fund['high_52w'] - fund['low_52w']
        pct_52w = ((ltp - fund['low_52w']) / range_52w * 100) if range_52w > 0 else 50.0
        pct_52w = max(0.0, min(100.0, pct_52w))

        # 3. INTERACTIVE HERO CARD
        st.markdown(f"""
        <div class="hero-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
                <div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <h2 style="margin: 0; color: #0F172A; font-weight: 800; font-size: 28px; letter-spacing: -0.02em;">{fund['short_name']}</h2>
                    </div>
                    <div style="margin-top: 8px;">
                        <span class="pill-tag" style="background: #0284C7; color: white; border: none; font-weight: 700;">{symbol}</span>
                        <span class="pill-tag">{fund['sector']}</span>
                        <span class="pill-tag">{fund['industry']}</span>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div class="stat-label" style="margin-bottom: 2px;">LIVE LAST TRADED PRICE</div>
                    <div style="font-size: 34px; font-weight: 900; color: #0F172A; letter-spacing: -0.03em;">₹{ltp:,.2f}</div>
                    <div style="font-size: 14px; font-weight: 700; color: {'#16A34A' if chg >= 0 else '#DC2626'}; margin-top: 2px;">
                        {'+' if chg >= 0 else ''}{chg:.2f} ({chg_pct:+.2f}%) Today
                    </div>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-top: 24px;">
                <div class="hero-stat-box">
                    <div class="stat-label">DAY RANGE</div>
                    <div class="stat-val" style="font-size: 17px;">₹{fund['day_low']:,.2f} — ₹{fund['day_high']:,.2f}</div>
                    <div style="font-size: 11px; color: #64748B; margin-top: 4px;">Spread: ₹{fund['day_high'] - fund['day_low']:.2f}</div>
                </div>
                <div class="hero-stat-box">
                    <div class="stat-label">52-WEEK RANGE ({pct_52w:.1f}%)</div>
                    <div class="stat-val" style="font-size: 17px;">₹{fund['low_52w']:,.2f} — ₹{fund['high_52w']:,.2f}</div>
                    <div class="range-bar-track">
                        <div class="range-bar-fill" style="width: {pct_52w}%;"></div>
                        <div class="range-indicator" style="left: {pct_52w}%;"></div>
                    </div>
                </div>
                <div class="hero-stat-box">
                    <div class="stat-label">VOLUME</div>
                    <div class="stat-val">{tech['volume'] / 100000:.2f} Lakhs</div>
                    <div style="font-size: 11px; font-weight: 700; color: {'#16A34A' if tech['volume_surge'] else '#64748B'}; margin-top: 4px;">
                        {'⚡ Volume Surge' if tech['volume_surge'] else 'Normal Activity'}
                    </div>
                </div>
                <div class="hero-stat-box">
                    <div class="stat-label">MARKET CAP</div>
                    <div class="stat-val">₹{fund['market_cap_cr']:,.1f} Cr</div>
                    <div style="font-size: 11px; color: #0284C7; font-weight: 600; margin-top: 4px;">P/E: {fund['pe_ratio'] if fund['pe_ratio'] else 'N/A'}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 4. CONFLUENCE SIGNAL BAR
        with st.container(border=True):
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("FinBERT Sentiment", f"{confluence['sentiment_score']}/100", delta=f"{confluence['raw_mean']:+.2f} Polar Bias")
            s2.metric("RSI (14)", tech['rsi'], delta="Overbought" if tech['rsi'] > 70 else ("Oversold" if tech['rsi'] < 30 else "Balanced"))
            s3.metric("MACD Status", "Bullish Cross" if tech['macd'] > tech['macd_signal'] else "Bearish Cross", delta=f"{tech['macd_hist']:+.2f} Hist")
            s4.metric("Algorithm Verdict", confluence['verdict'])

        st.write("")

        # 5. EXPANDED TABS
        tab_tech, tab_fund, tab_analysts, tab_indicators, tab_news, tab_ai = st.tabs([
            "📈 Technical Chart",
            "🏛️ Exhaustive Fundamentals",
            "🎯 Brokerage Price Targets",
            "⚡ Advanced Indicators",
            "📰 Classified 7-Day News",
            "🧠 AI News Digest"
        ])

        # TAB 1: CHART
        with tab_tech:
            with st.container(border=True):
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=df.index, open=df['Open'], high=df['High'],
                    low=df['Low'], close=df['Close'], name='OHLC'
                ))
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='#F59E0B', width=1.5), name='20 SMA'))
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='#0284C7', width=1.5), name='50 SMA'))
                fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], line=dict(color='#94A3B8', dash='dash'), name='Upper BB'))
                fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], line=dict(color='#94A3B8', dash='dash'), name='Lower BB'))
                fig.update_layout(
                    template="plotly_white",
                    height=520,
                    margin=dict(l=10, r=10, t=10, b=10),
                    xaxis_rangeslider_visible=False,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True)

        # TAB 2: EXHAUSTIVE FUNDAMENTALS
        with tab_fund:
            with st.container(border=True):
                st.markdown("<h4 style='color:#0F172A; font-weight:700;'>1. Valuation Ratios & Pricing Multiples</h4>", unsafe_allow_html=True)
                v1, v2, v3, v4 = st.columns(4)
                v1.metric("Trailing P/E (TTM)", fund['pe_ratio'] if fund['pe_ratio'] else "N/A")
                v2.metric("Forward P/E", fund['forward_pe'] if fund['forward_pe'] else "N/A")
                v3.metric("Price to Book (P/B)", fund['price_to_book'])
                v4.metric("EV / EBITDA", fund['ev_to_ebitda'] if fund['ev_to_ebitda'] else "N/A")

                v5, v6, v7, v8 = st.columns(4)
                v5.metric("Price to Sales (P/S)", fund['price_to_sales'])
                v6.metric("Book Value / Share", f"₹{fund['book_value_per_share']}")
                v7.metric("Enterprise Value", f"₹{fund['enterprise_val_cr']:,.1f} Cr")
                v8.metric("Dividend Yield", f"{fund['dividend_yield']}%")

            st.write("")
            with st.container(border=True):
                st.markdown("<h4 style='color:#0F172A; font-weight:700;'>2. Operating Margins & Profitability Returns</h4>", unsafe_allow_html=True)
                p1, p2, p3, p4 = st.columns(4)
                p1.metric("Operating Margin", f"{fund['operating_margin']}%")
                p2.metric("Net Profit Margin", f"{fund['profit_margin']}%")
                p3.metric("Return on Equity (ROE)", f"{fund['roe']}%")
                p4.metric("Return on Assets (ROA)", f"{fund['roa']}%")

            st.write("")
            with st.container(border=True):
                st.markdown("<h4 style='color:#0F172A; font-weight:700;'>3. Balance Sheet Solvency, Debt & Cash Flow</h4>", unsafe_allow_html=True)
                b1, b2, b3, b4 = st.columns(4)
                b1.metric("Total Revenue (TTM)", f"₹{fund['total_revenue_cr']:,.1f} Cr")
                b2.metric("Free Cash Flow (FCF)", f"₹{fund['free_cash_flow_cr']:,.1f} Cr")
                b3.metric("Total Debt", f"₹{fund['total_debt_cr']:,.1f} Cr")
                b4.metric("Debt-to-Equity", fund['debt_to_equity'], delta="Low Debt" if fund['debt_to_equity'] < 0.5 else "High Debt", delta_color="inverse")

                b5, b6, b7, b8 = st.columns(4)
                b5.metric("Cash Reserves", f"₹{fund['total_cash_cr']:,.1f} Cr")
                b6.metric("Current Ratio", fund['current_ratio'])
                b7.metric("Quick Ratio", fund['quick_ratio'])
                b8.metric("Operating EBITDA", f"₹{fund['ebitda_cr']:,.1f} Cr")

        # TAB 3: BROKERAGE TARGETS WITH SOURCE LINKS
        with tab_analysts:
            if fund['target_mean_price'] > 0:
                upside_mean = ((fund['target_mean_price'] - ltp) / ltp) * 100
                with st.container(border=True):
                    top1, top2, top3 = st.columns(3)
                    top1.metric("Consensus Mean Target", f"₹{fund['target_mean_price']}", delta=f"{upside_mean:+.1f}% Return")
                    top2.metric("Target High / Low", f"₹{fund['target_high_price']} / ₹{fund['target_low_price']}")
                    top3.metric("Consensus Action", fund['recommendation'], help=f"Covered by {fund['num_analysts']} analyst desks")

            st.markdown("<h4 style='color:#0F172A; font-weight:700; margin-top:16px;'>Institutional Research Desk Targets</h4>", unsafe_allow_html=True)
            reports = fetch_brokerage_reports(company_name, symbol, fund['target_mean_price'], ltp)
            for r in reports:
                badge_html = f"<span class='badge-bullish'>{r['rating']}</span>" if r['upside'] >= 0 else f"<span class='badge-bearish'>{r['rating']}</span>"
                with st.container(border=True):
                    rc1, rc2 = st.columns([3, 2])
                    with rc1:
                        st.markdown(f"<div style='font-size: 17px; font-weight: 800; color: #0F172A;'>{r['broker']} {badge_html}</div>", unsafe_allow_html=True)
                        st.caption(f"Time Horizon: **{r['timeframe']}**")
                    with rc2:
                        st.metric(
                            label="Target Price",
                            value=f"₹{r['target']:,.1f}",
                            delta=f"{r['upside']:+.1f}% Expected Return"
                        )
                        st.markdown(f"[🔍 View Research Source ↗]({r['link']})")

        # TAB 4: ADVANCED INDICATORS TERMINAL
        with tab_indicators:
            i1, i2, i3 = st.columns(3)
            with i1:
                with st.container(border=True):
                    st.metric("RSI (14-Day)", tech['rsi'])
                    st.progress(min(100, int(tech['rsi'])))
                    st.caption("🔥 Overbought" if tech['rsi'] > 70 else ("❄️ Oversold" if tech['rsi'] < 30 else "✅ Balanced Momentum"))

            with i2:
                with st.container(border=True):
                    st.metric("Stochastic %K", f"{tech['stoch_k']}", delta=f"%D: {tech['stoch_d']}")
                    st.progress(min(100, int(tech['stoch_k'])))
                    st.caption("Bullish Crossover" if tech['stoch_k'] > tech['stoch_d'] else "Bearish Crossover")

            with i3:
                with st.container(border=True):
                    st.metric("Average True Range (ATR)", f"₹{tech['atr']}")
                    st.caption(f"Bollinger Band Width: **{tech['bb_width']:.2f}%**")
                    st.caption("⚡ Band Squeeze Alert" if tech['bb_width'] < 10 else "Normal Volatility")

            st.write("")
            with st.container(border=True):
                st.markdown("<h4 style='color:#0F172A; font-weight:700;'>Moving Average Confluence Matrix</h4>", unsafe_allow_html=True)
                ma_df = pd.DataFrame([
                    {"Moving Average": "20-Day SMA (Short-Term)", "Value": f"₹{tech['sma20']}", "Price Position": "Above SMA" if ltp > tech['sma20'] else "Below SMA", "Bias": "BULLISH" if ltp > tech['sma20'] else "BEARISH"},
                    {"Moving Average": "50-Day SMA (Intermediate)", "Value": f"₹{tech['sma50']}", "Price Position": "Above SMA" if ltp > tech['sma50'] else "Below SMA", "Bias": "BULLISH" if ltp > tech['sma50'] else "BEARISH"},
                    {"Moving Average": "200-Day SMA (Long-Term Trend)", "Value": f"₹{tech['sma200']}", "Price Position": "Above SMA" if ltp > tech['sma200'] else "Below SMA", "Bias": "BULLISH" if ltp > tech['sma200'] else "BEARISH"},
                ])
                st.dataframe(ma_df, use_container_width=True, hide_index=True)

        # TAB 5: RECENT CLASSIFIED NEWS
        with tab_news:
            with st.container(border=True):
                np1, np2, np3 = st.columns(3)
                np1.metric("Positive Headlines", confluence['positive_count'])
                np2.metric("Neutral Headlines", confluence['neutral_count'])
                np3.metric("Negative Headlines", confluence['negative_count'])

            for item in analyzed_news:
                event_cat = classify_event(item["title"])
                is_pos = item["label"] == "POSITIVE"
                is_neg = item["label"] == "NEGATIVE"
                badge_html = "<span class='badge-bullish'>BULLISH</span>" if is_pos else ("<span class='badge-bearish'>BEARISH</span>" if is_neg else "<span class='pill-tag'>NEUTRAL</span>")

                with st.container(border=True):
                    st.markdown(f"<div style='font-size: 16px; font-weight: 700; color: #0F172A;'><a href='{item['link']}' target='_blank' style='text-decoration:none; color:#0F172A;'>{item['title']}</a></div>", unsafe_allow_html=True)
                    st.markdown(f"""
                    <div style='margin-top: 6px; font-size: 12px; color: #64748B;'>
                        <span class='pill-tag'>{event_cat}</span> • <b>{item['source']}</b> • {item['published']} • {badge_html} (Score: {item['score']:+.2f})
                    </div>
                    """, unsafe_allow_html=True)

        # TAB 6: AI NEWS DIGEST
        with tab_ai:
            if analyzed_news:
                pos_h = [n['title'] for n in analyzed_news if n['label'] == 'POSITIVE']
                neg_h = [n['title'] for n in analyzed_news if n['label'] == 'NEGATIVE']

                ai_c1, ai_c2 = st.columns(2)
                with ai_c1:
                    with st.container(border=True):
                        st.markdown("<h4 style='color: #15803D; font-weight: 800; margin-top: 0;'>🟢 Bullish Drivers</h4>", unsafe_allow_html=True)
                        if pos_h:
                            for h in pos_h[:4]:
                                st.markdown(f"- **{h}**")
                        else:
                            st.write("No distinct positive catalysts detected in the 7-day window.")
                with ai_c2:
                    with st.container(border=True):
                        st.markdown("<h4 style='color: #B91C1C; font-weight: 800; margin-top: 0;'>🔴 Downside Risks & Friction</h4>", unsafe_allow_html=True)
                        if neg_h:
                            for h in neg_h[:4]:
                                st.markdown(f"- **{h}**")
                        else:
                            st.write("No major negative headwinds reported in recent press.")
            else:
                st.info("Insufficient recent news data to generate synthesis.")