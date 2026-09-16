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

st.title("⚡ vibe-check-nse")
st.caption("Institutional Equity Intelligence Terminal • FinBERT NLP • Technical Confluence • Fundamental Radar")

# 1. Top Institutional FII/DII Flow Bar
fii_dii = fetch_fii_dii_activity()
with st.container(border=True):
    col_date, col_fii, col_dii, col_bias = st.columns(4)
    col_date.metric("Institutional Date", fii_dii['date'])
    col_fii.metric("FII Net Flow (Cr)", f"₹{fii_dii['fii_net_crores']:,.2f}")
    col_dii.metric("DII Net Flow (Cr)", f"₹{fii_dii['dii_net_crores']:,.2f}")
    col_bias.metric("Smart Money Posture", fii_dii['institutional_sentiment'])

st.divider()

# 2. Stock Selection & Search
nse_df = load_all_nse_symbols()
stock_options = [f"{row['Symbol']} — {row['Company Name']}" for _, row in nse_df.iterrows()]

c_sel, c_cust = st.columns([3, 2])
with c_sel:
    default_idx = next((i for i, s in enumerate(stock_options) if "TCS" in s), 0)
    selected_option = st.selectbox("Search Nifty 500 Constituents", options=stock_options, index=default_idx)
    selected_ticker = selected_option.split(" — ")[0]
with c_cust:
    custom_input = st.text_input("Or Enter Any NSE Ticker Directly", placeholder="e.g. MAZDOCK, TATAMOTORS, SBIN")

target_input = custom_input.strip() if custom_input else selected_ticker
symbol, company_name = resolve_ticker(target_input, nse_df)

if symbol:
    with st.spinner(f"Aggregating live intelligence for {symbol}..."):
        df, tech = fetch_indicator_suite(symbol)
        fund = fetch_company_fundamentals(symbol)
        raw_news = fetch_targeted_news(company_name, max_items=12)
        analyzed_news = analyze_sentiment(raw_news)
        confluence = calculate_confluence(analyzed_news, tech)

    if df is None:
        st.error(f"Could not load market data for {symbol}. Check the symbol.")
    else:
        # Price Action Calculation
        ltp = tech['current_price']
        prev_close = fund['prev_close'] or ltp
        chg = ltp - prev_close
        chg_pct = (chg / prev_close) * 100 if prev_close else 0.0

        range_52w = fund['high_52w'] - fund['low_52w']
        pct_52w = ((ltp - fund['low_52w']) / range_52w * 100) if range_52w > 0 else 50.0
        pct_52w = max(0.0, min(100.0, pct_52w))

        # 3. EXECUTIVE LIVE PRICE CARD (Native Bordered Container)
        with st.container(border=True):
            head_left, head_right = st.columns([3, 2])
            with head_left:
                st.subheader(fund['short_name'])
                st.caption(f"**{symbol}** • {fund['sector']} • {fund['industry']}")
            with head_right:
                st.metric(
                    label="Current LTP",
                    value=f"₹{ltp:,.2f}",
                    delta=f"{'+' if chg >= 0 else ''}{chg:.2f} ({chg_pct:+.2f}%) Today"
                )

            st.divider()

            b1, b2, b3, b4 = st.columns(4)
            b1.metric("Day Range", f"₹{fund['day_low']:,.2f} — ₹{fund['day_high']:,.2f}")
            b2.metric("52-Week Range", f"₹{fund['low_52w']:,.2f} — ₹{fund['high_52w']:,.2f}", delta=f"{pct_52w:.1f}% from 52W Low")
            b3.metric("Volume", f"{tech['volume'] / 100000:.2f} Lakhs", delta="⚡ Volume Surge" if tech['volume_surge'] else "Normal")
            b4.metric("Market Cap", f"₹{fund['market_cap_cr']:,.1f} Cr")

        # 4. CONFLUENCE STATUS BAR
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("FinBERT News Vibe", f"{confluence['sentiment_score']}/100", delta=f"{confluence['raw_mean']:+.2f} Polar Bias")
        s2.metric("RSI (14)", tech['rsi'], delta="Overbought" if tech['rsi'] > 70 else ("Oversold" if tech['rsi'] < 30 else "Balanced"))
        s3.metric("MACD Crossover", "Bullish" if tech['macd'] > tech['macd_signal'] else "Bearish", delta=f"{tech['macd_hist']:+.2f} Hist")
        s4.metric("Confluence Signal", confluence['verdict'])

        st.divider()

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
            st.subheader("🏛️ Complete Balance Sheet & Valuation Health")

            st.write("##### 1. Valuation Ratios & Pricing Multiples")
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

            st.write("---")
            st.write("##### 2. Operating Margins & Profitability Returns")
            p1, p2, p3, p4 = st.columns(4)
            p1.metric("Operating Margin", f"{fund['operating_margin']}%")
            p2.metric("Net Profit Margin", f"{fund['profit_margin']}%")
            p3.metric("Return on Equity (ROE)", f"{fund['roe']}%")
            p4.metric("Return on Assets (ROA)", f"{fund['roa']}%")

            st.write("---")
            st.write("##### 3. Cash Position, Debt & Solvency")
            b1, b2, b3, b4 = st.columns(4)
            b1.metric("Total Revenue (TTM)", f"₹{fund['total_revenue_cr']:,.1f} Cr")
            b2.metric("Free Cash Flow (FCF)", f"₹{fund['free_cash_flow_cr']:,.1f} Cr")
            b3.metric("Total Debt", f"₹{fund['total_debt_cr']:,.1f} Cr")
            b4.metric("Debt-to-Equity", fund['debt_to_equity'], delta="Low Debt" if fund['debt_to_equity'] < 0.5 else "High Debt", delta_color="inverse")

            b5, b6, b7, b8 = st.columns(4)
            b5.metric("Total Cash Reserves", f"₹{fund['total_cash_cr']:,.1f} Cr")
            b6.metric("Current Ratio", fund['current_ratio'])
            b7.metric("Quick Ratio", fund['quick_ratio'])
            b8.metric("Operating EBITDA", f"₹{fund['ebitda_cr']:,.1f} Cr")

        # TAB 3: BROKERAGE TARGETS WITH SOURCE LINKS
        with tab_analysts:
            st.subheader("🎯 Institutional Brokerage Targets & Consensus")
            if fund['target_mean_price'] > 0:
                upside_mean = ((fund['target_mean_price'] - ltp) / ltp) * 100
                top1, top2, top3 = st.columns(3)
                top1.metric("Consensus Mean Target", f"₹{fund['target_mean_price']}", delta=f"{upside_mean:+.1f}% Return")
                top2.metric("Target High / Low", f"₹{fund['target_high_price']} / ₹{fund['target_low_price']}")
                top3.metric("Consensus Action", fund['recommendation'], help=f"Covered by {fund['num_analysts']} analyst desks")

            st.write("##### Brokerage Specific Target Cards")
            reports = fetch_brokerage_reports(company_name, symbol, fund['target_mean_price'], ltp)
            for r in reports:
                with st.container(border=True):
                    rc1, rc2 = st.columns([3, 2])
                    with rc1:
                        st.markdown(f"### {r['broker']}")
                        st.caption(f"**Rating:** {r['rating']} • **Horizon:** {r['timeframe']}")
                    with rc2:
                        st.metric(
                            label=f"Projected Target (Upside: {r['upside']:+.1f}%)",
                            value=f"₹{r['target']:,.1f}",
                            delta=f"{r['upside']:+.1f}% Expected"
                        )
                        st.markdown(f"[🔍 View Research Note & Source ↗]({r['link']})")

        # TAB 4: ADVANCED INDICATORS TERMINAL
        with tab_indicators:
            st.subheader("⚡ Advanced Indicator & Momentum Dashboard")
            i1, i2, i3 = st.columns(3)
            with i1:
                with st.container(border=True):
                    st.write("**Relative Strength Index (RSI-14)**")
                    st.progress(min(100, int(tech['rsi'])))
                    st.metric("RSI Value", tech['rsi'])
                    st.caption("🔥 Overbought" if tech['rsi'] > 70 else ("❄️ Oversold" if tech['rsi'] < 30 else "✅ Balanced Momentum"))

            with i2:
                with st.container(border=True):
                    st.write("**Stochastic Oscillator (14, 3)**")
                    st.progress(min(100, int(tech['stoch_k'])))
                    st.metric("Stochastic %K", f"{tech['stoch_k']}", delta=f"%D: {tech['stoch_d']}")
                    st.caption("Bullish Crossover" if tech['stoch_k'] > tech['stoch_d'] else "Bearish Crossover")

            with i3:
                with st.container(border=True):
                    st.write("**Volatility & ATR (14-Day)**")
                    st.metric("Average True Range (ATR)", f"₹{tech['atr']}")
                    st.caption(f"Bollinger Band Width: **{tech['bb_width']:.2f}%**")

            st.write("##### Moving Average Confluence Matrix")
            ma_df = pd.DataFrame([
                {"Moving Average": "20-Day SMA (Short-Term)", "Value": f"₹{tech['sma20']}", "Price Position": "Above SMA" if ltp > tech['sma20'] else "Below SMA", "Bias": "BULLISH" if ltp > tech['sma20'] else "BEARISH"},
                {"Moving Average": "50-Day SMA (Intermediate)", "Value": f"₹{tech['sma50']}", "Price Position": "Above SMA" if ltp > tech['sma50'] else "Below SMA", "Bias": "BULLISH" if ltp > tech['sma50'] else "BEARISH"},
                {"Moving Average": "200-Day SMA (Long-Term Trend)", "Value": f"₹{tech['sma200']}", "Price Position": "Above SMA" if ltp > tech['sma200'] else "Below SMA", "Bias": "BULLISH" if ltp > tech['sma200'] else "BEARISH"},
            ])
            st.dataframe(ma_df, use_container_width=True, hide_index=True)

        # TAB 5: RECENT CLASSIFIED NEWS
        with tab_news:
            st.subheader("📰 Recent Press Coverage (Last 7 Days)")
            np1, np2, np3 = st.columns(3)
            np1.metric("Positive Headlines", confluence['positive_count'])
            np2.metric("Neutral Headlines", confluence['neutral_count'])
            np3.metric("Negative Headlines", confluence['negative_count'])

            for item in analyzed_news:
                event_cat = classify_event(item["title"])
                with st.container(border=True):
                    st.markdown(f"##### [{item['title']}]({item['link']})")
                    st.caption(f"🏷️ `{event_cat}` • **{item['source']}** • {item['published']} • **[{item['label']}] ({item['score']:+.2f})**")

        # TAB 6: AI NEWS DIGEST
        with tab_ai:
            st.subheader("🧠 FinBERT Catalyst Breakdown")
            if analyzed_news:
                pos_h = [n['title'] for n in analyzed_news if n['label'] == 'POSITIVE']
                neg_h = [n['title'] for n in analyzed_news if n['label'] == 'NEGATIVE']

                ai_c1, ai_c2 = st.columns(2)
                with ai_c1:
                    with st.container(border=True):
                        st.markdown("##### 🟢 Bullish Triggers")
                        if pos_h:
                            for h in pos_h[:4]:
                                st.write(f"- {h}")
                        else:
                            st.write("No distinct positive catalysts detected in the 7-day window.")
                with ai_c2:
                    with st.container(border=True):
                        st.markdown("##### 🔴 Friction & Headwinds")
                        if neg_h:
                            for h in neg_h[:4]:
                                st.write(f"- {h}")
                        else:
                            st.write("No major negative headwinds reported in recent press.")
            else:
                st.info("Insufficient recent news data to generate synthesis.")