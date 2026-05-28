"""SSE event models for streaming analysis results."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel

from confidence_map.models.findings import ConsolidatorResult


class SSEEventType(StrEnum):
    AGENT_START = "agent_start"
    AGENT_COMPLETE = "agent_complete"
    AGENT_ERROR = "agent_error"
    ANALYSIS_COMPLETE = "analysis_complete"
    CONSOLIDATION_START = "consolidation_start"
    CONSOLIDATION_COMPLETE = "consolidation_complete"
    ERROR = "error"


class SSEEvent(BaseModel):
    """A single server-sent event payload."""

    type: SSEEventType
    agent_id: str | None = None
    agent_name: str | None = None
    result: dict[str, Any] | None = None
    total_findings: int | None = None
    confidence_distribution: dict[str, int] | None = None
    global_confidence_score: float | None = None
    consolidation: ConsolidatorResult | None = None
    error: str | None = None
