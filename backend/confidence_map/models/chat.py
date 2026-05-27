"""Chat request/response models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class FindingRef(BaseModel):
    title: str
    description: str
    confidence: str
    confidence_score: float
    category: str
    agent_name: str
    recommended_action: str


class AgentRef(BaseModel):
    agent_name: str
    summary: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    findings: list[FindingRef] = Field(default_factory=list)
    agents: list[AgentRef] = Field(default_factory=list)
    global_score: float | None = None
    history: list[ChatMessage] = Field(default_factory=list)
