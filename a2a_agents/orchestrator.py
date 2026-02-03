"""A2A Multi-Agent Orchestrator for AI Market Research.

This service coordinates specialized agents through a research pipeline,
managing task state in Redis and streaming progress via WebSocket.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import redis.asyncio as aioredis
import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from protocols.a2a_protocol import (
    AgentCard,
    PipelineStage,
    ProgressUpdate,
    ResearchPipeline,
    ResearchTask,
    StageStatus,
    TaskRequest,
    TaskResponse,
)
from agents import (
    BaseAgent,
    CompetitorAgent,
    FinancialAgent,
    ReportAgent,
    ResearchAgent,
    SectorAgent,
    SentimentAgent,
    TrendAgent,
    ValidationAgent,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("orchestrator")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REDIS_URL: str = os.environ.get("REDIS_URL", "redis://redis:6379/0")
MCP_SERVER_URL: str = os.environ.get("MCP_SERVER_URL", "http://mcp-server:7062")
HOST: str = os.environ.get("HOST", "0.0.0.0")
PORT: int = int(os.environ.get("PORT", "7063"))

# ---------------------------------------------------------------------------
# Pipeline definition
# ---------------------------------------------------------------------------
PIPELINE_STAGES: List[Dict[str, str]] = [
    {"name": "validation", "agent": "validation_agent"},
    {"name": "sector_identification", "agent": "sector_agent"},
    {"name": "competitor_discovery", "agent": "competitor_agent"},
    {"name": "financial_research", "agent": "financial_agent"},
    {"name": "deep_research", "agent": "research_agent"},
    {"name": "sentiment_analysis", "agent": "sentiment_agent"},
    {"name": "trend_analysis", "agent": "trend_agent"},
    {"name": "report_generation", "agent": "report_agent"},
]

# ---------------------------------------------------------------------------
# Agent registry
# ---------------------------------------------------------------------------
AGENTS: Dict[str, BaseAgent] = {}


def _register_agents() -> None:
    """Instantiate and register all agents."""
    for cls in (
        ValidationAgent,
        SectorAgent,
        CompetitorAgent,
        FinancialAgent,
        ResearchAgent,
        SentimentAgent,
        TrendAgent,
        ReportAgent,
    ):
        agent = cls()
        agent.connect_to_mcp(MCP_SERVER_URL)
        AGENTS[agent.name] = agent


# ---------------------------------------------------------------------------
# Redis helper
# ---------------------------------------------------------------------------
_redis_pool: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """Return a shared Redis connection."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _redis_pool


# ---------------------------------------------------------------------------
# Task storage (Redis-backed)
# ---------------------------------------------------------------------------
TASK_KEY_PREFIX = "a2a:task:"
PROGRESS_CHANNEL_PREFIX = "a2a:progress:"


async def store_task(task: ResearchTask) -> None:
    """Persist a ResearchTask to Redis."""
    r = await get_redis()
    await r.set(
        f"{TASK_KEY_PREFIX}{task.task_id}",
        task.model_dump_json(),
        ex=86400,  # 24 h TTL
    )


async def load_task(task_id: str) -> Optional[ResearchTask]:
    """Load a ResearchTask from Redis."""
    r = await get_redis()
    raw = await r.get(f"{TASK_KEY_PREFIX}{task_id}")
    if raw is None:
        return None
    return ResearchTask.model_validate_json(raw)


async def publish_progress(update: ProgressUpdate) -> None:
    """Publish a progress update to the Redis pub/sub channel."""
    r = await get_redis()
    channel = f"{PROGRESS_CHANNEL_PREFIX}{update.task_id}"
    await r.publish(channel, update.model_dump_json())


# ---------------------------------------------------------------------------
# WebSocket manager
# ---------------------------------------------------------------------------
class ConnectionManager:
    """Manages active WebSocket connections keyed by task_id."""

    def __init__(self) -> None:
        self._connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, task_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.setdefault(task_id, []).append(ws)

    def disconnect(self, task_id: str, ws: WebSocket) -> None:
        conns = self._connections.get(task_id, [])
        if ws in conns:
            conns.remove(ws)

    async def broadcast(self, task_id: str, message: str) -> None:
        dead: List[WebSocket] = []
        for ws in self._connections.get(task_id, []):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(task_id, ws)


ws_manager = ConnectionManager()

# ---------------------------------------------------------------------------
# Pipeline executor
# ---------------------------------------------------------------------------


async def _send_progress(
    task: ResearchTask,
    stage_name: str,
    status: StageStatus,
    message: str,
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """Helper to publish and broadcast a progress update."""
    update = ProgressUpdate(
        task_id=task.task_id,
        stage_name=stage_name,
        status=status,
        progress=task.pipeline.progress,
        message=message,
        data=data,
    )
    await publish_progress(update)
    await ws_manager.broadcast(task.task_id, update.model_dump_json())


async def run_pipeline(task: ResearchTask) -> None:
    """Execute the full research pipeline sequentially."""
    task.status = StageStatus.RUNNING
    await store_task(task)

    accumulated_context: Dict[str, Any] = {
        "company_name": task.company_name,
        "options": task.options,
    }

    for idx, stage in enumerate(task.pipeline.stages):
        task.pipeline.current_stage = idx
        stage.status = StageStatus.RUNNING
        stage.started_at = time.time()
        await store_task(task)
        await _send_progress(
            task, stage.name, StageStatus.RUNNING,
            f"Starting stage: {stage.name}",
        )

        agent = AGENTS.get(stage.agent_name)
        if agent is None:
            stage.status = StageStatus.FAILED
            stage.error = f"Agent '{stage.agent_name}' not found"
            stage.completed_at = time.time()
            await store_task(task)
            await _send_progress(
                task, stage.name, StageStatus.FAILED,
                f"Agent not found: {stage.agent_name}",
            )
            continue

        request = TaskRequest(
            task_id=task.task_id,
            agent_name=agent.name,
            input_data={"company_name": task.company_name, **task.options},
            context=accumulated_context,
        )

        try:
            response: TaskResponse = await agent.handle_request(request)
        except Exception as exc:
            logger.exception("Unhandled error in agent %s", agent.name)
            response = TaskResponse(
                task_id=task.task_id,
                agent_name=agent.name,
                output_data={},
                status=StageStatus.FAILED,
                error=str(exc),
            )

        stage.duration = response.duration
        stage.completed_at = time.time()

        if response.status == StageStatus.FAILED:
            stage.status = StageStatus.FAILED
            stage.error = response.error
            await store_task(task)
            await _send_progress(
                task, stage.name, StageStatus.FAILED,
                f"Stage failed: {stage.name} - {response.error}",
            )
            # Check for critical failure (validation)
            if stage.name == "validation":
                valid = response.output_data.get("valid", False)
                if not valid:
                    logger.warning(
                        "Validation failed for '%s'; aborting pipeline.",
                        task.company_name,
                    )
                    task.status = StageStatus.FAILED
                    task.completed_at = time.time()
                    await store_task(task)
                    await _send_progress(
                        task, stage.name, StageStatus.FAILED,
                        "Pipeline aborted: company validation failed.",
                    )
                    return
            continue

        # Success
        stage.status = StageStatus.COMPLETED
        stage.result = response.output_data
        accumulated_context[stage.name] = response.output_data
        task.pipeline.results[stage.name] = response.output_data

        await store_task(task)
        await _send_progress(
            task, stage.name, StageStatus.COMPLETED,
            f"Completed stage: {stage.name}",
            data={"duration": response.duration},
        )

        # Special handling: if validation returns valid=False, abort
        if stage.name == "validation":
            valid = response.output_data.get("valid", True)
            if not valid:
                logger.warning(
                    "Company '%s' not valid; aborting pipeline.", task.company_name,
                )
                task.status = StageStatus.FAILED
                task.completed_at = time.time()
                # Mark remaining stages as skipped
                for remaining in task.pipeline.stages[idx + 1:]:
                    remaining.status = StageStatus.SKIPPED
                await store_task(task)
                await _send_progress(
                    task, "validation", StageStatus.FAILED,
                    f"Company '{task.company_name}' could not be validated.",
                )
                return

    # Pipeline complete
    task.status = StageStatus.COMPLETED
    task.completed_at = time.time()
    task.final_report = task.pipeline.results.get("report_generation")
    await store_task(task)
    await _send_progress(
        task, "pipeline", StageStatus.COMPLETED,
        "Research pipeline completed successfully.",
        data={"total_stages": len(task.pipeline.stages)},
    )


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------
class ResearchRequest(BaseModel):
    company_name: str = Field(..., min_length=1, description="Company to research")
    task_id: Optional[str] = Field(
        default=None, description="Optional task ID; auto-generated if omitted"
    )
    options: Dict[str, Any] = Field(
        default_factory=dict, description="Additional research options"
    )


class ResearchStartResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    company_name: str
    status: str
    progress: float
    current_stage: str
    stages: List[Dict[str, Any]]
    created_at: float
    completed_at: Optional[float] = None


class TaskResultResponse(BaseModel):
    task_id: str
    company_name: str
    status: str
    final_report: Optional[Dict[str, Any]] = None
    pipeline_results: Dict[str, Any]
    duration: Optional[float] = None


class AgentInvokeRequest(BaseModel):
    task_id: Optional[str] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    _register_agents()
    logger.info("Registered %d agents: %s", len(AGENTS), list(AGENTS.keys()))
    logger.info("Pipeline stages: %s", [s["name"] for s in PIPELINE_STAGES])
    yield
    # Cleanup
    for agent in AGENTS.values():
        await agent.close()
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None
    logger.info("Orchestrator shut down.")


app = FastAPI(
    title="A2A Market Research Orchestrator",
    description="Multi-agent orchestrator for comprehensive market research.",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    redis_ok = False
    try:
        r = await get_redis()
        await r.ping()
        redis_ok = True
    except Exception:
        pass

    return {
        "status": "healthy",
        "service": "a2a-orchestrator",
        "agents": len(AGENTS),
        "redis_connected": redis_ok,
        "pipeline_stages": len(PIPELINE_STAGES),
    }


@app.post("/a2a/research", response_model=ResearchStartResponse)
async def start_research(request: ResearchRequest) -> ResearchStartResponse:
    """Start a new market research task."""
    task_id = request.task_id or str(uuid.uuid4())

    # Build pipeline stages
    stages = [
        PipelineStage(name=s["name"], agent_name=s["agent"])
        for s in PIPELINE_STAGES
    ]

    task = ResearchTask(
        task_id=task_id,
        company_name=request.company_name,
        options=request.options,
        pipeline=ResearchPipeline(stages=stages),
        status=StageStatus.PENDING,
    )
    await store_task(task)

    # Launch pipeline in background
    asyncio.create_task(run_pipeline(task))

    return ResearchStartResponse(
        task_id=task_id,
        status="started",
        message=f"Research pipeline started for '{request.company_name}' with {len(stages)} stages.",
    )


@app.get("/a2a/research/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """Get the current status and progress of a research task."""
    task = await load_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    current_stage_name = ""
    if 0 <= task.pipeline.current_stage < len(task.pipeline.stages):
        current_stage_name = task.pipeline.stages[task.pipeline.current_stage].name

    stages_info = [
        {
            "name": s.name,
            "agent": s.agent_name,
            "status": s.status.value,
            "duration": s.duration,
            "error": s.error,
        }
        for s in task.pipeline.stages
    ]

    return TaskStatusResponse(
        task_id=task.task_id,
        company_name=task.company_name,
        status=task.status.value,
        progress=task.pipeline.progress,
        current_stage=current_stage_name,
        stages=stages_info,
        created_at=task.created_at,
        completed_at=task.completed_at,
    )


@app.get("/a2a/research/{task_id}/result", response_model=TaskResultResponse)
async def get_task_result(task_id: str) -> TaskResultResponse:
    """Get the final results of a completed research task."""
    task = await load_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    duration = None
    if task.completed_at and task.created_at:
        duration = task.completed_at - task.created_at

    return TaskResultResponse(
        task_id=task.task_id,
        company_name=task.company_name,
        status=task.status.value,
        final_report=task.final_report,
        pipeline_results=task.pipeline.results,
        duration=duration,
    )


@app.post("/a2a/agent/{agent_name}/invoke")
async def invoke_agent(
    agent_name: str, request: AgentInvokeRequest
) -> Dict[str, Any]:
    """Directly invoke a specific agent outside the pipeline."""
    agent = AGENTS.get(agent_name)
    if agent is None:
        raise HTTPException(
            status_code=404, detail=f"Agent '{agent_name}' not found"
        )

    task_id = request.task_id or str(uuid.uuid4())
    task_request = TaskRequest(
        task_id=task_id,
        agent_name=agent_name,
        input_data=request.input_data,
        context=request.context,
    )
    response = await agent.handle_request(task_request)
    return response.model_dump()


@app.get("/a2a/agents")
async def list_agents() -> Dict[str, Any]:
    """List all registered agents with their capabilities (Agent Cards)."""
    cards: List[Dict[str, Any]] = []
    for agent in AGENTS.values():
        cards.append(agent.get_agent_card().model_dump())

    return {
        "agents": cards,
        "total": len(cards),
        "pipeline_order": [s["name"] for s in PIPELINE_STAGES],
    }


@app.websocket("/a2a/ws/{task_id}")
async def websocket_progress(websocket: WebSocket, task_id: str) -> None:
    """WebSocket endpoint for real-time progress streaming."""
    await ws_manager.connect(task_id, websocket)
    try:
        # Also subscribe to Redis pub/sub for this task
        r = await get_redis()
        pubsub = r.pubsub()
        channel = f"{PROGRESS_CHANNEL_PREFIX}{task_id}"
        await pubsub.subscribe(channel)

        # Send current task state immediately
        task = await load_task(task_id)
        if task:
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "initial_state",
                        "task_id": task_id,
                        "status": task.status.value,
                        "progress": task.pipeline.progress,
                        "stages": [
                            {"name": s.name, "status": s.status.value}
                            for s in task.pipeline.stages
                        ],
                    }
                )
            )

        # Listen for Redis messages and relay to WebSocket
        async def relay_redis():
            try:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        await websocket.send_text(message["data"])
            except Exception:
                pass

        relay_task = asyncio.create_task(relay_redis())

        # Keep connection alive; also receive pings from client
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                if data == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except asyncio.TimeoutError:
                # Send keepalive
                try:
                    await websocket.send_text(json.dumps({"type": "keepalive"}))
                except Exception:
                    break

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for task %s", task_id)
    except Exception as exc:
        logger.warning("WebSocket error for task %s: %s", task_id, exc)
    finally:
        ws_manager.disconnect(task_id, websocket)
        try:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()
        except Exception:
            pass
        try:
            relay_task.cancel()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "orchestrator:app",
        host=HOST,
        port=PORT,
        log_level="info",
        reload=False,
    )
