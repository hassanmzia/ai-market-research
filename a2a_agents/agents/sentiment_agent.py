"""Sentiment analysis agent -- analyses market sentiment for company and competitors."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class SentimentAgent(BaseAgent):
    name = "sentiment_agent"
    description = (
        "Analyses market sentiment for the target company and its competitors "
        "using MCP sentiment tools and LLM-based interpretation."
    )
    capabilities: List[str] = [
        "sentiment_analysis",
        "brand_perception",
        "social_listening",
        "reputation_scoring",
    ]
    mcp_tools: List[str] = ["sentiment_analysis"]

    async def _analyze_sentiment(self, company: str) -> Dict[str, Any]:
        """Get sentiment data for a single company via MCP."""
        mcp_result = await self.call_mcp_tool(
            "sentiment_analysis", {"company_name": company}
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

        # Gather MCP sentiment data
        company_sentiment_raw = await self._analyze_sentiment(canonical_name)
        competitor_sentiments_raw: List[Dict[str, Any]] = []
        for cname in competitor_names[:5]:
            result = await self._analyze_sentiment(cname)
            competitor_sentiments_raw.append(result)

        # LLM deep analysis
        llm_result = await self.call_llm_json(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a market sentiment analyst. Given raw sentiment data "
                        "for a company and its competitors, produce structured sentiment "
                        "analysis. Respond in JSON with keys: "
                        '"company_sentiment" (object with "overall_score" float -1 to 1, '
                        '"label" str positive/neutral/negative, "key_positive_factors" '
                        "list[str], "
                        '"key_negative_factors" list[str], "brand_strength" str, '
                        '"media_coverage" str), '
                        '"competitor_sentiments" (dict mapping company name to same '
                        "structure), "
                        '"market_mood" (str: bullish/bearish/neutral), '
                        '"sentiment_comparison" (str summary), '
                        '"reputation_ranking" (list of company names best to worst).'
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Target company: {canonical_name}\n"
                        f"Company sentiment data: {json.dumps(company_sentiment_raw)}\n\n"
                        f"Competitor sentiment data: {json.dumps(competitor_sentiments_raw)}\n\n"
                        "Provide comprehensive sentiment analysis."
                    ),
                },
            ]
        )

        return {
            "company_sentiment": llm_result.get("company_sentiment", {}),
            "competitor_sentiments": llm_result.get("competitor_sentiments", {}),
            "market_mood": llm_result.get("market_mood", "neutral"),
            "sentiment_comparison": llm_result.get("sentiment_comparison", ""),
            "reputation_ranking": llm_result.get("reputation_ranking", []),
        }
