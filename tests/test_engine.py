import unittest
from src.data_fetcher import resolve_ticker
from src.event_classifier import classify_event
from src.scorer import calculate_confluence

class TestEngine(unittest.TestCase):

    def test_ticker_resolver(self):
        symbol, name = resolve_ticker("TATAMOTORS")
        self.assertEqual(symbol, "TATAMOTORS.NS")
        self.assertEqual(name, "Tata Motors")

    def test_event_classifier(self):
        category = classify_event("SEBI imposes fine on market maker")
        self.assertEqual(category, "SEBI / REGULATORY")

    def test_confluence_logic(self):
        mock_news = [{"score": 0.8, "label": "POSITIVE"}]
        mock_technicals = {"rsi": 78, "current_price": 500, "sma50": 450}
        res = calculate_confluence(mock_news, mock_technicals)
        self.assertIn("OVERBOUGHT", res["verdict"])

if __name__ == "__main__":
    unittest.main()