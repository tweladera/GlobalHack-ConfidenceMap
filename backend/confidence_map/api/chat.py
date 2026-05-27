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

_DEMO_RESPONSE = (
    "Based on this analysis, here are the key insights.\n\n"
    "The findings reveal a complex risk landscape. Critical items (marked red) "
    "indicate areas where the specification lacks explicit definition — these "
    "should be resolved before implementation begins.\n\n"
    "I recommend the following approach:\n"
    "1. **Address the critical findings first** — schedule a refinement session "
    "focused on resolving high-uncertainty items.\n"
    "2. **Make implicit decisions explicit** — update the specification to document "
    "the assumptions identified by the agents.\n"
    "3. **Prioritize architectural decisions** that would block parallel work streams.\n\n"
    "A confidence score below 60% typically means the spec needs at least one more "
    "refinement pass before it is implementation-ready. The goal is to move red "
    "findings to yellow (inferred) or green (confirmed) through deliberate "
    "clarification work."
)


def _build_system_prompt(request: ChatRequest) -> str:
    findings_text = "\n".join(
        f"- [{f.confidence.upper()}] {f.title} ({f.agent_name}, {f.category}): "
        f"{f.description} → Action: {f.recommended_action}"
        for f in request.findings
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
    except Exception as exc:
        yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
