import numpy as np

def calculate_confluence(analyzed_news: list[dict], technicals: dict):
    if not analyzed_news:
        return {"sentiment_score": 50, "verdict": "NO DATA", "confidence": "0%"}

    scores = [a["score"] for a in analyzed_news]
    avg_score = float(np.mean(scores))
    base_sentiment = round((avg_score + 1.0) * 50, 1)

    rsi = technicals.get("rsi", 50)

    if base_sentiment >= 60:
        if rsi > 70:
            verdict = "BULLISH (OVERBOUGHT - EXERCISE CAUTION)"
        else:
            verdict = "STRONG BUY / BULLISH"
    elif base_sentiment <= 40:
        if rsi < 30:
            verdict = "BEARISH (OVERSOLD - WATCH FOR REVERSAL)"
        else:
            verdict = "BEARISH / SELL PRESSURE"
    else:
        verdict = "NEUTRAL / RANGEBOUND"

    return {
        "sentiment_score": base_sentiment,
        "raw_mean": round(avg_score, 2),
        "verdict": verdict,
        "positive_count": sum(1 for a in analyzed_news if a["label"] == "POSITIVE"),
        "negative_count": sum(1 for a in analyzed_news if a["label"] == "NEGATIVE"),
        "neutral_count": sum(1 for a in analyzed_news if a["label"] == "NEUTRAL"),
    }