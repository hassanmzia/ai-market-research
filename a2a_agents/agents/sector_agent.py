"""Sector identification agent -- determines industry sector and sub-sectors."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class SectorAgent(BaseAgent):
    name = "sector_agent"
    description = (
        "Identifies the industry sector and sub-sectors for a given company "
        "using MCP tools and LLM-based classification."
    )
    capabilities: List[str] = [
        "sector_identification",
        "industry_classification",
        "sub_sector_analysis",
    ]
    mcp_tools: List[str] = ["identify_sector"]

    async def execute(
        self, input_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        company_name: str = input_data.get(
            "company_name", context.get("company_name", "")
        )
        validation_data = context.get("validation", {})
        canonical_name = validation_data.get("canonical_name", company_name)

        # Step 1 -- MCP identify_sector
        mcp_result = await self.call_mcp_tool(
            "identify_sector", {"company_name": canonical_name}
        )
        mcp_sector = ""
        if "error" not in mcp_result:
            content = mcp_result.get("content", mcp_result)
            if isinstance(content, list) and len(content) > 0:
                text_block = content[0] if isinstance(content[0], dict) else {}
                mcp_sector = text_block.get("text", json.dumps(content))
            elif isinstance(content, dict):
                mcp_sector = content.get("text", json.dumps(content))
            else:
                mcp_sector = str(content)

        # Step 2 -- LLM reasoning
        llm_result = await self.call_llm_json(
            [
                {
                    "role": "system",
                    "content": (
                        "You are an industry classification expert. Given a company "
                        "name and optional sector tool output, identify the primary "
                        "sector, sub-sectors, and SIC/NAICS-style classification. "
                        "Respond in JSON with keys: "
                        '"sector" (str), "sub_sectors" (list[str]), '
                        '"sic_code" (str or null), "naics_code" (str or null), '
                        '"confidence" (float 0-1), "reasoning" (str).'
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Company: {canonical_name}\n"
                        f"MCP sector tool output: {mcp_sector}\n\n"
                        "Identify the sector and sub-sectors for this company."
                    ),
                },
            ]
        )

        return {
            "sector": llm_result.get("sector", "Unknown"),
            "sub_sectors": llm_result.get("sub_sectors", []),
            "sic_code": llm_result.get("sic_code"),
            "naics_code": llm_result.get("naics_code"),
            "confidence": float(llm_result.get("confidence", 0.5)),
            "reasoning": llm_result.get("reasoning", ""),
            "mcp_raw": mcp_sector,
        }
