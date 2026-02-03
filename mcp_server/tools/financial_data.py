"""
financial_data tool -- Gathers financial data for a company by searching
for revenue, market cap, growth metrics, and key financial indicators.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from duckduckgo_search import DDGS

logger = logging.getLogger("mcp_tools.financial_data")

# ---------------------------------------------------------------------------
# Tool schema
# ---------------------------------------------------------------------------
TOOL_SCHEMA: Dict[str, Any] = {
    "name": "financial_data",
    "description": (
        "Gathers financial data for a company including revenue, market cap, "
        "growth metrics, and key financial indicators from web searches. "
        "Returns a structured financial overview."
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
                "description": "The industry sector (optional, improves search context).",
                "default": "",
            },
        },
        "required": ["company_name"],
    },
}

# ---------------------------------------------------------------------------
# Financial metric patterns
# ---------------------------------------------------------------------------
MONEY_PATTERN = re.compile(
    r"\$\s?([\d,\.]+)\s*(billion|million|trillion|B|M|T|bn|mn)",
    re.IGNORECASE,
)

PERCENTAGE_PATTERN = re.compile(
    r"([\d\.]+)\s*%",
)

METRIC_KEYWORDS: Dict[str, List[str]] = {
    "revenue": ["revenue", "sales", "annual revenue", "total revenue", "net revenue"],
    "market_cap": ["market cap", "market capitalization", "market value", "valuation"],
    "growth": ["growth", "year-over-year", "yoy", "quarterly growth", "annual growth"],
    "profit": ["profit", "net income", "earnings", "ebitda", "operating income"],
    "employees": ["employees", "workforce", "headcount", "staff"],
    "funding": ["funding", "raised", "series", "investment round", "venture"],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _search(query: str, max_results: int = 5) -> list[dict]:
    try:
        return DDGS().text(query, max_results=max_results)
    except Exception as exc:
        logger.warning("Search failed for query '%s': %s", query, exc)
        return []


def _extract_money(text: str) -> List[Dict[str, str]]:
    """Extract monetary values from text."""
    values: List[Dict[str, str]] = []
    for match in MONEY_PATTERN.finditer(text):
        amount = match.group(1).replace(",", "")
        unit = match.group(2).lower()
        # Normalise unit
        unit_map = {"b": "billion", "bn": "billion", "m": "million", "mn": "million", "t": "trillion"}
        unit = unit_map.get(unit, unit)
        values.append({"amount": amount, "unit": unit, "raw": match.group(0)})
    return values


def _extract_percentages(text: str) -> List[str]:
    """Extract percentage values from text."""
    return [f"{m}%" for m in PERCENTAGE_PATTERN.findall(text)]


def _find_metric_context(text: str, metric_keywords: List[str]) -> Optional[str]:
    """Find the sentence containing a metric keyword."""
    sentences = re.split(r"[.!?]\s+", text)
    for sentence in sentences:
        sl = sentence.lower()
        if any(kw in sl for kw in metric_keywords):
            return sentence.strip()[:300]
    return None


# ---------------------------------------------------------------------------
# Tool implementation
# ---------------------------------------------------------------------------
async def run(company_name: str, sector: str = "") -> Dict[str, Any]:
    """Gather financial data for *company_name*."""
    if not company_name or not company_name.strip():
        return {
            "company": company_name,
            "financial_data": {},
            "message": "Company name is empty.",
        }

    company_name = company_name.strip()
    sector = (sector or "").strip()

    # --- Search queries ---
    queries = [
        f"{company_name} revenue market cap financials",
        f"{company_name} annual report financial results",
        f"{company_name} company valuation funding growth",
    ]
    if sector:
        queries.append(f"{company_name} {sector} financial performance")

    all_results: List[dict] = []
    for query in queries:
        results = _search(query)
        all_results.extend(results)

    # --- Extract financial metrics ---
    financial_metrics: Dict[str, Any] = {}
    raw_data: List[Dict[str, str]] = []
    seen_titles: set = set()

    for r in all_results:
        title = r.get("title", "").strip()
        body = r.get("body", "").strip()
        combined = f"{title} {body}"

        if title.lower() in seen_titles:
            continue
        seen_titles.add(title.lower())

        combined_lower = combined.lower()

        # Extract metrics by category
        for metric_name, keywords in METRIC_KEYWORDS.items():
            context = _find_metric_context(combined, keywords)
            if context and metric_name not in financial_metrics:
                money_vals = _extract_money(context)
                pct_vals = _extract_percentages(context)
                financial_metrics[metric_name] = {
                    "context": context,
                    "monetary_values": money_vals,
                    "percentages": pct_vals,
                    "source": r.get("href", ""),
                }

        # Record source
        raw_data.append({
            "title": title,
            "snippet": body[:200] if body else "",
            "source": r.get("href", ""),
        })

    # --- Build summary ---
    summary_parts: List[str] = [f"Financial overview for '{company_name}':"]
    for metric_name, data in financial_metrics.items():
        label = metric_name.replace("_", " ").title()
        if data["monetary_values"]:
            vals = ", ".join(v["raw"] for v in data["monetary_values"])
            summary_parts.append(f"- {label}: {vals}")
        elif data["percentages"]:
            vals = ", ".join(data["percentages"])
            summary_parts.append(f"- {label}: {vals}")
        else:
            summary_parts.append(f"- {label}: {data['context'][:100]}")

    if not financial_metrics:
        summary_parts.append("- No specific financial figures found in search results.")

    summary = "\n".join(summary_parts)

    return {
        "company": company_name,
        "sector": sector or None,
        "financial_metrics": financial_metrics,
        "sources": raw_data[:10],
        "metrics_found": list(financial_metrics.keys()),
        "summary": summary,
        "message": summary,
    }
