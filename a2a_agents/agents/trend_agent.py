"""Trend analysis agent -- identifies emerging and declining market trends."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class TrendAgent(BaseAgent):
    name = "trend_agent"
    description = (
        "Analyses market trends using MCP tools and LLM reasoning to identify "
        "emerging opportunities, declining trends, and strategic implications."
    )
    capabilities: List[str] = [
        "trend_analysis",
        "opportunity_identification",
        "market_forecasting",
        "technology_trend_tracking",
    ]
    mcp_tools: List[str] = ["trend_analysis"]

    async def execute(
        self, input_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        company_name: str = input_data.get(
            "company_name", context.get("company_name", "")
        )
        validation = context.get("validation", {})
        canonical_name = validation.get("canonical_name", company_name)

        sector_data = context.get("sector_identification", {})
        sector = sector_data.get("sector", input_data.get("sector", "Unknown"))
        sub_sectors = sector_data.get("sub_sectors", [])

        # Step 1 -- MCP trend_analysis
        mcp_result = await self.call_mcp_tool(
            "trend_analysis",
            {"sector": sector, "company_name": canonical_name},
        )
        mcp_trends = ""
        if "error" not in mcp_result:
            content = mcp_result.get("content", mcp_result)
            if isinstance(content, list) and len(content) > 0:
                text_block = content[0] if isinstance(content[0], dict) else {}
                mcp_trends = text_block.get("text", json.dumps(content))
            elif isinstance(content, dict):
                mcp_trends = content.get("text", json.dumps(content))
            else:
                mcp_trends = str(content)

        # Gather additional context from previous stages
        research_data = context.get("deep_research", {})
        market_data = research_data.get("market_data", {})

        # Step 2 -- LLM deep trend analysis
        llm_result = await self.call_llm_json(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a market trend analyst and futurist. Given sector "
                        "information, MCP trend data, and market research, identify "
                        "and classify trends. Respond in JSON with keys: "
                        '"emerging_trends" (list of {"trend": str, "impact": str '
                        'high/medium/low, "timeline": str, "description": str}), '
                        '"declining_trends" (list of same structure), '
                        '"opportunities" (list of {"opportunity": str, '
                        '"potential_value": str, "difficulty": str, "description": str}), '
                        '"threats" (list of {"threat": str, "severity": str, '
                        '"likelihood": str, "description": str}), '
                        '"technology_shifts" (list[str]), '
                        '"market_outlook" (str), '
                        '"five_year_forecast" (str).'
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Company: {canonical_name}\n"
                        f"Sector: {sector}\n"
                        f"Sub-sectors: {sub_sectors}\n"
                        f"MCP trend data: {mcp_trends}\n"
                        f"Market data: {json.dumps(market_data)[:2000]}\n\n"
                        "Provide comprehensive trend analysis for this sector and company."
                    ),
                },
            ]
        )

        return {
            "emerging_trends": llm_result.get("emerging_trends", []),
            "declining_trends": llm_result.get("declining_trends", []),
            "opportunities": llm_result.get("opportunities", []),
            "threats": llm_result.get("threats", []),
            "technology_shifts": llm_result.get("technology_shifts", []),
            "market_outlook": llm_result.get("market_outlook", ""),
            "five_year_forecast": llm_result.get("five_year_forecast", ""),
            "mcp_raw": mcp_trends,
        }
