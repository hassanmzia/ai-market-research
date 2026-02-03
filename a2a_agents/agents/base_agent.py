"""Base agent class that all specialized agents inherit from."""

from __future__ import annotations

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx
from openai import AsyncOpenAI

from protocols.a2a_protocol import AgentCard, TaskRequest, TaskResponse, StageStatus

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all A2A agents.

    Provides common functionality for MCP tool invocation, LLM reasoning,
    and agent card generation.
    """

    name: str = "base_agent"
    description: str = "Base agent"
    capabilities: List[str] = []
    mcp_tools: List[str] = []
    version: str = "1.0.0"

    def __init__(self) -> None:
        self._mcp_url: str = os.environ.get("MCP_SERVER_URL", "http://mcp-server:7062")
        self._openai_client: Optional[AsyncOpenAI] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        self._model: str = os.environ.get("OPENAI_MODEL", "gpt-4o")

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Return a reusable async HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=httpx.Timeout(120.0))
        return self._http_client

    async def _get_openai_client(self) -> AsyncOpenAI:
        """Return a reusable OpenAI async client."""
        if self._openai_client is None:
            self._openai_client = AsyncOpenAI(
                api_key=os.environ.get("OPENAI_API_KEY", ""),
                base_url=os.environ.get("OPENAI_BASE_URL"),
            )
        return self._openai_client

    async def close(self) -> None:
        """Clean up resources."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    # ------------------------------------------------------------------
    # MCP integration
    # ------------------------------------------------------------------

    def connect_to_mcp(self, url: str) -> None:
        """Set the MCP server URL."""
        self._mcp_url = url

    async def call_mcp_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Invoke a tool on the MCP server via HTTP.

        Args:
            tool_name: The name of the MCP tool to call.
            arguments: A dictionary of arguments to pass to the tool.

        Returns:
            The result dictionary from the MCP server.
        """
        client = await self._get_http_client()
        payload = {
            "name": tool_name,
            "arguments": arguments,
        }
        try:
            response = await client.post(
                f"{self._mcp_url}/mcp/tools/call",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            result = response.json()
            if result.get("status") == "error" or result.get("error"):
                error_msg = result.get("error", "Unknown MCP error")
                logger.error(
                    "MCP tool %s returned error: %s", tool_name, error_msg
                )
                return {"error": error_msg}
            return result.get("result", result)
        except httpx.HTTPStatusError as exc:
            logger.error(
                "MCP HTTP error calling %s: %s %s",
                tool_name,
                exc.response.status_code,
                exc.response.text,
            )
            return {"error": f"HTTP {exc.response.status_code}: {exc.response.text}"}
        except Exception as exc:
            logger.error("MCP call failed for %s: %s", tool_name, exc)
            return {"error": str(exc)}

    # ------------------------------------------------------------------
    # LLM integration
    # ------------------------------------------------------------------

    async def call_llm(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
        response_format: Optional[Dict[str, str]] = None,
    ) -> str:
        """Call the OpenAI-compatible LLM for reasoning.

        Args:
            messages: Chat messages in OpenAI format.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in the response.
            response_format: Optional response format (e.g. {"type": "json_object"}).

        Returns:
            The assistant's reply as a string.
        """
        client = await self._get_openai_client()
        kwargs: Dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        try:
            completion = await client.chat.completions.create(**kwargs)
            return completion.choices[0].message.content or ""
        except Exception as exc:
            logger.error("LLM call failed: %s", exc)
            return json.dumps({"error": str(exc)})

    async def call_llm_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """Convenience wrapper that requests a JSON response and parses it.

        Returns:
            Parsed JSON dictionary, or {"error": ...} on failure.
        """
        raw = await self.call_llm(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("LLM did not return valid JSON: %s", raw[:500])
            return {"raw_response": raw}

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    @abstractmethod
    async def execute(
        self, input_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run the agent's main logic.

        Args:
            input_data: Direct input for this agent.
            context: Accumulated context from earlier pipeline stages.

        Returns:
            A dictionary of result data.
        """
        ...

    async def handle_request(self, request: TaskRequest) -> TaskResponse:
        """Handle a full TaskRequest and produce a TaskResponse."""
        start = time.time()
        try:
            output = await self.execute(request.input_data, request.context)
            duration = time.time() - start
            return TaskResponse(
                task_id=request.task_id,
                agent_name=self.name,
                output_data=output,
                status=StageStatus.COMPLETED,
                duration=duration,
            )
        except Exception as exc:
            duration = time.time() - start
            logger.exception("Agent %s failed on task %s", self.name, request.task_id)
            return TaskResponse(
                task_id=request.task_id,
                agent_name=self.name,
                output_data={},
                status=StageStatus.FAILED,
                duration=duration,
                error=str(exc),
            )

    # ------------------------------------------------------------------
    # Agent card
    # ------------------------------------------------------------------

    def get_agent_card(self) -> AgentCard:
        """Return the agent's public descriptor."""
        return AgentCard(
            name=self.name,
            description=self.description,
            capabilities=self.capabilities,
            endpoint=f"/a2a/agent/{self.name}/invoke",
            version=self.version,
            mcp_tools=self.mcp_tools,
        )
