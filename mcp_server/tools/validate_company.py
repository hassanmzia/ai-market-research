"""
validate_company tool -- Validates whether a company name refers to a real business
by performing web searches and analysing the results for evidence.
"""

import logging
import re
from typing import Any, Dict

from duckduckgo_search import DDGS

logger = logging.getLogger("mcp_tools.validate_company")

# ---------------------------------------------------------------------------
# Tool schema (exposed to MCP clients)
# ---------------------------------------------------------------------------
TOOL_SCHEMA: Dict[str, Any] = {
    "name": "validate_company",
    "description": (
        "Validates if a company name is real by searching the web for evidence "
        "of its existence. Returns a validation result with confidence indicators."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "company_name": {
                "type": "string",
                "description": "The name of the company to validate.",
            }
        },
        "required": ["company_name"],
    },
}

# ---------------------------------------------------------------------------
# Evidence patterns
# ---------------------------------------------------------------------------
OFFICIAL_DOMAIN_PATTERNS = [
    r"\.com",
    r"\.io",
    r"\.org",
    r"\.net",
    r"\.co",
    r"\.ai",
]

BUSINESS_TERMS = [
    "inc",
    "llc",
    "ltd",
    "corporation",
    "company",
    "enterprise",
    "group",
    "holdings",
    "founded",
    "headquartered",
    "ceo",
    "revenue",
    "employees",
    "nasdaq",
    "nyse",
    "stock",
    "ipo",
    "startup",
    "funding",
    "series a",
    "series b",
    "valuation",
]

TRUSTED_SOURCES = [
    "wikipedia",
    "bloomberg",
    "reuters",
    "crunchbase",
    "linkedin",
    "forbes",
    "techcrunch",
    "wsj",
    "ft.com",
    "sec.gov",
]


# ---------------------------------------------------------------------------
# Tool implementation
# ---------------------------------------------------------------------------
async def run(company_name: str) -> Dict[str, Any]:
    """Validate whether *company_name* refers to a real company."""
    if not company_name or not company_name.strip():
        return {
            "company": company_name,
            "is_valid": False,
            "confidence": "none",
            "evidence_count": 0,
            "evidence": [],
            "message": "Company name is empty.",
        }

    company_name = company_name.strip()
    query = f"{company_name} company business official site"
    logger.info("Validating company: %s (query: %s)", company_name, query)

    evidence: list[str] = []

    try:
        results = DDGS().text(query, max_results=5)
    except Exception as exc:
        logger.error("Search failed for '%s': %s", company_name, exc)
        # Re-raise so the MCP server returns an error (not cached)
        raise RuntimeError(f"Search temporarily unavailable: {exc}") from exc

    if not results:
        return {
            "company": company_name,
            "is_valid": False,
            "confidence": "low",
            "evidence_count": 0,
            "evidence": [],
            "message": "No search results found.",
        }

    company_lower = company_name.lower()

    for r in results:
        title = (r.get("title") or "").lower()
        body = (r.get("body") or "").lower()
        href = (r.get("href") or "").lower()
        combined = f"{title} {body} {href}"

        # Check 1: Official domain present
        for pat in OFFICIAL_DOMAIN_PATTERNS:
            if re.search(pat, href) and company_lower.split()[0] in href:
                evidence.append(f"Official domain found: {href}")
                break

        # Check 2: Title or body contains "official site" style language
        if any(kw in combined for kw in ["official site", "official website", "official page", "home page"]):
            evidence.append(f"Official site mention in: {r.get('title', '')}")

        # Check 3: Company description present
        if company_lower in combined and any(
            term in combined
            for term in ["is a", "was founded", "provides", "offers", "specializes", "develops"]
        ):
            evidence.append(f"Company description found: {r.get('title', '')}")

        # Check 4: Business terminology
        if any(term in combined for term in BUSINESS_TERMS):
            evidence.append(f"Business terminology found: {r.get('title', '')}")

        # Check 5: Trusted / known source
        if any(src in href for src in TRUSTED_SOURCES):
            evidence.append(f"Trusted source mention: {href}")

    # De-duplicate evidence
    evidence = list(dict.fromkeys(evidence))
    evidence_count = len(evidence)

    is_valid = evidence_count >= 2
    if evidence_count >= 4:
        confidence = "high"
    elif evidence_count >= 2:
        confidence = "medium"
    else:
        confidence = "low"

    message = (
        f"Company '{company_name}' appears to be a valid company."
        if is_valid
        else f"Could not confirm '{company_name}' as a real company."
    )

    return {
        "company": company_name,
        "is_valid": is_valid,
        "confidence": confidence,
        "evidence_count": evidence_count,
        "evidence": evidence,
        "message": message,
    }
