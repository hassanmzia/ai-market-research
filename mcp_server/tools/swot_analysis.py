"""
swot_analysis tool -- Performs a SWOT (Strengths, Weaknesses, Opportunities,
Threats) analysis for a company using web search and provided context.
"""

import logging
import re
from typing import Any, Dict, List

from duckduckgo_search import DDGS

logger = logging.getLogger("mcp_tools.swot_analysis")

# ---------------------------------------------------------------------------
# Tool schema
# ---------------------------------------------------------------------------
TOOL_SCHEMA: Dict[str, Any] = {
    "name": "swot_analysis",
    "description": (
        "Performs a SWOT analysis (Strengths, Weaknesses, Opportunities, "
        "Threats) for a company by searching the web and analyzing the provided "
        "context. Returns structured SWOT data."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "company_name": {
                "type": "string",
                "description": "The name of the company to analyze.",
            },
            "sector": {
                "type": "string",
                "description": "The industry sector of the company.",
                "default": "",
            },
            "context": {
                "type": "string",
                "description": (
                    "Additional context gathered from previous research "
                    "(competitors, financials, sentiment, etc.)."
                ),
                "default": "",
            },
        },
        "required": ["company_name"],
    },
}

# ---------------------------------------------------------------------------
# SWOT keyword patterns
# ---------------------------------------------------------------------------
STRENGTH_KEYWORDS = [
    "leader", "leading", "dominant", "strong", "innovative", "patent",
    "brand recognition", "loyal customer", "market share", "expertise",
    "proprietary", "advantage", "best-in-class", "award", "reputation",
    "profitable", "efficient", "scalable", "global presence", "diverse",
    "talent", "ecosystem", "network effect", "recurring revenue",
]

WEAKNESS_KEYWORDS = [
    "weak", "limited", "lack", "depend", "concentration", "debt",
    "legacy", "outdated", "slow", "bureaucra", "complex", "expensive",
    "narrow", "vulnerable", "turnover", "attrition", "regulatory burden",
    "single point", "over-reliance", "margin pressure", "customer churn",
]

OPPORTUNITY_KEYWORDS = [
    "opportunity", "growth", "expansion", "emerging market", "untapped",
    "acquisition", "partnership", "new market", "innovation", "digital",
    "transformation", "regulation change", "trend", "demand", "adoption",
    "global", "international", "underserved", "gap", "potential",
    "next generation", "ai", "cloud", "sustainability",
]

THREAT_KEYWORDS = [
    "threat", "competition", "regulatory", "disrupt", "recession",
    "economic downturn", "new entrant", "substitute", "price war",
    "cybersecurity", "data breach", "geopolitical", "tariff", "supply chain",
    "inflation", "talent shortage", "commoditization", "antitrust",
    "obsolescence", "changing consumer", "interest rate",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _search(query: str, max_results: int = 5, retries: int = 3) -> list[dict]:
    import time
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


def _extract_items(text: str, keywords: List[str], max_items: int = 5) -> List[str]:
    """Extract sentences from text that match given keywords."""
    sentences = re.split(r"[.!?]\s+", text)
    items: List[str] = []
    seen: set = set()

    for sentence in sentences:
        sl = sentence.lower().strip()
        if len(sl) < 15 or len(sl) > 300:
            continue
        for kw in keywords:
            if kw in sl and sl not in seen:
                clean = sentence.strip()
                if not clean.endswith("."):
                    clean += "."
                items.append(clean)
                seen.add(sl)
                break
        if len(items) >= max_items:
            break

    return items


def _deduplicate(items: List[str]) -> List[str]:
    """Remove near-duplicate items."""
    unique: List[str] = []
    seen_starts: set = set()
    for item in items:
        start = item[:50].lower()
        if start not in seen_starts:
            seen_starts.add(start)
            unique.append(item)
    return unique


# ---------------------------------------------------------------------------
# Tool implementation
# ---------------------------------------------------------------------------
async def run(
    company_name: str,
    sector: str = "",
    context: str = "",
) -> Dict[str, Any]:
    """Perform a SWOT analysis for *company_name*."""
    if not company_name or not company_name.strip():
        return {
            "company": company_name,
            "swot": {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []},
            "message": "Company name is empty.",
        }

    company_name = company_name.strip()
    sector = (sector or "").strip()
    context = (context or "").strip()

    # --- Gather text from searches ---
    queries = [
        f"{company_name} strengths weaknesses SWOT analysis",
        f"{company_name} competitive advantages challenges",
        f"{company_name} opportunities threats market",
    ]
    if sector:
        queries.append(f"{sector} industry opportunities threats trends")

    all_text = context + " "
    for query in queries:
        results = _search(query)
        for r in results:
            all_text += f" {r.get('title', '')}. {r.get('body', '')}. "

    # --- Extract SWOT items ---
    strengths = _extract_items(all_text, STRENGTH_KEYWORDS, max_items=5)
    weaknesses = _extract_items(all_text, WEAKNESS_KEYWORDS, max_items=5)
    opportunities = _extract_items(all_text, OPPORTUNITY_KEYWORDS, max_items=5)
    threats = _extract_items(all_text, THREAT_KEYWORDS, max_items=5)

    # Deduplicate
    strengths = _deduplicate(strengths)
    weaknesses = _deduplicate(weaknesses)
    opportunities = _deduplicate(opportunities)
    threats = _deduplicate(threats)

    # --- Generate defaults if empty ---
    if not strengths:
        strengths = [f"{company_name} has established presence in the {sector or 'market'} sector."]
    if not weaknesses:
        weaknesses = ["Further research needed to identify specific weaknesses."]
    if not opportunities:
        opportunities = [f"Growth potential exists in the {sector or 'broader'} market."]
    if not threats:
        threats = ["Competitive pressure from established and emerging players."]

    # --- Build Markdown summary ---
    md_parts: List[str] = [
        f"# SWOT Analysis: {company_name}",
        "",
        "## Strengths",
        *[f"- {s}" for s in strengths],
        "",
        "## Weaknesses",
        *[f"- {w}" for w in weaknesses],
        "",
        "## Opportunities",
        *[f"- {o}" for o in opportunities],
        "",
        "## Threats",
        *[f"- {t}" for t in threats],
    ]
    markdown = "\n".join(md_parts)

    summary = (
        f"SWOT analysis for '{company_name}': "
        f"{len(strengths)} strengths, {len(weaknesses)} weaknesses, "
        f"{len(opportunities)} opportunities, {len(threats)} threats identified."
    )

    return {
        "company": company_name,
        "sector": sector or None,
        "swot": {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "opportunities": opportunities,
            "threats": threats,
        },
        "markdown": markdown,
        "summary": summary,
        "message": summary,
    }
