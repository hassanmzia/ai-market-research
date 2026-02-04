"""
identify_competitors tool -- Identifies the top competitors for a given company
within its sector using multiple search strategies.
"""

import logging
import re
from collections import Counter
from typing import Any, Dict, List

from duckduckgo_search import DDGS

logger = logging.getLogger("mcp_tools.identify_competitors")

# ---------------------------------------------------------------------------
# Tool schema
# ---------------------------------------------------------------------------
TOOL_SCHEMA: Dict[str, Any] = {
    "name": "identify_competitors",
    "description": (
        "Identifies the top 3 competitors for a company in its sector by "
        "searching the web with multiple queries and ranking by frequency."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "company_name": {
                "type": "string",
                "description": "The name of the company.",
            },
            "sector": {
                "type": "string",
                "description": "The industry sector of the company (e.g., 'Technology').",
            },
        },
        "required": ["company_name", "sector"],
    },
}

# ---------------------------------------------------------------------------
# Known companies per sector (seed list for boosting)
# ---------------------------------------------------------------------------
SECTOR_COMPANIES: Dict[str, List[str]] = {
    "Technology": [
        "Google", "Microsoft", "Apple", "Amazon", "Meta", "Salesforce", "Oracle",
        "IBM", "Adobe", "SAP", "Intel", "Nvidia", "Cisco", "ServiceNow",
        "Snowflake", "Databricks", "Palantir", "CrowdStrike", "Shopify",
    ],
    "Finance": [
        "JPMorgan", "Goldman Sachs", "Morgan Stanley", "Bank of America",
        "Citigroup", "Wells Fargo", "BlackRock", "Visa", "Mastercard",
        "PayPal", "Square", "Stripe", "Robinhood", "Charles Schwab",
    ],
    "Healthcare": [
        "Johnson & Johnson", "Pfizer", "UnitedHealth", "Abbott", "Merck",
        "AstraZeneca", "Novartis", "Roche", "Moderna", "Eli Lilly",
        "Medtronic", "Amgen", "Gilead", "Bristol-Myers Squibb",
    ],
    "Education": [
        "Coursera", "Udemy", "Khan Academy", "Pearson", "Chegg",
        "Duolingo", "Byju's", "2U", "Instructure", "McGraw-Hill",
    ],
    "Retail": [
        "Amazon", "Walmart", "Target", "Costco", "Alibaba", "Shopify",
        "eBay", "Etsy", "Wayfair", "Best Buy", "Home Depot",
    ],
    "Manufacturing": [
        "Siemens", "General Electric", "3M", "Honeywell", "Caterpillar",
        "Deere & Company", "ABB", "Emerson", "Parker Hannifin", "Rockwell",
    ],
    "Energy": [
        "ExxonMobil", "Chevron", "Shell", "BP", "TotalEnergies",
        "NextEra Energy", "Enphase", "First Solar", "Tesla Energy",
        "ConocoPhillips", "Duke Energy",
    ],
}


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


def _extract_company_names(text: str, company_name: str) -> List[str]:
    """Extract potential company names from a text block."""
    names: List[str] = []
    company_lower = company_name.lower()

    # Pattern 1: Numbered lists  ("1. CompanyName", "1) CompanyName")
    numbered = re.findall(r"\d+[\.\)]\s*([A-Z][A-Za-z\s&\-\.]{2,30})", text)
    for n in numbered:
        n = n.strip().rstrip(".")
        if n.lower() != company_lower and len(n) > 2:
            names.append(n)

    # Pattern 2: Bullet-style lists ("- CompanyName", "* CompanyName")
    bullets = re.findall(r"[\-\*]\s+([A-Z][A-Za-z\s&\-\.]{2,30})", text)
    for b in bullets:
        b = b.strip().rstrip(".")
        if b.lower() != company_lower and len(b) > 2:
            names.append(b)

    # Pattern 3: "such as X, Y, and Z"
    such_as = re.findall(
        r"such as\s+((?:[A-Z][A-Za-z\s&\-\.]+(?:,\s*)?)+(?:and\s+[A-Z][A-Za-z\s&\-\.]+)?)",
        text,
    )
    for match in such_as:
        parts = re.split(r",\s*(?:and\s+)?|(?:\s+and\s+)", match)
        for p in parts:
            p = p.strip().rstrip(".")
            if p and p.lower() != company_lower and len(p) > 2:
                names.append(p)

    # Pattern 4: "competitors include X, Y"
    comp_include = re.findall(
        r"competitors?\s+(?:include|are|like)\s+((?:[A-Z][A-Za-z\s&\-\.]+(?:,\s*)?)+(?:and\s+[A-Z][A-Za-z\s&\-\.]+)?)",
        text,
        re.IGNORECASE,
    )
    for match in comp_include:
        parts = re.split(r",\s*(?:and\s+)?|(?:\s+and\s+)", match)
        for p in parts:
            p = p.strip().rstrip(".")
            if p and p.lower() != company_lower and len(p) > 2:
                names.append(p)

    return names


# ---------------------------------------------------------------------------
# Tool implementation
# ---------------------------------------------------------------------------
async def run(company_name: str, sector: str) -> Dict[str, Any]:
    """Identify top 3 competitors for *company_name* in *sector*."""
    if not company_name or not company_name.strip():
        return {
            "company": company_name,
            "sector": sector,
            "competitors": [],
            "message": "Company name is empty.",
        }

    company_name = company_name.strip()
    sector = (sector or "").strip()
    competitor_counter: Counter = Counter()
    evidence: list[str] = []

    # --- Query 1: General sector competitors ---
    q1 = f"top companies in {sector} sector competitors"
    results1 = _search(q1)
    for r in results1:
        combined = f"{r.get('title', '')} {r.get('body', '')}"
        names = _extract_company_names(combined, company_name)
        for name in names:
            competitor_counter[name] += 1
        if names:
            evidence.append(f"[Query 1] Found names in: {r.get('title', '')[:80]}")

    # --- Query 2: Direct competitors ---
    q2 = f"{company_name} competitors alternatives vs"
    results2 = _search(q2)
    for r in results2:
        combined = f"{r.get('title', '')} {r.get('body', '')}"
        names = _extract_company_names(combined, company_name)
        for name in names:
            competitor_counter[name] += 2  # higher weight for direct competitor mentions
        if names:
            evidence.append(f"[Query 2] Found names in: {r.get('title', '')[:80]}")

    # --- Query 3: Industry analysis ---
    q3 = f"{company_name} {sector} industry analysis market share"
    results3 = _search(q3)
    for r in results3:
        combined = f"{r.get('title', '')} {r.get('body', '')}"
        names = _extract_company_names(combined, company_name)
        for name in names:
            competitor_counter[name] += 1
        if names:
            evidence.append(f"[Query 3] Found names in: {r.get('title', '')[:80]}")

    # --- Boost known sector companies ---
    known = SECTOR_COMPANIES.get(sector, [])
    for company in known:
        if company.lower() != company_name.lower() and company in competitor_counter:
            competitor_counter[company] += 2  # boost known names

    # Also check if known companies appear in any result text even if not extracted
    all_text = ""
    for results in [results1, results2, results3]:
        for r in results:
            all_text += f" {r.get('title', '')} {r.get('body', '')}"
    all_text_lower = all_text.lower()
    for company in known:
        if company.lower() != company_name.lower() and company.lower() in all_text_lower:
            competitor_counter[company] += 1

    # --- Remove self ---
    for key in list(competitor_counter.keys()):
        if key.lower() == company_name.lower():
            del competitor_counter[key]

    # --- Top 3 ---
    top_competitors = [
        {"name": name, "mentions": count}
        for name, count in competitor_counter.most_common(3)
    ]

    return {
        "company": company_name,
        "sector": sector,
        "competitors": top_competitors,
        "all_candidates": dict(competitor_counter.most_common(10)),
        "evidence": evidence,
        "message": (
            f"Top competitors for '{company_name}' in {sector}: "
            + ", ".join(c["name"] for c in top_competitors)
            if top_competitors
            else f"Could not identify competitors for '{company_name}'."
        ),
    }
