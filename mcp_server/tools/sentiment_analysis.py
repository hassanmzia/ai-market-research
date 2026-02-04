"""
sentiment_analysis tool -- Analyzes market sentiment for a company
by searching for recent news and classifying headline sentiment.
"""

import logging
import re
import time
from typing import Any, Dict, List

from duckduckgo_search import DDGS

logger = logging.getLogger("mcp_tools.sentiment_analysis")

# ---------------------------------------------------------------------------
# Tool schema
# ---------------------------------------------------------------------------
TOOL_SCHEMA: Dict[str, Any] = {
    "name": "sentiment_analysis",
    "description": (
        "Analyzes market sentiment for a company by searching recent news "
        "headlines and classifying them as positive, negative, or neutral. "
        "Returns an overall sentiment score and summary."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "company_name": {
                "type": "string",
                "description": "The name of the company to analyze sentiment for.",
            },
            "sector": {
                "type": "string",
                "description": "The industry sector (optional, improves search context).",
                "default": "",
            },
        },
        "required": ["company_name"],
    },
}

# ---------------------------------------------------------------------------
# Sentiment lexicons
# ---------------------------------------------------------------------------
POSITIVE_WORDS = [
    "growth", "profit", "gain", "surge", "rise", "soar", "jump", "boost",
    "record", "strong", "positive", "beat", "exceed", "upgrade", "expand",
    "innovation", "breakthrough", "success", "winning", "bullish", "rally",
    "outperform", "partnership", "deal", "launch", "milestone", "recovery",
    "optimistic", "upbeat", "leading", "dominance", "revenue growth",
    "impressive", "stellar", "robust", "accelerate", "momentum",
]

NEGATIVE_WORDS = [
    "loss", "decline", "drop", "fall", "crash", "plunge", "cut", "layoff",
    "lawsuit", "fine", "penalty", "scandal", "fraud", "bankruptcy", "debt",
    "downgrade", "miss", "weak", "bearish", "selloff", "sell-off", "risk",
    "concern", "warning", "threat", "struggle", "fail", "closure", "recall",
    "investigation", "regulatory", "antitrust", "slump", "downturn",
    "disappointing", "shortfall", "deficit", "restructuring",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _classify_headline(text: str) -> str:
    """Classify a headline as positive, negative, or neutral."""
    text_lower = text.lower()
    pos_count = sum(1 for w in POSITIVE_WORDS if w in text_lower)
    neg_count = sum(1 for w in NEGATIVE_WORDS if w in text_lower)

    if pos_count > neg_count:
        return "positive"
    elif neg_count > pos_count:
        return "negative"
    return "neutral"


def _compute_score(classifications: List[str]) -> float:
    """Compute a sentiment score from -1.0 (very negative) to 1.0 (very positive)."""
    if not classifications:
        return 0.0
    score_map = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
    total = sum(score_map[c] for c in classifications)
    return round(total / len(classifications), 2)


def _search(query: str, max_results: int = 5, retries: int = 3) -> list[dict]:
    for attempt in range(retries):
        try:
            results = DDGS().text(query, max_results=max_results)
            return results
        except Exception as exc:
            logger.warning(
                "Search attempt %d/%d failed for '%s': %s",
                attempt + 1, retries, query, exc,
            )
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # 1s, 2s backoff
    return []


# ---------------------------------------------------------------------------
# Tool implementation
# ---------------------------------------------------------------------------
async def run(company_name: str, sector: str = "") -> Dict[str, Any]:
    """Analyze market sentiment for *company_name*."""
    if not company_name or not company_name.strip():
        return {
            "company": company_name,
            "sentiment_score": 0.0,
            "overall_sentiment": "neutral",
            "headlines": [],
            "message": "Company name is empty.",
        }

    company_name = company_name.strip()
    sector = (sector or "").strip()

    # --- Search for recent news ---
    queries = [
        f"{company_name} latest news",
        f"{company_name} stock market news",
    ]
    if sector:
        queries.append(f"{company_name} {sector} news analysis")

    all_headlines: List[Dict[str, str]] = []
    seen_titles: set = set()

    for qi, query in enumerate(queries):
        if qi > 0:
            time.sleep(1)  # Space out searches to avoid rate limits
        results = _search(query)
        for r in results:
            title = r.get("title", "").strip()
            body = r.get("body", "").strip()
            if not title or title.lower() in seen_titles:
                continue
            seen_titles.add(title.lower())

            combined = f"{title} {body}"
            classification = _classify_headline(combined)
            all_headlines.append({
                "title": title,
                "snippet": body[:200] if body else "",
                "sentiment": classification,
                "source": r.get("href", ""),
            })

    # --- Compute overall sentiment ---
    classifications = [h["sentiment"] for h in all_headlines]
    sentiment_score = _compute_score(classifications)

    pos_count = classifications.count("positive")
    neg_count = classifications.count("negative")
    neu_count = classifications.count("neutral")

    if sentiment_score > 0.3:
        overall = "positive"
    elif sentiment_score < -0.3:
        overall = "negative"
    else:
        overall = "neutral"

    # --- Summary ---
    total = len(all_headlines)
    summary = (
        f"Based on {total} recent headlines, market sentiment for '{company_name}' "
        f"is **{overall}** (score: {sentiment_score}). "
        f"Breakdown: {pos_count} positive, {neg_count} negative, {neu_count} neutral."
    )

    return {
        "company": company_name,
        "sentiment_score": sentiment_score,
        "overall_sentiment": overall,
        "positive_count": pos_count,
        "negative_count": neg_count,
        "neutral_count": neu_count,
        "total_headlines": total,
        "headlines": all_headlines,
        "summary": summary,
        "message": summary,
    }
