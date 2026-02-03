"""
MCP (Model Context Protocol) Server for AI Market Research Assistant.

Exposes research tools via HTTP endpoints that agents call using the MCP protocol.
Runs on port 9063 inside Docker.
"""

import os
import json
import logging
import traceback
from typing import Any, Dict, List

import redis.asyncio as aioredis
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from tools.validate_company import run as validate_company, TOOL_SCHEMA as validate_company_schema
from tools.identify_sector import run as identify_sector, TOOL_SCHEMA as identify_sector_schema
from tools.identify_competitors import run as identify_competitors, TOOL_SCHEMA as identify_competitors_schema
from tools.browse_page import run as browse_page, TOOL_SCHEMA as browse_page_schema
from tools.generate_report import run as generate_report, TOOL_SCHEMA as generate_report_schema
from tools.sentiment_analysis import run as sentiment_analysis, TOOL_SCHEMA as sentiment_analysis_schema
from tools.trend_analysis import run as trend_analysis, TOOL_SCHEMA as trend_analysis_schema
from tools.financial_data import run as financial_data, TOOL_SCHEMA as financial_data_schema
from tools.swot_analysis import run as swot_analysis, TOOL_SCHEMA as swot_analysis_schema

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("mcp_server")

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AI Market Research MCP Server",
    description="Model Context Protocol server exposing market-research tools for AI agents.",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# Redis connection (lazy)
# ---------------------------------------------------------------------------
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CACHE_TTL = int(os.getenv("CACHE_TTL", 3600))  # 1 hour default

_redis_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Return a shared async Redis connection, creating it on first call."""
    global _redis_pool
    if _redis_pool is None:
        try:
            _redis_pool = aioredis.from_url(
                REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
            )
            await _redis_pool.ping()
            logger.info("Connected to Redis at %s", REDIS_URL)
        except Exception as exc:
            logger.warning("Redis unavailable (%s). Caching disabled.", exc)
            _redis_pool = None
    return _redis_pool


async def cache_get(key: str) -> str | None:
    """Retrieve a value from Redis cache. Returns None on miss or error."""
    r = await get_redis()
    if r is None:
        return None
    try:
        return await r.get(key)
    except Exception:
        return None


async def cache_set(key: str, value: str, ttl: int = CACHE_TTL) -> None:
    """Store a value in Redis cache with a TTL. Silently ignores errors."""
    r = await get_redis()
    if r is None:
        return
    try:
        await r.set(key, value, ex=ttl)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------
TOOL_FUNCTIONS: Dict[str, Any] = {
    "validate_company": validate_company,
    "identify_sector": identify_sector,
    "identify_competitors": identify_competitors,
    "browse_page": browse_page,
    "generate_report": generate_report,
    "sentiment_analysis": sentiment_analysis,
    "trend_analysis": trend_analysis,
    "financial_data": financial_data,
    "swot_analysis": swot_analysis,
}

TOOL_SCHEMAS: Dict[str, Dict] = {
    "validate_company": validate_company_schema,
    "identify_sector": identify_sector_schema,
    "identify_competitors": identify_competitors_schema,
    "browse_page": browse_page_schema,
    "generate_report": generate_report_schema,
    "sentiment_analysis": sentiment_analysis_schema,
    "trend_analysis": trend_analysis_schema,
    "financial_data": financial_data_schema,
    "swot_analysis": swot_analysis_schema,
}

# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = {}


class ToolCallResponse(BaseModel):
    result: Any = None
    error: str | None = None
    status: str  # "success" or "error"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
async def health():
    """Health-check endpoint."""
    redis_ok = False
    r = await get_redis()
    if r is not None:
        try:
            await r.ping()
            redis_ok = True
        except Exception:
            pass
    return {"status": "healthy", "redis": redis_ok}


@app.post("/mcp/tools/list")
async def list_tools():
    """Return the list of all available tools with their schemas."""
    tools: List[Dict] = []
    for name, schema in TOOL_SCHEMAS.items():
        tools.append(
            {
                "name": name,
                "description": schema.get("description", ""),
                "inputSchema": schema.get("parameters", {}),
            }
        )
    return {"tools": tools}


@app.post("/mcp/tools/call")
async def call_tool(request: ToolCallRequest):
    """Call a tool by name with the provided arguments."""
    tool_name = request.name
    arguments = request.arguments

    if tool_name not in TOOL_FUNCTIONS:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_name}' not found. Available tools: {list(TOOL_FUNCTIONS.keys())}",
        )

    logger.info("Calling tool '%s' with arguments: %s", tool_name, arguments)

    # --- Check cache ---
    cache_key = f"mcp:tool:{tool_name}:{json.dumps(arguments, sort_keys=True)}"
    cached = await cache_get(cache_key)
    if cached is not None:
        logger.info("Cache hit for '%s'", tool_name)
        return ToolCallResponse(
            result=json.loads(cached),
            status="success",
        )

    # --- Execute tool ---
    try:
        func = TOOL_FUNCTIONS[tool_name]
        result = await func(**arguments)

        # Cache the result
        try:
            await cache_set(cache_key, json.dumps(result))
        except Exception:
            pass  # caching is best-effort

        logger.info("Tool '%s' completed successfully", tool_name)
        return ToolCallResponse(result=result, status="success")
    except Exception as exc:
        tb = traceback.format_exc()
        logger.error("Tool '%s' failed: %s\n%s", tool_name, exc, tb)
        return ToolCallResponse(error=str(exc), status="error")


# ---------------------------------------------------------------------------
# Startup / shutdown
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def on_startup():
    logger.info("MCP Server starting up ...")
    await get_redis()  # warm the connection


@app.on_event("shutdown")
async def on_shutdown():
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.close()
        _redis_pool = None
    logger.info("MCP Server shut down.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("MCP_PORT", 9063))
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=False,
    )
