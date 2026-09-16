import streamlit as st
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

@st.cache_resource
def load_finbert_pipeline():
    model_name = "ProsusAI/finbert"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    model.eval()
    return tokenizer, model

def analyze_sentiment(headlines: list[dict]):
    if not headlines:
        return []

    tokenizer, model = load_finbert_pipeline()
    texts = [h["title"] for h in headlines]

    inputs = tokenizer(texts, padding=True, truncation=True, max_length=128, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)

    labels = ["positive", "negative", "neutral"]
    analyzed = []

    for i, h in enumerate(headlines):
        pos, neg, neu = probs[i].tolist()
        net_score = pos - neg
        pred_label = labels[probs[i].argmax().item()]

        analyzed.append({
            "title": h["title"],
            "link": h["link"],
            "source": h["source"],
            "published": h["published"],
            "label": pred_label.upper(),
            "score": round(net_score, 3),
            "confidence": round(max(pos, neg, neu), 3)
        })

    return analyzed