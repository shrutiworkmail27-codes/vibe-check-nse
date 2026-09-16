import plotly.graph_objects as go
import streamlit as st
import pandas as pd
from data_fetcher import (
    load_all_nse_symbols,
    resolve_ticker,
    fetch_company_fundamentals,
    fetch_targeted_news,
)
from event_classifier import classify_event
from fii_dii import fetch_fii_dii_activity
from scorer import calculate_confluence
from sentiment_engine import analyze_sentiment
from technicals import fetch_indicator_suite

st.set_page_config(page_title="vibe-check-nse", layout="wide")

# Custom Dark Card Layout
st.markdown("""
<style>
    .card-container {
        background-color: #121820;
        border: 1px solid #1E293B;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
    }
    .metric-subtext {
        font-size: 13px;
        color: #94A3B8;
        margin-bottom: 4px;
    }
    .badge-pill {
        background-color: #064E3B;
        color: #34D399;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
    }
    .stat-box {
        background-color: #0B0F15;
        border: 1px solid #1E293B;
        border-radius: 8px;
        padding: 14px;
        text-align: left;
    }
</style>
""", unsafe_allow_html=True)

st.title("💅 vibe-check-nse")
st.caption("Dalal Street runs on 90% vibes and 10% fundamentals. FinBERT news sentiment meets RSI reality checks.")

# Top Institutional Flow Bar
fii_dii = fetch_fii_dii_activity()
with st.container():
    f1, f2, f3, f4 = st.columns(4)
    f1.metric("FII Net Flow (Cr)", f"₹{fii_dii['fii_net_crores']:,.2f}")
    f2.metric("DII Net Flow (Cr)", f"₹{fii_dii['dii_net_crores']:,.2f}")
    f3.metric("Smart Money Bias", fii_dii['institutional_sentiment'])
    f4.metric("Market Date", fii_dii['date'])

st.divider()

# Load all 500+ NSE Stocks for search/select
nse_df = load_all_nse_symbols()
stock_options = [f"{row['Symbol']} — {row['Company Name']}" for _, row in nse_df.iterrows()]

col_select, col_custom = st.columns([3, 2])
with col_select:
    default_idx = next((i for i, s in enumerate(stock_options) if "MAZDOCK" in s), 0)
    selected_option = st.selectbox("Select Any NSE 500 Stock", options=stock_options, index=default_idx)
    selected_ticker = selected_option.split(" — ")[0]
with col_custom:
    custom_input = st.text_input("Or Type Any Custom NSE Ticker / Symbol", placeholder="e.g. GRSE, COALINDIA, IREDA")

# Resolve priority (Custom input overrides selectbox if typed)
target_input = custom_input.strip() if custom_input else selected_ticker
symbol, company_name = resolve_ticker(target_input, nse_df)

if symbol:
    with st.spinner(f"Running intelligence pipeline on {company_name} ({symbol})..."):
        df, tech = fetch_indicator_suite(symbol)
        fund = fetch_company_fundamentals(symbol)
        raw_news = fetch_targeted_news(company_name, max_items=12)
        analyzed_news = analyze_sentiment(raw_news)
        confluence = calculate_confluence(analyzed_news, tech)

    if df is None:
        st.error(f"Could not load market data for {symbol}. Verify the ticker symbol.")
    else:
        # LIVE PRICE & FUNDAMENTAL BANNER CARD
        ltp = tech['current_price']
        prev_close = fund['prev_close'] or ltp
        chg = ltp - prev_close
        chg_pct = (chg / prev_close) * 100 if prev_close else 0.0

        range_52w = fund['high_52w'] - fund['low_52w']
        pct_52w = ((ltp - fund['low_52w']) / range_52w * 100) if range_52w > 0 else 50.0
        pct_52w = max(0.0, min(100.0, pct_52w))

        st.markdown(f"""
        <div class="card-container">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <span class="metric-subtext">📈 LIVE PRICE & METRICS</span>
                    <h2 style="margin: 2px 0 6px 0; font-size: 28px;">{fund['short_name']}</h2>
                    <span style="color: #64748B; font-weight: 500;">{symbol} • NSE</span>
                    <div style="margin-top: 8px;">
                        <span class="badge-pill">{pct_52w:.1f}% of 52W High</span>
                    </div>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-top: 20px;">
                <div class="stat-box">
                    <div class="metric-subtext">{symbol.replace('.NS', '')}</div>
                    <div style="font-size: 24px; font-weight: bold;">₹{ltp:,.2f}</div>
                    <div style="color: {'#34D399' if chg >= 0 else '#F87171'}; font-size: 13px; font-weight: 600;">
                        {'+' if chg >= 0 else ''}{chg:.2f} ({chg_pct:+.2f}%)
                    </div>
                </div>
                <div class="stat-box">
                    <div class="metric-subtext">DAY RANGE</div>
                    <div style="font-size: 17px; font-weight: 600; margin-top: 4px;">
                        ₹{fund['day_low']:,.2f} — ₹{fund['day_high']:,.2f}
                    </div>
                </div>
                <div class="stat-box">
                    <div class="metric-subtext">VOLUME</div>
                    <div style="font-size: 22px; font-weight: bold; margin-top: 2px;">
                        {tech['volume'] / 100000:.2f}L
                    </div>
                    <div style="font-size: 12px; color: {'#34D399' if tech['volume_surge'] else '#64748B'};">
                        {'⚡ Volume Surge' if tech['volume_surge'] else 'Normal Activity'}
                    </div>
                </div>
                <div class="stat-box">
                    <div class="metric-subtext">P/E RATIO</div>
                    <div style="font-size: 22px; font-weight: bold; margin-top: 2px;">
                        {fund['pe_ratio'] if fund['pe_ratio'] else 'N/A'}
                    </div>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 14px; font-size: 13px; color: #94A3B8;">
                <div>Sector: <b style="color: #F1F5F9;">{fund['sector']}</b></div>
                <div>Industry: <b style="color: #F1F5F9;">{fund['industry']}</b></div>
                <div>Market Cap: <b style="color: #F1F5F9;">₹{fund['market_cap_cr']:,.2f} Cr</b></div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 10px; font-size: 13px; color: #94A3B8;">
                <div>52W High: <b style="color: #F1F5F9;">₹{fund['high_52w']:,.2f}</b></div>
                <div>52W Low: <b style="color: #F1F5F9;">₹{fund['low_52w']:,.2f}</b></div>
                <div>D/E Ratio: <b style="color: {'#F87171' if fund['debt_to_equity'] > 2 else '#34D399'};">{fund['debt_to_equity']}</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # QUICK CONFLUENCE SUMMARY METRICS
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Current RSI (14)", tech['rsi'], delta="Overbought" if tech['rsi'] > 70 else ("Oversold" if tech['rsi'] < 30 else "Neutral zone"))
        m2.metric("FinBERT Vibe", f"{confluence['sentiment_score']}/100")
        m3.metric("Signal Bias", confluence['verdict'])
        m4.metric("MACD Status", "Bullish Crossover" if tech['macd'] > tech['macd_signal'] else "Bearish Crossover")

        st.divider()

        # 6 EXPANDED TABS
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Technical Chart",
            "📰 Recent News & Vibes",
            "⚡ Indicator Dashboard",
            "🎯 Analyst Price Targets",
            "🏛️ Fundamentals",
            "🧠 AI News Digest"
        ])

        with tab1:
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'], name='OHLC'
            ))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='orange', width=1.3), name='SMA 20'))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='deepskyblue', width=1.3), name='SMA 50'))
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], line=dict(color='rgba(255,255,255,0.3)', dash='dot'), name='BB Upper'))
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], line=dict(color='rgba(255,255,255,0.3)', dash='dot'), name='BB Lower'))
            fig.update_layout(height=480, template="plotly_dark", margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            s1, s2, s3 = st.columns(3)
            s1.success(f"Positive: {confluence['positive_count']}")
            s2.warning(f"Neutral: {confluence['neutral_count']}")
            s3.error(f"Negative: {confluence['negative_count']}")

            st.write("### Fresh Extracted Headlines (Last 7 Days)")
            for item in analyzed_news:
                event_cat = classify_event(item["title"])
                color = "#34D399" if item["label"] == "POSITIVE" else "#F87171" if item["label"] == "NEGATIVE" else "#94A3B8"
                st.markdown(
                    f"""
                    <div style="background-color: #0F172A; border-left: 4px solid {color}; padding: 12px; border-radius: 6px; margin-bottom: 10px;">
                        <a href="{item['link']}" target="_blank" style="color: #F8FAFC; text-decoration: none; font-weight: 600; font-size: 15px;">{item['title']}</a>
                        <div style="font-size: 12px; color: #94A3B8; margin-top: 4px;">
                            <span style="background: #1E293B; padding: 2px 6px; border-radius: 4px; color: #38BDF8;">{event_cat}</span> • 
                            <i>{item['source']}</i> • {item['published']} • 
                            <b style="color: {color};">[{item['label']}] ({item['score']:+.2f})</b>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        with tab3:
            st.write("### Technical Strength & Momentum Gauges")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("#### RSI (14)")
                st.progress(min(100, int(tech['rsi'])))
                st.caption(f"Score: **{tech['rsi']}** — {'🔥 Overbought' if tech['rsi'] > 70 else '❄️ Oversold' if tech['rsi'] < 30 else '✅ Balanced Momentum'}")

            with c2:
                st.markdown("#### MACD vs Signal")
                spread = round(tech['macd'] - tech['macd_signal'], 2)
                st.metric("MACD Spread", spread, delta="Bullish Divergence" if spread >= 0 else "Bearish Divergence")
                st.caption(f"MACD Line: {tech['macd']} | Signal Line: {tech['macd_signal']}")

            with c3:
                st.markdown("#### Trend Against Moving Averages")
                above_50 = ltp > tech['sma50']
                st.metric("50-Day Moving Avg", f"₹{tech['sma50']}", delta="Above (Bullish)" if above_50 else "Below (Bearish)")
                st.caption(f"20-Day SMA: ₹{tech['sma20']}")

        with tab4:
            st.write("### Institutional Analyst Consensus & Price Targets")
            if fund['target_mean_price'] > 0:
                upside = ((fund['target_mean_price'] - ltp) / ltp) * 100
                a1, a2, a3 = st.columns(3)
                a1.metric("Analyst Consensus Target", f"₹{fund['target_mean_price']}", delta=f"{upside:+.1f}% Expected Return")
                a2.metric("Target High / Low", f"₹{fund['target_high_price']} / ₹{fund['target_low_price']}")
                a3.metric("Consensus Recommendation", fund['recommendation'], help="Derived from tracked analyst opinions")
            else:
                st.info("No active institutional analyst coverage consensus reported for this ticker.")

        with tab5:
            st.write("### Valuation & Balance Sheet Health")
            fcol1, fcol2, fcol3 = st.columns(3)
            fcol1.metric("Trailing P/E", fund['pe_ratio'] if fund['pe_ratio'] else "N/A")
            fcol1.metric("Forward P/E", fund['forward_pe'] if fund['forward_pe'] else "N/A")
            fcol2.metric("Price-to-Book (P/B)", fund['price_to_book'])
            fcol2.metric("Return on Equity (ROE)", f"{fund['roe']}%")
            fcol3.metric("Debt-to-Equity Ratio", fund['debt_to_equity'])
            fcol3.metric("Dividend Yield", f"{fund['dividend_yield']}%")

        with tab6:
            st.write("### AI Headline Summary & Market Drivers")
            if analyzed_news:
                pos_headlines = [n['title'] for n in analyzed_news if n['label'] == 'POSITIVE']
                neg_headlines = [n['title'] for n in analyzed_news if n['label'] == 'NEGATIVE']
                
                col_bull, col_bear = st.columns(2)
                with col_bull:
                    st.markdown("#### 🟢 Bullish Narratives Driving Sentiment")
                    if pos_headlines:
                        for h in pos_headlines[:4]:
                            st.write(f"- {h}")
                    else:
                        st.write("No major positive catalysts identified in recent news.")
                with col_bear:
                    st.markdown("#### 🔴 Bearish Friction & Risks")
                    if neg_headlines:
                        for h in neg_headlines[:4]:
                            st.write(f"- {h}")
                    else:
                        st.write("No major negative friction detected in recent headlines.")
            else:
                st.info("Insufficient news flow to construct sentiment digest.")