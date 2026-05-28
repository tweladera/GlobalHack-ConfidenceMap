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
    thinking: str = ""  # Extended thinking chain-of-thought (empty when ENABLE_THINKING=false)


# ── Consolidator models ────────────────────────────────────────────────────────


class Contradiction(BaseModel):
    """A conflict detected between two or more agent findings on the same topic."""

    topic: str
    agents: list[str]
    description: str
    resolution: str


class ConfirmedCritical(BaseModel):
    """A red finding independently corroborated by two or more agents."""

    topic: str
    agents: list[str]
    combined_evidence: str


class Redundancy(BaseModel):
    """A finding reported by multiple agents that covers the same concern."""

    topic: str
    agents: list[str]
    kept: str  # agent_id of the finding to surface (most complete evidence)


class ConsolidatorResult(BaseModel):
    """Structured output of the Consolidator (cross-agent audit)."""

    contradictions: list[Contradiction] = Field(default_factory=list)
    confirmed_criticals: list[ConfirmedCritical] = Field(default_factory=list)
    redundancies: list[Redundancy] = Field(default_factory=list)
    audit_summary: str = ""
