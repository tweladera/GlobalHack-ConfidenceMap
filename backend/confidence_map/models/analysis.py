"""Models for analysis requests and responses."""

from __future__ import annotations

from pydantic import BaseModel, Field

from confidence_map.models.findings import AgentResult


class AnalysisRequest(BaseModel):
    """Input for starting a new analysis."""

    spec: str = Field(min_length=10, description="Specification text to analyze")
    architecture: str = Field(default="", description="Optional architecture description")
    context: str = Field(default="", description="Optional additional context")
    language: str = Field(default="en", description="Response language: en | es | pt")


class AnalysisStartResponse(BaseModel):
    """Response returned when an analysis is queued."""

    analysis_id: str


class TranslateRequest(BaseModel):
    """Input for translating existing results to a new language."""

    language: str = Field(default="en", description="Target language: en | es | pt")
    agents: list[AgentResult] | None = Field(
        default=None,
        description="Agent results to translate — required in real (non-demo) mode",
    )


class TranslateResponse(BaseModel):
    """Translated agent results."""

    agents: list[AgentResult]


class ConfidenceDistribution(BaseModel):
    """Count of findings per confidence level."""

    green: int = 0
    yellow: int = 0
    red: int = 0

    @property
    def total(self) -> int:
        return self.green + self.yellow + self.red
