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

st.set_page_config(page_title="vibe-check-nse | Equity Intelligence Terminal", layout="wide")

# High-End Professional Light Theme Styling
st.markdown("""
<style>
    /* Main Background & Clean Font Hierarchy */
    .stApp {
        background-color: #F8FAFC;
        color: #0F172A;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Institutional Light Cards */
    .light-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 22px 26px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.03);
        margin-bottom: 20px;
    }

    .sub-box {
        background-color: #F1F5F9;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 14px 16px;
    }

    .metric-label {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
        margin-bottom: 4px;
    }

    .metric-value {
        font-size: 20px;
        font-weight: 800;
        color: #0F172A;
    }

    .tag-pill {
        background-color: #EEF2F6;
        color: #334155;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
        margin-right: 6px;
    }

    .badge-bull {
        background-color: #DCFCE7;
        color: #15803D;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 700;
    }

    .badge-bear {
        background-color: #FEE2E2;
        color: #B91C1C;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 700;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        color: #475569;
        font-weight: 600;
    }

    .stTabs [aria-selected="true"] {
        background-color: #0284C7 !important;
        color: #FFFFFF !important;
        border-color: #0284C7 !important;
    }
</style>
""", unsafe_allow_html=True)

# App Header
st.title("⚡ vibe-check-nse")
st.markdown("<p style='color: #475569; font-size: 14px; margin-top: -12px;'>Institutional Equity Terminal • FinBERT Sentiment • Multi-Indicator Confluence • Fundamental Radar</p>", unsafe_allow_html=True)

# 1. Top FII/DII Institutional Flow Bar
fii_dii = fetch_fii_dii_activity()
st.markdown(f"""
<div class="light-card" style="padding: 14px 20px; margin-bottom: 16px;">
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; align-items: center;">
        <div>
            <div class="metric-label">Institutional Date</div>
            <div style="font-weight: 700; color: #0F172A;">{fii_dii['date']}</div>
        </div>
        <div>
            <div class="metric-label">FII Net Cash Flow</div>
            <div style="font-weight: 800; color: {'#15803D' if fii_dii['fii_net_crores'] >= 0 else '#B91C1C'};">
                ₹{fii_dii['fii_net_crores']:,.2f} Cr
            </div>
        </div>
        <div>
            <div class="metric-label">DII Net Cash Flow</div>
            <div style="font-weight: 800; color: {'#15803D' if fii_dii['dii_net_crores'] >= 0 else '#B91C1C'};">
                ₹{fii_dii['dii_net_crores']:,.2f} Cr
            </div>
        </div>
        <div>
            <div class="metric-label">Smart Money Posture</div>
            <span class="{'badge-bull' if 'BUY' in fii_dii['institutional_sentiment'] else 'badge-bear'}">
                {fii_dii['institutional_sentiment']}
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 2. Stock Selection & Search
nse_df = load_all_nse_symbols()
stock_options = [f"{row['Symbol']} — {row['Company Name']}" for _, row in nse_df.iterrows()]

col_select, col_custom = st.columns([3, 2])
with col_select:
    default_idx = next((i for i, s in enumerate(stock_options) if "TCS" in s), 0)
    selected_option = st.selectbox("Search from Nifty 500 Constituents", options=stock_options, index=default_idx)
    selected_ticker = selected_option.split(" — ")[0]
with col_custom:
    custom_input = st.text_input("Or Enter Any NSE Ticker Directly", placeholder="e.g. MAZDOCK, TATAMOTORS, SBIN")

target_input = custom_input.strip() if custom_input else selected_ticker
symbol, company_name = resolve_ticker(target_input, nse_df)

if symbol:
    with st.spinner(f"Aggregating live institutional intelligence for {symbol}..."):
        df, tech = fetch_indicator_suite(symbol)
        fund = fetch_company_fundamentals(symbol)
        raw_news = fetch_targeted_news(company_name, max_items=12)
        analyzed_news = analyze_sentiment(raw_news)
        confluence = calculate_confluence(analyzed_news, tech)

    if df is None:
        st.error(f"Could not load market data for {symbol}. Check ticker symbol.")
    else:
        # Price Action Math
        ltp = tech['current_price']
        prev_close = fund['prev_close'] or ltp
        chg = ltp - prev_close
        chg_pct = (chg / prev_close) * 100 if prev_close else 0.0

        range_52w = fund['high_52w'] - fund['low_52w']
        pct_52w = ((ltp - fund['low_52w']) / range_52w * 100) if range_52w > 0 else 50.0
        pct_52w = max(0.0, min(100.0, pct_52w))

        # 3. EXECUTIVE LIVE PRICE CARD (Light Theme)
        st.markdown(f"""
        <div class="light-card">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #F1F5F9; padding-bottom: 12px;">
                <div>
                    <h2 style="margin: 0; font-size: 26px; font-weight: 800; color: #0F172A;">{fund['short_name']}</h2>
                    <div style="margin-top: 4px;">
                        <span class="tag-pill">{symbol}</span>
                        <span class="tag-pill">{fund['sector']}</span>
                        <span class="tag-pill">{fund['industry']}</span>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 32px; font-weight: 900; color: #0F172A;">₹{ltp:,.2f}</div>
                    <div style="font-weight: 700; font-size: 14px; color: {'#16A34A' if chg >= 0 else '#DC2626'};">
                        {'+' if chg >= 0 else ''}{chg:.2f} ({chg_pct:+.2f}%) Today
                    </div>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-top: 16px;">
                <div class="sub-box">
                    <div class="metric-label">Day Range</div>
                    <div style="font-weight: 700; font-size: 15px;">₹{fund['day_low']:,.2f} — ₹{fund['day_high']:,.2f}</div>
                </div>
                <div class="sub-box">
                    <div class="metric-label">52-Week Range</div>
                    <div style="font-weight: 700; font-size: 15px;">₹{fund['low_52w']:,.2f} — ₹{fund['high_52w']:,.2f}</div>
                    <div style="font-size: 11px; color: #0284C7; font-weight: 600; margin-top: 2px;">{pct_52w:.1f}% from low</div>
                </div>
                <div class="sub-box">
                    <div class="metric-label">Volume Activity</div>
                    <div style="font-weight: 700; font-size: 15px;">{tech['volume'] / 100000:.2f} Lakhs</div>
                    <div style="font-size: 11px; color: {'#16A34A' if tech['volume_surge'] else '#64748B'}; font-weight: 600;">
                        {'⚡ Volume Surge Detected' if tech['volume_surge'] else 'Normal Volume'}
                    </div>
                </div>
                <div class="sub-box">
                    <div class="metric-label">Market Capitalization</div>
                    <div style="font-weight: 700; font-size: 15px;">₹{fund['market_cap_cr']:,.2f} Cr</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 4. SIGNAL CONFLUENCE BAR
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("FinBERT News Vibe", f"{confluence['sentiment_score']}/100", delta=f"{confluence['raw_mean']:+.2f} Polar Bias")
        c2.metric("RSI (14)", tech['rsi'], delta="Overbought" if tech['rsi'] > 70 else ("Oversold" if tech['rsi'] < 30 else "Balanced"))
        c3.metric("MACD Crossover", "Bullish" if tech['macd'] > tech['macd_signal'] else "Bearish", delta=f"{tech['macd_hist']:+.2f} Hist")
        c4.metric("Confluence Verdict", confluence['verdict'])

        st.markdown("<br>", unsafe_allow_html=True)

        # 5. EXPANDED & EXHAUSTIVE TABS
        tab_tech, tab_fund, tab_analysts, tab_indicators, tab_news, tab_ai = st.tabs([
            "📈 Price & Technical Chart",
            "🏛️ Exhaustive Fundamentals",
            "🎯 Brokerage Price Targets",
            "⚡ Detailed Indicator Terminal",
            "📰 Classified 7-Day News",
            "🧠 AI Sentiment Executive Summary"
        ])

        # TAB 1: CHART
        with tab_tech:
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
                height=500,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis_rangeslider_visible=False,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)

        # TAB 2: EXHAUSTIVE FUNDAMENTALS
        with tab_fund:
            st.markdown("### 🏛️ Complete Fundamental & Balance Sheet Breakdown")
            
            st.markdown("#### 1. Valuation Ratios & Pricing Multiples")
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

            st.divider()

            st.markdown("#### 2. Operating Margins & Capital Return Efficiency")
            p1, p2, p3, p4 = st.columns(4)
            p1.metric("Operating Margin", f"{fund['operating_margin']}%")
            p2.metric("Net Profit Margin", f"{fund['profit_margin']}%")
            p3.metric("Return on Equity (ROE)", f"{fund['roe']}%")
            p4.metric("Return on Assets (ROA)", f"{fund['roa']}%")

            st.divider()

            st.markdown("#### 3. Balance Sheet Liquidity, Debt & Cash Position")
            b1, b2, b3, b4 = st.columns(4)
            b1.metric("Total Revenue (TTM)", f"₹{fund['total_revenue_cr']:,.1f} Cr")
            b2.metric("Free Cash Flow (FCF)", f"₹{fund['free_cash_flow_cr']:,.1f} Cr")
            b3.metric("Total Debt", f"₹{fund['total_debt_cr']:,.1f} Cr")
            b4.metric("Debt-to-Equity", fund['debt_to_equity'], delta="Low Debt" if fund['debt_to_equity'] < 0.5 else "High Leverage", delta_color="inverse")

            b5, b6, b7, b8 = st.columns(4)
            b5.metric("Total Cash Reserves", f"₹{fund['total_cash_cr']:,.1f} Cr")
            b6.metric("Current Ratio", fund['current_ratio'])
            b7.metric("Quick Ratio", fund['quick_ratio'])
            b8.metric("Operating EBITDA", f"₹{fund['ebitda_cr']:,.1f} Cr")

        # TAB 3: BROKERAGE TARGETS WITH SOURCE LINKS
        with tab_analysts:
            st.markdown("### 🎯 Institutional Brokerage Targets & Wall/Dalal Street Estimates")
            
            # Consensus Overview
            if fund['target_mean_price'] > 0:
                upside_mean = ((fund['target_mean_price'] - ltp) / ltp) * 100
                top1, top2, top3 = st.columns(3)
                top1.metric("Consensus Mean Target", f"₹{fund['target_mean_price']}", delta=f"{upside_mean:+.1f}% Return")
                top2.metric("Target High / Low", f"₹{fund['target_high_price']} / ₹{fund['target_low_price']}")
                top3.metric("Consensus Action", fund['recommendation'], help=f"Covered by {fund['num_analysts']} analyst desks")

            st.markdown("#### Broker-Specific Target Radar & Direct Research Reports")
            reports = fetch_brokerage_reports(company_name, symbol, fund['target_mean_price'], ltp)
            
            for r in reports:
                badge_style = "badge-bull" if r['upside'] >= 0 else "badge-bear"
                st.markdown(f"""
                <div class="light-card" style="padding: 16px 20px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="font-size: 16px; font-weight: 800; color: #0F172A;">{r['broker']}</span>
                            <span class="{badge_style}" style="margin-left: 10px;">{r['rating']}</span>
                            <div style="font-size: 12px; color: #64748B; margin-top: 4px;">Time Horizon: {r['timeframe']}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 20px; font-weight: 800; color: #0F172A;">₹{r['target']:,.1f}</div>
                            <div style="font-size: 13px; font-weight: 700; color: {'#16A34A' if r['upside'] >= 0 else '#DC2626'};">
                                {r['upside']:+.1f}% Target Upside
                            </div>
                            <div style="margin-top: 6px;">
                                <a href="{r['link']}" target="_blank" style="font-size: 12px; color: #0284C7; font-weight: 600; text-decoration: none;">
                                    🔍 View Research Note & Source ↗
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # TAB 4: DETAILED INDICATOR TERMINAL
        with tab_indicators:
            st.markdown("### ⚡ Advanced Indicator & Momentum Terminal")
            
            ind1, ind2, ind3 = st.columns(3)
            with ind1:
                st.markdown("""
                <div class="light-card">
                    <div class="metric-label">Relative Strength Index (RSI-14)</div>
                """, unsafe_allow_html=True)
                st.progress(min(100, int(tech['rsi'])))
                st.markdown(f"""
                    <div style="font-size: 22px; font-weight: 800; margin-top: 8px;">{tech['rsi']}</div>
                    <div style="font-size: 12px; font-weight: 600; color: {'#DC2626' if tech['rsi'] > 70 else '#16A34A' if tech['rsi'] < 30 else '#0284C7'};">
                        {'🔥 Overbought (Exhaustion Risk)' if tech['rsi'] > 70 else '❄️ Oversold (Accumulation Zone)' if tech['rsi'] < 30 else '✅ Neutral Momentum'}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with ind2:
                st.markdown("""
                <div class="light-card">
                    <div class="metric-label">Stochastic Oscillator (14, 3)</div>
                """, unsafe_allow_html=True)
                st.progress(min(100, int(tech['stoch_k'])))
                st.markdown(f"""
                    <div style="font-size: 22px; font-weight: 800; margin-top: 8px;">%K: {tech['stoch_k']} | %D: {tech['stoch_d']}</div>
                    <div style="font-size: 12px; font-weight: 600; color: #64748B;">
                        {'Bullish Fast Crossover' if tech['stoch_k'] > tech['stoch_d'] else 'Bearish Cross'}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with ind3:
                st.markdown("""
                <div class="light-card">
                    <div class="metric-label">Volatility & ATR (14-Day)</div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                    <div style="font-size: 22px; font-weight: 800; margin-top: 8px;">₹{tech['atr']}</div>
                    <div style="font-size: 12px; color: #64748B; margin-top: 4px;">
                        Bollinger Band Width: <b>{tech['bb_width']:.2f}%</b> ({'High Volatility' if tech['bb_width'] > 15 else 'Band Squeeze / Breakout Watch'})
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("#### Moving Average Confluence Table")
            ma_df = pd.DataFrame([
                {"Moving Average": "20-Day SMA (Short-Term)", "Value": f"₹{tech['sma20']}", "Price Position": "Above SMA" if ltp > tech['sma20'] else "Below SMA", "Bias": "BULLISH" if ltp > tech['sma20'] else "BEARISH"},
                {"Moving Average": "50-Day SMA (Intermediate)", "Value": f"₹{tech['sma50']}", "Price Position": "Above SMA" if ltp > tech['sma50'] else "Below SMA", "Bias": "BULLISH" if ltp > tech['sma50'] else "BEARISH"},
                {"Moving Average": "200-Day SMA (Long-Term Trend)", "Value": f"₹{tech['sma200']}", "Price Position": "Above SMA" if ltp > tech['sma200'] else "Below SMA", "Bias": "BULLISH" if ltp > tech['sma200'] else "BEARISH"},
            ])
            st.table(ma_df)

        # TAB 5: CLASSIFIED 7-DAY NEWS
        with tab_news:
            n_pos, n_neu, n_neg = st.columns(3)
            n_pos.success(f"Positive Signals: {confluence['positive_count']}")
            n_neu.info(f"Neutral Signals: {confluence['neutral_count']}")
            n_neg.error(f"Negative Signals: {confluence['negative_count']}")

            st.markdown("#### Verified Recent Coverage (Filtered to Last 7 Days)")
            for item in analyzed_news:
                event_cat = classify_event(item["title"])
                is_pos = item["label"] == "POSITIVE"
                is_neg = item["label"] == "NEGATIVE"
                border_col = "#16A34A" if is_pos else "#DC2626" if is_neg else "#94A3B8"
                badge_class = "badge-bull" if is_pos else "badge-bear" if is_neg else "tag-pill"

                st.markdown(f"""
                <div class="light-card" style="border-left: 5px solid {border_col}; padding: 14px 18px; margin-bottom: 12px;">
                    <a href="{item['link']}" target="_blank" style="color: #0F172A; text-decoration: none; font-weight: 700; font-size: 15px;">
                        {item['title']}
                    </a>
                    <div style="font-size: 12px; color: #64748B; margin-top: 6px;">
                        <span class="tag-pill">{event_cat}</span> • 
                        <b>{item['source']}</b> • {item['published']} • 
                        <span class="{badge_class}">[{item['label']}] (Score: {item['score']:+.2f})</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # TAB 6: AI SENTIMENT DIGEST
        with tab_ai:
            st.markdown("### 🧠 FinBERT News Synthesis & Qualitative Catalyst Matrix")
            if analyzed_news:
                pos_h = [n['title'] for n in analyzed_news if n['label'] == 'POSITIVE']
                neg_h = [n['title'] for n in analyzed_news if n['label'] == 'NEGATIVE']

                ai_c1, ai_c2 = st.columns(2)
                with ai_c1:
                    st.markdown("""
                    <div class="light-card" style="border-top: 4px solid #16A34A;">
                        <h4 style="color: #15803D; margin-top: 0;">🟢 Primary Bullish Triggers</h4>
                    """, unsafe_allow_html=True)
                    if pos_h:
                        for h in pos_h[:4]:
                            st.markdown(f"- {h}")
                    else:
                        st.write("No distinct positive catalysts detected in the 7-day window.")
                    st.markdown("</div>", unsafe_allow_html=True)

                with ai_c2:
                    st.markdown("""
                    <div class="light-card" style="border-top: 4px solid #DC2626;">
                        <h4 style="color: #B91C1C; margin-top: 0;">🔴 Downside Friction & Sentiment Drags</h4>
                    """, unsafe_allow_html=True)
                    if neg_h:
                        for h in neg_h[:4]:
                            st.markdown(f"- {h}")
                    else:
                        st.write("No major negative headwinds reported in recent press.")
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("Insufficient recent news data to generate synthesis.")