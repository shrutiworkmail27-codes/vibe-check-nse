import plotly.graph_objects as go
import streamlit as st
from data_fetcher import fetch_stock_technicals, fetch_targeted_news, resolve_ticker
from scorer import calculate_confluence
from sentiment_engine import analyze_sentiment

st.set_page_config(page_title="vibe-check-nse", layout="wide")
st.title("💅 vibe-check-nse")
st.caption("Dalal Street runs on 90% vibes and 10% fundamentals. FinBERT news sentiment meets RSI reality checks.")

col_search, _ = st.columns([2, 3])
with col_search:
    user_ticker = st.text_input("Enter NSE Ticker or Company Name", value="TATAMOTORS").strip()

if user_ticker:
    symbol, company_name = resolve_ticker(user_ticker)
    
    with st.spinner(f"Analyzing {company_name} ({symbol})..."):
        df, technicals = fetch_stock_technicals(symbol)
        raw_news = fetch_targeted_news(company_name, max_items=12)
        analyzed_news = analyze_sentiment(raw_news)
        confluence = calculate_confluence(analyzed_news, technicals)

    if df is None:
        st.error(f"Could not load market data for {symbol}. Check the symbol.")
    else:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("LTP", f"₹{technicals['current_price']}")
        m2.metric("RSI (14)", technicals['rsi'])
        m3.metric("Sentiment Score", f"{confluence['sentiment_score']}/100")
        m4.metric("Confluence Verdict", confluence['verdict'])

        st.divider()

        tab1, tab2 = st.tabs(["📊 Technical Confluence", "📰 Sentiment Breakdown"])

        with tab1:
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'], name='OHLC'
            ))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='orange', width=1.5), name='SMA 20'))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='blue', width=1.5), name='SMA 50'))
            fig.update_layout(height=450, margin=dict(l=20, r=20, t=20, b=20), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            s1, s2, s3 = st.columns(3)
            s1.success(f"Positive: {confluence['positive_count']}")
            s2.warning(f"Neutral: {confluence['neutral_count']}")
            s3.error(f"Negative: {confluence['negative_count']}")

            st.write("### Latest Headlines & Scores")
            for item in analyzed_news:
                color = "green" if item["label"] == "POSITIVE" else "red" if item["label"] == "NEGATIVE" else "gray"
                st.markdown(
                    f"**[:link:]({item['link']}) {item['title']}**  \n"
                    f"*{item['source']} • {item['published']}* — "
                    f"<span style='color:{color}; font-weight:bold;'>[{item['label']}] (Score: {item['score']})</span>",
                    unsafe_allow_html=True
                )