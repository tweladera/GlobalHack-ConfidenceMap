"""Chat endpoint: conversational Q&A over analysis findings via Claude streaming."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator

import anthropic
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from confidence_map.core.settings import get_settings
from confidence_map.models.chat import ChatRequest

router = APIRouter(prefix="/api", tags=["chat"])

# Cap findings sent to Claude to avoid context overflow on large analyses.
# Findings are sorted red → yellow → green so critical items are never dropped.
_MAX_FINDINGS_IN_PROMPT = 20

_DEMO_RESPONSE = (
    "The most critical risk is the **SLA contradiction** flagged by the Architecture Validator.\n\n"
    "The spec requires a 2-second response time, but the proposed architecture relies on a "
    "synchronous call to a legacy payment gateway with no documented latency SLA. "
    "These two constraints are incompatible — and no one has made that decision explicitly yet.\n\n"
    "Fix this before writing a single line of code:\n"
    "1. Define the gateway's actual p99 latency with the vendor.\n"
    "2. Decide: async processing with a callback, or a different gateway.\n\n"
    "The **idempotency gap** in the retry strategy is a close second — "
    "duplicate payments are a production incident waiting to happen."
)


_CONFIDENCE_PRIORITY: dict[str, int] = {"red": 0, "yellow": 1, "green": 2}


def _build_system_prompt(request: ChatRequest) -> str:
    # Prioritize critical findings; cap to avoid context overflow
    findings = sorted(request.findings, key=lambda f: _CONFIDENCE_PRIORITY.get(f.confidence, 3))
    findings = findings[:_MAX_FINDINGS_IN_PROMPT]
    findings_text = "\n".join(
        f"- [{f.confidence.upper()}] {f.title} ({f.agent_name}, {f.category}): "
        f"{f.description} → Action: {f.recommended_action}"
        for f in findings
    )
    agent_summaries = "\n".join(
        f"- {a.agent_name}: {a.summary}" for a in request.agents if a.summary
    )
    score_text = (
        f"Global confidence score: {round(request.global_score * 100)}%"
        if request.global_score is not None
        else ""
    )
    return (
        "You are an expert software architecture advisor helping a team understand "
        "the results of an automated confidence analysis of their specification.\n\n"
        f"{score_text}\n\n"
        "Agent summaries:\n"
        f"{agent_summaries}\n\n"
        "All findings:\n"
        f"{findings_text}\n\n"
        "Answer concisely and practically. Focus on actionable guidance. "
        "Use markdown formatting where helpful. Reference specific findings by title when relevant."
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    """Stream a conversational response about the analysis findings."""
    settings = get_settings()
    if settings.demo_mode:
        return StreamingResponse(
            _demo_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    return StreamingResponse(
        _claude_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


async def _demo_generator() -> AsyncGenerator[str, None]:
    words = _DEMO_RESPONSE.split(" ")
    for i, word in enumerate(words):
        chunk = word + (" " if i < len(words) - 1 else "")
        yield f"data: {json.dumps({'text': chunk})}\n\n"
        await asyncio.sleep(0.03)
    yield 'data: {"type": "complete"}\n\n'


async def _claude_generator(request: ChatRequest) -> AsyncGenerator[str, None]:
    settings = get_settings()
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    system = _build_system_prompt(request)
    messages: list[anthropic.types.MessageParam] = [
        {"role": m.role, "content": m.content} for m in request.history
    ]
    messages.append({"role": "user", "content": request.question})

    try:
        async with client.messages.stream(
            model=settings.model,
            max_tokens=1024,
            system=system,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield f"data: {json.dumps({'text': text})}\n\n"
        yield 'data: {"type": "complete"}\n\n'
    except anthropic.APIError as exc:
        yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
