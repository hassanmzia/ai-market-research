"""A2A (Agent-to-Agent) protocol data models for the market research orchestrator."""

from __future__ import annotations

import time
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StageStatus(str, Enum):
    """Status of a pipeline stage."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AgentCard(BaseModel):
    """Describes an agent's identity, capabilities, and endpoint information."""

    name: str = Field(..., description="Unique agent identifier")
    description: str = Field(..., description="Human-readable agent description")
    capabilities: List[str] = Field(
        default_factory=list, description="List of capabilities this agent provides"
    )
    endpoint: str = Field(
        default="", description="HTTP endpoint for direct invocation"
    )
    version: str = Field(default="1.0.0", description="Agent version")
    mcp_tools: List[str] = Field(
        default_factory=list, description="MCP tools this agent uses"
    )


class TaskRequest(BaseModel):
    """Request payload sent to an agent for execution."""

    task_id: str = Field(..., description="Unique task identifier")
    agent_name: str = Field(..., description="Target agent name")
    input_data: Dict[str, Any] = Field(
        default_factory=dict, description="Input data for the agent"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Accumulated context from previous pipeline stages",
    )
    options: Dict[str, Any] = Field(
        default_factory=dict, description="Optional execution parameters"
    )


class TaskResponse(BaseModel):
    """Response payload returned by an agent after execution."""

    task_id: str = Field(..., description="Unique task identifier")
    agent_name: str = Field(..., description="Agent that produced this response")
    output_data: Dict[str, Any] = Field(
        default_factory=dict, description="Agent output data"
    )
    status: StageStatus = Field(
        default=StageStatus.COMPLETED, description="Execution status"
    )
    duration: float = Field(
        default=0.0, description="Execution duration in seconds"
    )
    error: Optional[str] = Field(
        default=None, description="Error message if execution failed"
    )
    timestamp: float = Field(
        default_factory=time.time, description="Unix timestamp of completion"
    )


class PipelineStage(BaseModel):
    """Represents a single stage in the research pipeline."""

    name: str = Field(..., description="Stage name / identifier")
    agent_name: str = Field(..., description="Agent responsible for this stage")
    status: StageStatus = Field(
        default=StageStatus.PENDING, description="Current stage status"
    )
    result: Optional[Dict[str, Any]] = Field(
        default=None, description="Stage result data"
    )
    error: Optional[str] = Field(
        default=None, description="Error message if stage failed"
    )
    duration: float = Field(default=0.0, description="Stage duration in seconds")
    started_at: Optional[float] = Field(
        default=None, description="Unix timestamp when stage started"
    )
    completed_at: Optional[float] = Field(
        default=None, description="Unix timestamp when stage completed"
    )


class ResearchPipeline(BaseModel):
    """Represents the full research pipeline with ordered stages."""

    stages: List[PipelineStage] = Field(
        default_factory=list, description="Ordered list of pipeline stages"
    )
    current_stage: int = Field(
        default=0, description="Index of the currently executing stage"
    )
    results: Dict[str, Any] = Field(
        default_factory=dict,
        description="Accumulated results keyed by stage name",
    )

    @property
    def progress(self) -> float:
        """Calculate overall pipeline progress as a percentage."""
        if not self.stages:
            return 0.0
        completed = sum(
            1
            for s in self.stages
            if s.status in (StageStatus.COMPLETED, StageStatus.SKIPPED)
        )
        return round((completed / len(self.stages)) * 100, 1)

    @property
    def is_complete(self) -> bool:
        """Check whether every stage has finished (completed, failed, or skipped)."""
        return all(
            s.status
            in (StageStatus.COMPLETED, StageStatus.FAILED, StageStatus.SKIPPED)
            for s in self.stages
        )


class ProgressUpdate(BaseModel):
    """Real-time progress update published via WebSocket / Redis pub/sub."""

    task_id: str
    stage_name: str
    status: StageStatus
    progress: float = Field(
        default=0.0, description="Overall pipeline progress percentage"
    )
    message: str = Field(default="", description="Human-readable status message")
    data: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional partial result data"
    )
    timestamp: float = Field(default_factory=time.time)


class ResearchTask(BaseModel):
    """Top-level research task that the orchestrator manages."""

    task_id: str = Field(..., description="Unique task identifier")
    company_name: str = Field(..., description="Target company for research")
    options: Dict[str, Any] = Field(
        default_factory=dict, description="Task-level options"
    )
    pipeline: ResearchPipeline = Field(
        default_factory=ResearchPipeline,
        description="The research pipeline for this task",
    )
    status: StageStatus = Field(
        default=StageStatus.PENDING, description="Overall task status"
    )
    created_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = Field(default=None)
    final_report: Optional[Dict[str, Any]] = Field(
        default=None, description="Final consolidated report"
    )
