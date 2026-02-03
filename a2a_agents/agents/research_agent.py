"""Deep research agent -- performs web research for comprehensive market intelligence."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    name = "research_agent"
    description = (
        "Performs deep web research to gather pricing strategies, product offerings, "
        "recent news, and market positioning for a company and its competitors."
    )
    capabilities: List[str] = [
        "web_research",
        "pricing_analysis",
        "product_research",
        "news_gathering",
        "market_positioning",
    ]
    mcp_tools: List[str] = ["browse_page"]

    async def _browse(self, url: str, instructions: str = "Extract relevant company and market information") -> str:
        """Browse a page via MCP and return raw text."""
        result = await self.call_mcp_tool("browse_page", {"url": url, "instructions": instructions})
        if "error" in result:
            return f"[Error browsing {url}: {result['error']}]"
        content = result.get("content", result)
        if isinstance(content, list) and len(content) > 0:
            text_block = content[0] if isinstance(content[0], dict) else {}
            return text_block.get("text", json.dumps(content))
        if isinstance(content, dict):
            return content.get("text", json.dumps(content))
        return str(content)

    async def _research_entity(self, entity_name: str, sector: str) -> Dict[str, Any]:
        """Research a single entity using web browsing and LLM summarisation."""
        # Attempt to browse relevant pages
        search_url = f"https://www.google.com/search?q={entity_name}+{sector}+company+overview"
        news_url = f"https://www.google.com/search?q={entity_name}+latest+news"
        pricing_url = f"https://www.google.com/search?q={entity_name}+pricing+strategy"

        search_content = await self._browse(search_url, f"Extract company overview, products, and market position for {entity_name}")
        news_content = await self._browse(news_url, f"Extract latest news and announcements about {entity_name}")
        pricing_content = await self._browse(pricing_url, f"Extract pricing strategy and business model for {entity_name}")

        # LLM summarisation of gathered content
        llm_result = await self.call_llm_json(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a market research analyst. Given raw web content "
                        "about a company, extract structured intelligence. "
                        "Respond in JSON with keys: "
                        '"overview" (str), "products_services" (list[str]), '
                        '"pricing_strategy" (str), "recent_news" (list of '
                        '{"headline": str, "summary": str}), '
                        '"market_position" (str), "key_differentiators" (list[str]), '
                        '"target_market" (str).'
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Company: {entity_name} (Sector: {sector})\n\n"
                        f"--- Overview content ---\n{search_content[:3000]}\n\n"
                        f"--- News content ---\n{news_content[:2000]}\n\n"
                        f"--- Pricing content ---\n{pricing_content[:2000]}\n\n"
                        "Extract structured market intelligence."
                    ),
                },
            ]
        )
        return llm_result

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

        competitor_data = context.get("competitor_discovery", {})
        competitors: List[Dict[str, Any]] = competitor_data.get("competitors", [])
        competitor_names = [c.get("name", "") for c in competitors if c.get("name")]

        # Research target company
        company_research = await self._research_entity(canonical_name, sector)

        # Research competitors (limit to top 5)
        competitor_research: Dict[str, Any] = {}
        for cname in competitor_names[:5]:
            competitor_research[cname] = await self._research_entity(cname, sector)

        # Market-level research
        market_data = await self.call_llm_json(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a market analyst. Based on the sector and companies "
                        "provided, produce a market-level overview. "
                        "Respond in JSON with keys: "
                        '"market_size" (str), "growth_rate" (str), '
                        '"key_drivers" (list[str]), "barriers_to_entry" (list[str]), '
                        '"regulatory_landscape" (str), "technology_trends" (list[str]).'
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Sector: {sector}\n"
                        f"Target company: {canonical_name}\n"
                        f"Competitors: {', '.join(competitor_names[:5])}\n\n"
                        "Provide a market-level overview for this sector."
                    ),
                },
            ]
        )

        return {
            "company_data": company_research,
            "competitor_data": competitor_research,
            "market_data": market_data,
        }
