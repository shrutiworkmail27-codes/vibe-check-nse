import re

EVENT_TAXONOMY = {
    "SEBI / REGULATORY": [r"sebi", r"penalty", r"show-cause", r"ed probe", r"investigation", r"cleared"],
    "EARNINGS / RESULTS": [r"q[1-4]", r"quarterly", r"pat up", r"pat down", r"net profit", r"ebitda", r"revenue"],
    "MANAGEMENT / CXO": [r"resigns", r"resignation", r"appointed", r"new ceo", r"cfo steps down"],
    "MERGERS & DEALS": [r"acquisition", r"merger", r"stake", r"joint venture", r"deal signed"],
}

def classify_event(headline: str) -> str:
    lower = headline.lower()
    for category, patterns in EVENT_TAXONOMY.items():
        for pattern in patterns:
            if re.search(pattern, lower):
                return category
    return "GENERAL MARKET"