"""Validation agent -- verifies that a company name is valid and resolvable."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ValidationAgent(BaseAgent):
    name = "validation_agent"
    description = (
        "Validates company names by cross-referencing MCP tools and LLM reasoning "
        "to ensure the target entity is a real, identifiable company."
    )
    capabilities: List[str] = [
        "company_name_validation",
        "entity_resolution",
        "confidence_scoring",
    ]
    mcp_tools: List[str] = ["validate_company"]

    async def execute(
        self, input_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        company_name: str = input_data.get("company_name", "")
        if not company_name:
            return {
                "valid": False,
                "details": "No company name provided.",
                "confidence": 0.0,
            }

        # Step 1 -- Call MCP validate_company tool
        mcp_result = await self.call_mcp_tool(
            "validate_company", {"company_name": company_name}
        )
        mcp_valid = True
        mcp_details = ""
        if "error" in mcp_result:
            logger.warning("MCP validate_company error: %s", mcp_result["error"])
            mcp_valid = False
            mcp_details = str(mcp_result["error"])
        else:
            content = mcp_result.get("content", mcp_result)
            if isinstance(content, list) and len(content) > 0:
                text_block = content[0] if isinstance(content[0], dict) else {}
                mcp_details = text_block.get("text", json.dumps(content))
            elif isinstance(content, dict):
                # Check the is_valid field from validate_company tool
                if content.get("is_valid") is False:
                    mcp_valid = False
                mcp_details = content.get("text", json.dumps(content))
            else:
                mcp_details = str(content)

        # Step 2 -- LLM reasoning for additional validation
        llm_result = await self.call_llm_json(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a company validation assistant. Given a company name "
                        "and optional MCP tool output, determine whether the company "
                        "is a real, identifiable entity. Respond in JSON with keys: "
                        '"valid" (bool), "details" (str), "confidence" (float 0-1), '
                        '"canonical_name" (str).'
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Company name: {company_name}\n"
                        f"MCP tool output: {mcp_details}\n"
                        f"MCP tool succeeded: {mcp_valid}\n\n"
                        "Please validate this company and provide your assessment."
                    ),
                },
            ]
        )

        valid = llm_result.get("valid", mcp_valid)
        confidence = float(llm_result.get("confidence", 0.5 if mcp_valid else 0.2))
        details = llm_result.get("details", mcp_details)
        canonical_name = llm_result.get("canonical_name", company_name)

        return {
            "valid": valid,
            "details": details,
            "confidence": confidence,
            "canonical_name": canonical_name,
            "mcp_raw": mcp_details,
        }
