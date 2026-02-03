"""Competitor discovery agent -- identifies key competitors in the same sector."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class CompetitorAgent(BaseAgent):
    name = "competitor_agent"
    description = (
        "Discovers and profiles key competitors for a target company within "
        "its identified sector using MCP tools and LLM analysis."
    )
    capabilities: List[str] = [
        "competitor_identification",
        "competitive_landscape_mapping",
        "market_share_estimation",
    ]
    mcp_tools: List[str] = ["identify_competitors"]

    async def execute(
        self, input_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        company_name: str = input_data.get(
            "company_name", context.get("company_name", "")
        )
        sector_data = context.get("sector_identification", {})
        sector = sector_data.get("sector", input_data.get("sector", "Unknown"))
        validation = context.get("validation", {})
        canonical_name = validation.get("canonical_name", company_name)

        # Step 1 -- MCP identify_competitors
        mcp_result = await self.call_mcp_tool(
            "identify_competitors",
            {"company_name": canonical_name, "sector": sector},
        )
        mcp_competitors = ""
        if "error" not in mcp_result:
            content = mcp_result.get("content", mcp_result)
            if isinstance(content, list) and len(content) > 0:
                text_block = content[0] if isinstance(content[0], dict) else {}
                mcp_competitors = text_block.get("text", json.dumps(content))
            elif isinstance(content, dict):
                mcp_competitors = content.get("text", json.dumps(content))
            else:
                mcp_competitors = str(content)

        # Step 2 -- LLM enrichment
        llm_result = await self.call_llm_json(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a competitive intelligence analyst. Given a company, "
                        "its sector, and raw competitor data, produce a structured "
                        "competitor list. Respond in JSON with keys: "
                        '"competitors" (list of objects with "name", "description", '
                        '"estimated_market_share", "key_strengths"), '
                        '"sector" (str), "total_market_players" (int), '
                        '"competitive_intensity" (str: low/medium/high).'
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Company: {canonical_name}\n"
                        f"Sector: {sector}\n"
                        f"Sub-sectors: {sector_data.get('sub_sectors', [])}\n"
                        f"MCP competitor data: {mcp_competitors}\n\n"
                        "Identify the top competitors and map the competitive landscape."
                    ),
                },
            ]
        )

        competitors = llm_result.get("competitors", [])
        # Ensure each competitor has required fields
        normalized: List[Dict[str, Any]] = []
        for comp in competitors:
            if isinstance(comp, dict):
                normalized.append(
                    {
                        "name": comp.get("name", "Unknown"),
                        "description": comp.get("description", ""),
                        "estimated_market_share": comp.get(
                            "estimated_market_share", "N/A"
                        ),
                        "key_strengths": comp.get("key_strengths", []),
                    }
                )

        return {
            "competitors": normalized,
            "sector": llm_result.get("sector", sector),
            "total_market_players": llm_result.get("total_market_players", 0),
            "competitive_intensity": llm_result.get(
                "competitive_intensity", "medium"
            ),
            "mcp_raw": mcp_competitors,
        }
