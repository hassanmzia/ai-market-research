"""
browse_page tool -- Scrapes a webpage and extracts relevant content
based on provided instructions / keywords.
"""

import logging
import re
from typing import Any, Dict, List

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger("mcp_tools.browse_page")

# ---------------------------------------------------------------------------
# Tool schema
# ---------------------------------------------------------------------------
TOOL_SCHEMA: Dict[str, Any] = {
    "name": "browse_page",
    "description": (
        "Fetches a webpage and extracts relevant text content based on "
        "provided instructions. Removes boilerplate (nav, footer, scripts) "
        "and returns the most relevant paragraphs."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL of the webpage to browse.",
            },
            "instructions": {
                "type": "string",
                "description": (
                    "Instructions describing what information to extract. "
                    "Key terms from instructions are used to rank paragraphs."
                ),
            },
        },
        "required": ["url", "instructions"],
    },
}

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REMOVE_TAGS = ["script", "style", "nav", "footer", "header", "aside", "noscript", "iframe"]
MAX_CONTENT_LENGTH = 5000  # characters returned
REQUEST_TIMEOUT = 15  # seconds
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_keywords(instructions: str) -> List[str]:
    """Extract meaningful keywords from the instructions string."""
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "dare", "ought",
        "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "out", "off", "over", "under", "again",
        "further", "then", "once", "here", "there", "when", "where", "why",
        "how", "all", "both", "each", "few", "more", "most", "other",
        "some", "such", "no", "nor", "not", "only", "own", "same", "so",
        "than", "too", "very", "just", "because", "but", "and", "or",
        "if", "while", "about", "up", "what", "which", "who", "whom",
        "this", "that", "these", "those", "i", "me", "my", "we", "our",
        "you", "your", "he", "him", "his", "she", "her", "it", "its",
        "they", "them", "their", "find", "get", "look", "extract",
        "information", "details", "data", "page", "content",
    }
    words = re.findall(r"[a-zA-Z]+", instructions.lower())
    return [w for w in words if w not in stop_words and len(w) > 2]


def _score_paragraph(text: str, keywords: List[str]) -> int:
    """Score a paragraph based on how many keywords it contains."""
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


# ---------------------------------------------------------------------------
# Tool implementation
# ---------------------------------------------------------------------------
async def run(url: str, instructions: str) -> Dict[str, Any]:
    """Browse *url* and extract content relevant to *instructions*."""
    if not url or not url.strip():
        return {
            "url": url,
            "success": False,
            "content": "",
            "message": "URL is empty.",
        }

    url = url.strip()
    instructions = (instructions or "").strip()
    keywords = _extract_keywords(instructions)

    logger.info("Browsing %s (keywords: %s)", url, keywords[:10])

    # --- Fetch page ---
    try:
        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text
    except httpx.HTTPStatusError as exc:
        return {
            "url": url,
            "success": False,
            "content": "",
            "message": f"HTTP error {exc.response.status_code} fetching URL.",
        }
    except Exception as exc:
        return {
            "url": url,
            "success": False,
            "content": "",
            "message": f"Failed to fetch URL: {exc}",
        }

    # --- Parse HTML ---
    soup = BeautifulSoup(html, "lxml")

    # Remove unwanted elements
    for tag_name in REMOVE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Extract page title
    page_title = soup.title.string.strip() if soup.title and soup.title.string else ""

    # Extract meta description
    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag and meta_tag.get("content"):
        meta_desc = meta_tag["content"].strip()

    # Gather text paragraphs
    paragraphs: List[str] = []
    for element in soup.find_all(["p", "li", "h1", "h2", "h3", "h4", "td", "span", "div"]):
        text = element.get_text(separator=" ", strip=True)
        if text and len(text) > 30:
            paragraphs.append(text)

    # --- Rank paragraphs by relevance ---
    if keywords:
        scored = [(p, _score_paragraph(p, keywords)) for p in paragraphs]
        scored.sort(key=lambda x: x[1], reverse=True)
        relevant = [p for p, score in scored if score > 0]
        # Fall back to all if nothing matched
        if not relevant:
            relevant = paragraphs
    else:
        relevant = paragraphs

    # --- Build output ---
    content_parts: List[str] = []
    if page_title:
        content_parts.append(f"Page Title: {page_title}")
    if meta_desc:
        content_parts.append(f"Description: {meta_desc}")
    content_parts.append("")

    total_len = sum(len(p) for p in content_parts)
    for para in relevant:
        if total_len + len(para) > MAX_CONTENT_LENGTH:
            break
        content_parts.append(para)
        total_len += len(para)

    content = "\n\n".join(content_parts)

    return {
        "url": url,
        "success": True,
        "title": page_title,
        "content": content,
        "paragraphs_found": len(paragraphs),
        "relevant_paragraphs": len(relevant),
        "message": f"Successfully extracted content from {url}",
    }
