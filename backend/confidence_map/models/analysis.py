"""Models for analysis requests and responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    """Input for starting a new analysis."""

    spec: str = Field(min_length=10, description="Specification text to analyze")
    architecture: str = Field(default="", description="Optional architecture description")
    context: str = Field(default="", description="Optional additional context")
    language: str = Field(default="en", description="Response language: en | es | pt")


class AnalysisStartResponse(BaseModel):
    """Response returned when an analysis is queued."""

    analysis_id: str


class ConfidenceDistribution(BaseModel):
    """Count of findings per confidence level."""

    green: int = 0
    yellow: int = 0
    red: int = 0

    @property
    def total(self) -> int:
        return self.green + self.yellow + self.red
