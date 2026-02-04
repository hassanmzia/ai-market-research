"""
trend_analysis tool -- Analyzes market trends for a given sector,
identifying emerging and declining trends from web search results.
"""

import logging
import re
import time
from collections import Counter
from typing import Any, Dict, List

from duckduckgo_search import DDGS

logger = logging.getLogger("mcp_tools.trend_analysis")

# ---------------------------------------------------------------------------
# Tool schema
# ---------------------------------------------------------------------------
TOOL_SCHEMA: Dict[str, Any] = {
    "name": "trend_analysis",
    "description": (
        "Analyzes market trends for a given industry sector. Identifies "
        "emerging trends, declining trends, and key market drivers by "
        "searching recent articles and reports."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "sector": {
                "type": "string",
                "description": "The industry sector to analyze trends for.",
            },
            "company_name": {
                "type": "string",
                "description": "Optional company name for more targeted trend analysis.",
                "default": "",
            },
        },
        "required": ["sector"],
    },
}

# ---------------------------------------------------------------------------
# Trend indicators
# ---------------------------------------------------------------------------
EMERGING_INDICATORS = [
    "emerging", "growing", "rising", "trending", "booming", "accelerating",
    "adoption", "innovation", "breakthrough", "next-gen", "future of",
    "rapid growth", "new era", "disrupting", "transforming", "revolution",
    "gaining traction", "up-and-coming", "surging demand", "expansion",
]

DECLINING_INDICATORS = [
    "declining", "shrinking", "obsolete", "dying", "fading", "slowdown",
    "legacy", "outdated", "replaced by", "losing market", "downturn",
    "contraction", "phase out", "sunset", "diminishing", "displacement",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
                time.sleep(2 ** attempt)
    return []


def _extract_trends(text: str) -> List[str]:
    """Extract potential trend phrases from text."""
    trends: List[str] = []

    # Pattern: "trend/trends in/of ..."
    patterns = [
        r"(?:trend|trends)\s+(?:in|of|for|towards?)\s+([A-Za-z\s\-/&]{3,40})",
        r"(?:growth|rise|surge|adoption)\s+(?:of|in)\s+([A-Za-z\s\-/&]{3,40})",
        r"([A-Za-z\s\-/&]{3,30})\s+(?:is\s+(?:growing|rising|emerging|booming|trending))",
        r"(?:shift|move|transition)\s+(?:to|towards?)\s+([A-Za-z\s\-/&]{3,40})",
    ]

    for pat in patterns:
        matches = re.findall(pat, text, re.IGNORECASE)
        for m in matches:
            m = m.strip().rstrip(".,;:")
            if len(m) > 3 and len(m.split()) <= 6:
                trends.append(m.lower())

    return trends


def _classify_trend(text: str) -> str:
    """Classify whether text indicates an emerging or declining trend."""
    text_lower = text.lower()
    emerging = sum(1 for w in EMERGING_INDICATORS if w in text_lower)
    declining = sum(1 for w in DECLINING_INDICATORS if w in text_lower)
    if emerging > declining:
        return "emerging"
    elif declining > emerging:
        return "declining"
    return "stable"


# ---------------------------------------------------------------------------
# Tool implementation
# ---------------------------------------------------------------------------
async def run(sector: str, company_name: str = "") -> Dict[str, Any]:
    """Analyze market trends for *sector*."""
    if not sector or not sector.strip():
        return {
            "sector": sector,
            "emerging_trends": [],
            "declining_trends": [],
            "key_insights": [],
            "message": "Sector is empty.",
        }

    sector = sector.strip()
    company_name = (company_name or "").strip()

    # --- Search queries ---
    queries = [
        f"{sector} industry trends 2024 2025",
        f"{sector} market emerging trends analysis",
        f"{sector} sector future outlook predictions",
    ]
    if company_name:
        queries.append(f"{company_name} {sector} market trends")

    all_results: List[dict] = []
    for qi, query in enumerate(queries):
        if qi > 0:
            time.sleep(1)
        results = _search(query)
        all_results.extend(results)

    # --- Analyse results ---
    trend_counter: Counter = Counter()
    emerging_trends: List[str] = []
    declining_trends: List[str] = []
    key_insights: List[Dict[str, str]] = []
    seen_titles: set = set()

    for r in all_results:
        title = r.get("title", "").strip()
        body = r.get("body", "").strip()
        combined = f"{title} {body}"

        if title.lower() in seen_titles:
            continue
        seen_titles.add(title.lower())

        # Classify the result
        classification = _classify_trend(combined)

        # Extract trend phrases
        trends = _extract_trends(combined)
        for t in trends:
            trend_counter[t] += 1

        # Record insight
        key_insights.append({
            "title": title,
            "snippet": body[:200] if body else "",
            "direction": classification,
            "source": r.get("href", ""),
        })

        # Classify trend direction
        if classification == "emerging":
            for t in trends:
                if t not in emerging_trends:
                    emerging_trends.append(t)
        elif classification == "declining":
            for t in trends:
                if t not in declining_trends:
                    declining_trends.append(t)

    # --- Top trends by frequency ---
    top_trends = [
        {"trend": name, "mentions": count}
        for name, count in trend_counter.most_common(10)
    ]

    summary = (
        f"Analysis of the {sector} sector identified "
        f"{len(emerging_trends)} emerging trend(s) and "
        f"{len(declining_trends)} declining trend(s) from "
        f"{len(key_insights)} sources."
    )

    return {
        "sector": sector,
        "company_name": company_name or None,
        "emerging_trends": emerging_trends[:10],
        "declining_trends": declining_trends[:10],
        "top_trends": top_trends,
        "key_insights": key_insights[:10],
        "total_sources": len(key_insights),
        "summary": summary,
        "message": summary,
    }
