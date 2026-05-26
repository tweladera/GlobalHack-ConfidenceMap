"""Core domain models: findings and agent results."""

from __future__ import annotations

import uuid
from enum import StrEnum

from pydantic import BaseModel, Field


class ConfidenceLevel(StrEnum):
    """Confidence level of a finding.

    GREEN  = explicitly defined in the spec.
    YELLOW = reasonably inferred from context.
    RED    = missing, contradictory, or high uncertainty.
    """

    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class AgentStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


class Finding(BaseModel):
    """A single finding produced by an agent."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    confidence: ConfidenceLevel
    confidence_score: float = Field(ge=0.0, le=1.0)
    evidence: str
    assumptions: list[str] = Field(default_factory=list)
    needs_validation: list[str] = Field(default_factory=list)
    recommended_action: str = ""
    category: str = Field(min_length=1)
    agent_id: str
    agent_name: str


class AgentResult(BaseModel):
    """Complete result from a single agent run."""

    agent_id: str
    agent_name: str
    agent_icon: str
    status: AgentStatus = AgentStatus.PENDING
    findings: list[Finding] = Field(default_factory=list)
    summary: str = ""
    error: str | None = None
