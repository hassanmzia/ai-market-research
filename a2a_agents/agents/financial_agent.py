"""Financial data agent -- gathers financial metrics for the company and competitors."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class FinancialAgent(BaseAgent):
    name = "financial_agent"
    description = (
        "Gathers and analyses financial data for the target company and its "
        "competitors using MCP tools and LLM interpretation."
    )
    capabilities: List[str] = [
        "financial_data_gathering",
        "financial_comparison",
        "revenue_analysis",
        "growth_metrics",
    ]
    mcp_tools: List[str] = ["financial_data"]

    async def _fetch_financial(self, company: str) -> Dict[str, Any]:
        """Fetch financial data for a single company via MCP."""
        mcp_result = await self.call_mcp_tool(
            "financial_data", {"company_name": company}
        )
        if "error" in mcp_result:
            return {"company": company, "error": str(mcp_result["error"])}
        content = mcp_result.get("content", mcp_result)
        if isinstance(content, list) and len(content) > 0:
            text_block = content[0] if isinstance(content[0], dict) else {}
            raw = text_block.get("text", json.dumps(content))
        elif isinstance(content, dict):
            raw = content.get("text", json.dumps(content))
        else:
            raw = str(content)
        return {"company": company, "raw": raw}

    async def execute(
        self, input_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        company_name: str = input_data.get(
            "company_name", context.get("company_name", "")
        )
        validation = context.get("validation", {})
        canonical_name = validation.get("canonical_name", company_name)

        competitor_data = context.get("competitor_discovery", {})
        competitors: List[Dict[str, Any]] = competitor_data.get("competitors", [])
        competitor_names = [c.get("name", "") for c in competitors if c.get("name")]

        # Gather financial data for target company
        company_fin = await self._fetch_financial(canonical_name)

        # Gather financial data for competitors
        competitor_fins: List[Dict[str, Any]] = []
        for cname in competitor_names[:5]:  # Limit to top 5
            result = await self._fetch_financial(cname)
            competitor_fins.append(result)

        # Gather supplemental context from earlier pipeline stages
        # Note: financial_research runs before deep_research in the pipeline,
        # so only validation, sector_identification, and competitor_discovery
        # are available at this point.
        sector_data = context.get("sector_identification", {})
        sector = sector_data.get("sector", "")
        comp_data = context.get("competitor_discovery", {})
        supplemental = (
            f"Sector: {sector}\n"
            f"Sub-sectors: {', '.join(sector_data.get('sub_sectors', []))}\n"
            f"Sector reasoning: {sector_data.get('reasoning', '')}\n"
            f"Competitors: {json.dumps([c.get('name') for c in comp_data.get('competitors', [])], default=str)}\n"
        )

        # LLM analysis
        llm_result = await self.call_llm_json(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a financial analyst. Given raw financial data for a "
                        "company and its competitors, plus supplemental research "
                        "context, produce a structured financial comparison. "
                        "Use your knowledge of these companies to provide realistic "
                        "financial figures even if the raw search data is limited. "
                        "Respond in JSON with keys: "
                        '"company_financials" (object with "revenue", "revenue_growth", '
                        '"profit_margin", "market_cap", "employees", "founded", '
                        '"headquarters", "key_metrics" dict), '
                        '"competitor_financials" (list of objects each with "company" '
                        'str plus same fields as company_financials), '
                        '"financial_comparison" (str summary), '
                        '"financial_health_score" (float 0-10).'
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Target company: {canonical_name}\n"
                        f"Sector: {sector}\n"
                        f"Competitors: {', '.join(competitor_names)}\n\n"
                        f"Company financial data: {json.dumps(company_fin)}\n\n"
                        f"Competitor financial data: {json.dumps(competitor_fins)}\n\n"
                        f"Supplemental research context:\n{supplemental}\n\n"
                        "Analyze and compare the financial positions. If raw search "
                        "data is sparse, use the supplemental context and your "
                        "knowledge to provide informed financial estimates."
                    ),
                },
            ]
        )

        return {
            "company_financials": llm_result.get("company_financials", {}),
            "competitor_financials": llm_result.get("competitor_financials", []),
            "financial_comparison": llm_result.get("financial_comparison", ""),
            "financial_health_score": float(
                llm_result.get("financial_health_score", 0.0)
            ),
        }
