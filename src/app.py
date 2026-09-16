import plotly.graph_objects as go
import streamlit as st
from data_fetcher import fetch_targeted_news, resolve_ticker
from event_classifier import classify_event
from fii_dii import fetch_fii_dii_activity
from scorer import calculate_confluence
from sentiment_engine import analyze_sentiment
from technicals import fetch_indicator_suite

st.set_page_config(page_title="vibe-check-nse", layout="wide")
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

col_search, _ = st.columns([2, 3])
with col_search:
    user_ticker = st.text_input("Enter NSE Ticker or Company Name", value="TATAMOTORS").strip()

if user_ticker:
    symbol, company_name = resolve_ticker(user_ticker)
    
    with st.spinner(f"Running full vibe check on {company_name} ({symbol})..."):
        df, tech = fetch_indicator_suite(symbol)
        raw_news = fetch_targeted_news(company_name, max_items=12)
        analyzed_news = analyze_sentiment(raw_news)
        confluence = calculate_confluence(analyzed_news, tech)

    if df is None:
        st.error(f"Could not load market data for {symbol}. Check the symbol.")
    else:
        # Stock Summary Cards
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("LTP", f"₹{tech['current_price']}")
        m2.metric("RSI (14)", tech['rsi'])
        m3.metric("FinBERT Vibe Score", f"{confluence['sentiment_score']}/100")
        m4.metric("Confluence Signal", confluence['verdict'])

        st.divider()

        tab1, tab2, tab3 = st.tabs(["📊 Technical Confluence", "📰 Classified News & Vibes", "⚡ Indicator Stats"])

        with tab1:
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'], name='OHLC'
            ))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='orange', width=1.2), name='SMA 20'))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='blue', width=1.2), name='SMA 50'))
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], line=dict(color='gray', dash='dot'), name='BB Upper'))
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], line=dict(color='gray', dash='dot'), name='BB Lower'))
            fig.update_layout(height=480, margin=dict(l=20, r=20, t=20, b=20), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            s1, s2, s3 = st.columns(3)
            s1.success(f"Positive Vibes: {confluence['positive_count']}")
            s2.warning(f"Neutral Vibes: {confluence['neutral_count']}")
            s3.error(f"Negative Vibes: {confluence['negative_count']}")

            st.write("### Extracted Headlines & Event Classification")
            for item in analyzed_news:
                event_cat = classify_event(item["title"])
                color = "green" if item["label"] == "POSITIVE" else "red" if item["label"] == "NEGATIVE" else "gray"
                st.markdown(
                    f"**[:link:]({item['link']}) {item['title']}**  \n"
                    f"🏷️ `{event_cat}` • *{item['source']} • {item['published']}* — "
                    f"<span style='color:{color}; font-weight:bold;'>[{item['label']}] ({item['score']})</span>",
                    unsafe_allow_html=True
                )

        with tab3:
            st.json({
                "Current Price": tech["current_price"],
                "RSI (14)": tech["rsi"],
                "MACD": tech["macd"],
                "MACD Signal": tech["macd_signal"],
                "20-Day SMA": tech["sma20"],
                "50-Day SMA": tech["sma50"],
                "Volume Surge Detected": tech["volume_surge"],
            })