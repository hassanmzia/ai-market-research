"""Report generation agent -- produces the final comprehensive research report."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ReportAgent(BaseAgent):
    name = "report_agent"
    description = (
        "Generates a comprehensive market research report by synthesising all "
        "collected data from the pipeline into a structured Markdown document "
        "with executive summary, SWOT analysis, and strategic recommendations."
    )
    capabilities: List[str] = [
        "report_generation",
        "data_synthesis",
        "executive_summary",
        "swot_analysis",
        "strategic_recommendations",
    ]
    mcp_tools: List[str] = ["generate_report"]

    def _build_report_context(self, context: Dict[str, Any]) -> str:
        """Build a textual summary of all pipeline results for the LLM."""
        sections: List[str] = []

        validation = context.get("validation", {})
        sections.append(
            f"VALIDATION: Company is {'valid' if validation.get('valid') else 'unverified'}. "
            f"Canonical name: {validation.get('canonical_name', 'N/A')}. "
            f"Details: {validation.get('details', 'N/A')}"
        )

        sector = context.get("sector_identification", {})
        sections.append(
            f"SECTOR: {sector.get('sector', 'N/A')}. "
            f"Sub-sectors: {', '.join(sector.get('sub_sectors', []))}. "
            f"Reasoning: {sector.get('reasoning', 'N/A')}"
        )

        competitors = context.get("competitor_discovery", {})
        comp_list = competitors.get("competitors", [])
        comp_names = [c.get("name", "?") for c in comp_list]
        sections.append(
            f"COMPETITORS: {', '.join(comp_names)}. "
            f"Competitive intensity: {competitors.get('competitive_intensity', 'N/A')}."
        )

        financials = context.get("financial_research", {})
        sections.append(
            f"FINANCIALS: {json.dumps(financials.get('company_financials', {}), default=str)[:1500]}"
        )
        sections.append(
            f"COMPETITOR FINANCIALS: {json.dumps(financials.get('competitor_financials', []), default=str)[:1500]}"
        )

        research = context.get("deep_research", {})
        sections.append(
            f"COMPANY RESEARCH: {json.dumps(research.get('company_data', {}), default=str)[:2000]}"
        )
        sections.append(
            f"MARKET DATA: {json.dumps(research.get('market_data', {}), default=str)[:1500]}"
        )

        sentiment = context.get("sentiment_analysis", {})
        sections.append(
            f"SENTIMENT: Market mood: {sentiment.get('market_mood', 'N/A')}. "
            f"Company: {json.dumps(sentiment.get('company_sentiment', {}), default=str)[:800]}. "
            f"Comparison: {sentiment.get('sentiment_comparison', 'N/A')}"
        )

        trends = context.get("trend_analysis", {})
        sections.append(
            f"TRENDS: Outlook: {trends.get('market_outlook', 'N/A')}. "
            f"Emerging: {json.dumps(trends.get('emerging_trends', []), default=str)[:800]}. "
            f"Opportunities: {json.dumps(trends.get('opportunities', []), default=str)[:800]}"
        )

        return "\n\n".join(sections)

    async def execute(
        self, input_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        company_name: str = input_data.get(
            "company_name", context.get("company_name", "")
        )
        validation = context.get("validation", {})
        canonical_name = validation.get("canonical_name", company_name)

        report_context = self._build_report_context(context)

        # Step 1 -- Try MCP generate_report for any template or baseline
        mcp_result = await self.call_mcp_tool(
            "generate_report",
            {
                "company_name": canonical_name,
                "data": json.dumps(context, default=str)[:8000],
            },
        )
        mcp_report = ""
        if "error" not in mcp_result:
            content = mcp_result.get("content", mcp_result)
            if isinstance(content, list) and len(content) > 0:
                text_block = content[0] if isinstance(content[0], dict) else {}
                mcp_report = text_block.get("text", json.dumps(content))
            elif isinstance(content, dict):
                mcp_report = content.get("text", json.dumps(content))
            else:
                mcp_report = str(content)

        # Step 2 -- Generate comprehensive markdown report via LLM
        report_md = await self.call_llm(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a senior market research analyst producing a comprehensive "
                        "research report. Using ALL the data provided, generate a detailed "
                        "Markdown report. The report MUST include these sections:\n\n"
                        "1. **Executive Summary** - 2-3 paragraph overview\n"
                        "2. **Company Overview** - detailed profile of the target company\n"
                        "3. **Sector Analysis** - industry context and dynamics\n"
                        "4. **Competitor Comparison** - markdown table comparing key metrics\n"
                        "5. **Financial Analysis** - key financial metrics and comparison\n"
                        "6. **Market Sentiment Analysis** - brand perception and media coverage\n"
                        "7. **Trend Analysis** - emerging and declining trends\n"
                        "8. **SWOT Analysis** - Strengths, Weaknesses, Opportunities, Threats\n"
                        "9. **Strategic Recommendations** - numbered actionable recommendations\n"
                        "10. **Actionable Insights** - immediate next steps\n\n"
                        "Use proper Markdown formatting with headers, tables, bullet points, "
                        "and bold text. Be specific and data-driven."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Generate a comprehensive market research report for: {canonical_name}\n\n"
                        f"--- COLLECTED DATA ---\n{report_context}\n\n"
                        f"--- MCP REPORT BASELINE ---\n{mcp_report[:3000]}\n\n"
                        "Produce the full Markdown report now."
                    ),
                },
            ],
            temperature=0.4,
            max_tokens=8192,
        )

        # Step 3 -- Generate structured SWOT and recommendations via LLM JSON
        structured = await self.call_llm_json(
            [
                {
                    "role": "system",
                    "content": (
                        "Extract structured data from the research context. "
                        "Respond in JSON with keys: "
                        '"executive_summary" (str - 2-3 sentences), '
                        '"swot" (object with "strengths" list[str], "weaknesses" list[str], '
                        '"opportunities" list[str], "threats" list[str]), '
                        '"recommendations" (list of {"title": str, "description": str, '
                        '"priority": str high/medium/low, "timeframe": str}), '
                        '"key_metrics" (object with important numerical metrics), '
                        '"risk_score" (float 0-10), '
                        '"opportunity_score" (float 0-10).'
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Company: {canonical_name}\n\n"
                        f"Research data:\n{report_context[:6000]}\n\n"
                        "Extract structured insights."
                    ),
                },
            ]
        )

        return {
            "report_markdown": report_md,
            "executive_summary": structured.get("executive_summary", ""),
            "swot": structured.get("swot", {}),
            "recommendations": structured.get("recommendations", []),
            "key_metrics": structured.get("key_metrics", {}),
            "risk_score": float(structured.get("risk_score", 0.0)),
            "opportunity_score": float(structured.get("opportunity_score", 0.0)),
        }
