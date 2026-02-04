"""
identify_sector tool -- Determines the primary industry sector of a company
using multiple web-search strategies and pattern matching.
"""

import logging
import re
from collections import Counter
from typing import Any, Dict, List

from duckduckgo_search import DDGS

logger = logging.getLogger("mcp_tools.identify_sector")

# ---------------------------------------------------------------------------
# Tool schema
# ---------------------------------------------------------------------------
TOOL_SCHEMA: Dict[str, Any] = {
    "name": "identify_sector",
    "description": (
        "Determines the industry sector of a company by searching the web "
        "using multiple strategies and matching against known sector patterns. "
        "Returns the primary sector along with supporting evidence."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "company_name": {
                "type": "string",
                "description": "The name of the company to classify.",
            }
        },
        "required": ["company_name"],
    },
}

# ---------------------------------------------------------------------------
# Sector patterns
# ---------------------------------------------------------------------------
SECTOR_PATTERNS: Dict[str, List[str]] = {
    "Technology": [
        "software",
        "saas",
        "cloud",
        "ai",
        "artificial intelligence",
        "machine learning",
        "data",
        "platform",
        "digital",
        "tech",
        "internet",
        "app",
        "computing",
        "semiconductor",
        "cyber",
        "blockchain",
        "automation",
        "it services",
        "developer",
        "api",
    ],
    "Finance": [
        "bank",
        "banking",
        "financial",
        "fintech",
        "insurance",
        "investment",
        "capital",
        "asset management",
        "payments",
        "lending",
        "credit",
        "trading",
        "wealth",
        "mortgage",
        "hedge fund",
        "private equity",
        "venture capital",
    ],
    "Healthcare": [
        "health",
        "medical",
        "pharmaceutical",
        "biotech",
        "hospital",
        "clinical",
        "patient",
        "drug",
        "therapy",
        "diagnostic",
        "genomic",
        "wellness",
        "telehealth",
        "healthcare",
        "life sciences",
    ],
    "Education": [
        "education",
        "edtech",
        "learning",
        "university",
        "school",
        "training",
        "academic",
        "course",
        "student",
        "teacher",
        "curriculum",
        "e-learning",
        "tutoring",
        "certification",
    ],
    "Retail": [
        "retail",
        "e-commerce",
        "ecommerce",
        "store",
        "shop",
        "consumer",
        "marketplace",
        "brand",
        "fashion",
        "grocery",
        "merchandise",
        "wholesale",
        "direct-to-consumer",
        "d2c",
    ],
    "Manufacturing": [
        "manufacturing",
        "industrial",
        "factory",
        "production",
        "supply chain",
        "logistics",
        "automotive",
        "aerospace",
        "materials",
        "engineering",
        "hardware",
        "equipment",
        "assembly",
    ],
    "Energy": [
        "energy",
        "oil",
        "gas",
        "renewable",
        "solar",
        "wind",
        "nuclear",
        "utility",
        "electricity",
        "power",
        "clean energy",
        "petroleum",
        "mining",
        "sustainability",
        "ev",
        "battery",
    ],
}

# ---------------------------------------------------------------------------
# Helper
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


def _match_sectors(text: str) -> List[str]:
    """Return list of sector names whose patterns appear in *text*."""
    text_lower = text.lower()
    found: List[str] = []
    for sector, keywords in SECTOR_PATTERNS.items():
        for kw in keywords:
            if kw in text_lower:
                found.append(sector)
                break  # one match per sector per text block
    return found


# ---------------------------------------------------------------------------
# Tool implementation
# ---------------------------------------------------------------------------
async def run(company_name: str) -> Dict[str, Any]:
    """Identify the primary industry sector of *company_name*."""
    if not company_name or not company_name.strip():
        return {
            "company": company_name,
            "sector": "Unknown",
            "confidence": "none",
            "all_sectors": {},
            "evidence": [],
            "message": "Company name is empty.",
        }

    company_name = company_name.strip()
    sector_counter: Counter = Counter()
    evidence: list[str] = []

    # --- Strategy 1: General company description ---
    query1 = f"{company_name} company description what does it do"
    results1 = _search(query1)
    for r in results1:
        combined = f"{r.get('title', '')} {r.get('body', '')}"
        sectors = _match_sectors(combined)
        for s in sectors:
            sector_counter[s] += 1
            evidence.append(f"[Strategy 1] {s} matched in: {r.get('title', '')[:80]}")

    # --- Strategy 2: Wikipedia / LinkedIn style ---
    query2 = f"{company_name} Wikipedia OR LinkedIn industry sector"
    results2 = _search(query2)
    for r in results2:
        combined = f"{r.get('title', '')} {r.get('body', '')}"
        sectors = _match_sectors(combined)
        for s in sectors:
            sector_counter[s] += 1
            evidence.append(f"[Strategy 2] {s} matched in: {r.get('title', '')[:80]}")

    # --- Strategy 3: News and financial context ---
    query3 = f"{company_name} industry sector news financial"
    results3 = _search(query3)
    for r in results3:
        combined = f"{r.get('title', '')} {r.get('body', '')}"
        sectors = _match_sectors(combined)
        for s in sectors:
            sector_counter[s] += 1
            evidence.append(f"[Strategy 3] {s} matched in: {r.get('title', '')[:80]}")

    # --- Determine primary sector ---
    if not sector_counter:
        return {
            "company": company_name,
            "sector": "Unknown",
            "confidence": "low",
            "all_sectors": {},
            "evidence": evidence,
            "message": f"Could not determine the sector for '{company_name}'.",
        }

    primary_sector = sector_counter.most_common(1)[0][0]
    primary_count = sector_counter.most_common(1)[0][1]
    total_signals = sum(sector_counter.values())

    if primary_count >= 5:
        confidence = "high"
    elif primary_count >= 3:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "company": company_name,
        "sector": primary_sector,
        "confidence": confidence,
        "all_sectors": dict(sector_counter.most_common()),
        "total_signals": total_signals,
        "evidence": evidence,
        "message": f"'{company_name}' is primarily in the {primary_sector} sector.",
    }
