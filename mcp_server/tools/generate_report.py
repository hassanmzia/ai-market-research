"""
generate_report tool -- Generates a competitive analysis report in Markdown
from gathered research context.
"""

import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger("mcp_tools.generate_report")

# ---------------------------------------------------------------------------
# Tool schema
# ---------------------------------------------------------------------------
TOOL_SCHEMA: Dict[str, Any] = {
    "name": "generate_report",
    "description": (
        "Generates a structured competitive analysis report in Markdown. "
        "Includes an Executive Summary, Competitor Comparison table, and "
        "Actionable Insights based on the provided context."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "company_name": {
                "type": "string",
                "description": "The name of the company being analyzed.",
            },
            "sector": {
                "type": "string",
                "description": "The industry sector of the company.",
            },
            "competitors": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of competitor company names.",
            },
            "context": {
                "type": "string",
                "description": (
                    "Additional research context gathered from previous tools "
                    "(browsing, sentiment, financials, etc.)."
                ),
                "default": "",
            },
        },
        "required": ["company_name", "sector", "competitors"],
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_context_info(context: str, company: str) -> Dict[str, str]:
    """Pull structured snippets from free-text context for a company."""
    info: Dict[str, str] = {
        "description": "N/A",
        "strengths": "N/A",
        "market_position": "N/A",
    }
    if not context:
        return info

    context_lower = context.lower()
    company_lower = company.lower()

    # Try to find a sentence mentioning the company
    sentences = re.split(r"[.!?]\s+", context)
    for s in sentences:
        sl = s.lower()
        if company_lower in sl:
            if any(kw in sl for kw in ["is a", "provides", "offers", "develops", "specializes"]):
                info["description"] = s.strip()[:200]
            if any(kw in sl for kw in ["leader", "leading", "top", "largest", "dominant", "strong"]):
                info["market_position"] = s.strip()[:200]
            if any(kw in sl for kw in ["strength", "advantage", "known for", "excels", "innovative"]):
                info["strengths"] = s.strip()[:200]

    return info


def _build_comparison_table(
    company_name: str,
    sector: str,
    competitors: List[str],
    context: str,
) -> str:
    """Build a Markdown comparison table."""
    all_companies = [company_name] + competitors
    rows: List[str] = []

    # Header
    rows.append("| Company | Sector Focus | Market Position | Key Strengths |")
    rows.append("|---------|-------------|-----------------|---------------|")

    for comp in all_companies:
        info = _extract_context_info(context, comp)
        position = info["market_position"] if info["market_position"] != "N/A" else "Established player"
        strengths = info["strengths"] if info["strengths"] != "N/A" else "Industry expertise"
        label = f"**{comp}** (target)" if comp == company_name else comp
        rows.append(f"| {label} | {sector} | {position} | {strengths} |")

    return "\n".join(rows)


# ---------------------------------------------------------------------------
# Tool implementation
# ---------------------------------------------------------------------------
async def run(
    company_name: str,
    sector: str,
    competitors: List[str],
    context: str = "",
) -> Dict[str, Any]:
    """Generate a competitive analysis report."""
    if not company_name or not company_name.strip():
        return {"report": "", "message": "Company name is empty."}

    company_name = company_name.strip()
    sector = (sector or "Unknown").strip()
    competitors = [c.strip() for c in competitors if c and c.strip()]

    if not competitors:
        competitors = ["(no competitors identified)"]

    competitor_list = ", ".join(competitors)
    comparison_table = _build_comparison_table(company_name, sector, competitors, context)

    # --- Build report ---
    report_parts: List[str] = []

    # Title
    report_parts.append(f"# Competitive Analysis Report: {company_name}")
    report_parts.append("")
    report_parts.append(f"**Sector:** {sector}  ")
    report_parts.append(f"**Key Competitors:** {competitor_list}  ")
    report_parts.append("")

    # Executive Summary
    report_parts.append("## Executive Summary")
    report_parts.append("")
    report_parts.append(
        f"{company_name} operates in the **{sector}** sector. "
        f"This analysis examines the competitive landscape, identifying "
        f"**{len(competitors)}** key competitor(s): {competitor_list}. "
        f"The report provides a comparative overview and actionable insights "
        f"for strategic positioning."
    )
    report_parts.append("")

    # Company overview from context
    comp_info = _extract_context_info(context, company_name)
    if comp_info["description"] != "N/A":
        report_parts.append("### Company Overview")
        report_parts.append("")
        report_parts.append(comp_info["description"])
        report_parts.append("")

    # Competitor Comparison
    report_parts.append("## Competitor Comparison")
    report_parts.append("")
    report_parts.append(comparison_table)
    report_parts.append("")

    # Individual competitor sections
    report_parts.append("## Competitor Profiles")
    report_parts.append("")
    for i, comp in enumerate(competitors, 1):
        report_parts.append(f"### {i}. {comp}")
        info = _extract_context_info(context, comp)
        if info["description"] != "N/A":
            report_parts.append(f"- **Overview:** {info['description']}")
        if info["market_position"] != "N/A":
            report_parts.append(f"- **Market Position:** {info['market_position']}")
        if info["strengths"] != "N/A":
            report_parts.append(f"- **Key Strengths:** {info['strengths']}")
        if all(v == "N/A" for v in info.values()):
            report_parts.append(f"- Further research recommended for detailed profile.")
        report_parts.append("")

    # Actionable Insights
    report_parts.append("## Actionable Insights")
    report_parts.append("")
    report_parts.append(
        f"1. **Competitive Differentiation:** {company_name} should identify and "
        f"strengthen its unique value proposition relative to {competitor_list}."
    )
    report_parts.append(
        f"2. **Market Positioning:** Focus on underserved segments within the "
        f"{sector} sector where competitors have limited presence."
    )
    report_parts.append(
        f"3. **Innovation Strategy:** Monitor competitor product roadmaps and "
        f"invest in R&D to maintain technological edge."
    )
    report_parts.append(
        f"4. **Strategic Partnerships:** Explore partnerships or integrations "
        f"that complement existing offerings and expand market reach."
    )
    report_parts.append(
        f"5. **Customer Retention:** Analyze competitor pricing and service models "
        f"to ensure competitive customer value."
    )
    report_parts.append("")

    # Disclaimer
    report_parts.append("---")
    report_parts.append(
        "*This report was generated by the AI Market Research Assistant using "
        "publicly available information. Data should be verified for critical "
        "business decisions.*"
    )

    report = "\n".join(report_parts)

    return {
        "report": report,
        "company": company_name,
        "sector": sector,
        "competitors": competitors,
        "message": f"Report generated for '{company_name}' with {len(competitors)} competitors.",
    }
