"""Analysis endpoints: start analysis and stream results via SSE."""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from confidence_map.core.mock_results import get_mock_results
from confidence_map.core.orchestrator import stream_analysis
from confidence_map.core.settings import get_settings
from confidence_map.core.translator import translate_agent_results, translate_one_agent
from confidence_map.models.analysis import (
    AnalysisRequest,
    AnalysisStartResponse,
    TranslateRequest,
    TranslateResponse,
)
from confidence_map.models.events import SSEEvent
from confidence_map.models.findings import AgentResult

router = APIRouter(prefix="/api", tags=["analysis"])

# In-memory store: analysis_id → request
# Production would use Redis or a DB.
_store: dict[str, AnalysisRequest] = {}

# In-memory store: translate_id → (agents, language)
_translate_store: dict[str, tuple[list[AgentResult], str]] = {}


@router.post("/analyze", response_model=AnalysisStartResponse, status_code=202)
async def start_analysis(request: AnalysisRequest) -> AnalysisStartResponse:
    """Queue a new analysis and return its ID for streaming."""
    analysis_id = str(uuid.uuid4())
    _store[analysis_id] = request
    return AnalysisStartResponse(analysis_id=analysis_id)


@router.get("/analyze/{analysis_id}/stream")
async def stream_analysis_results(analysis_id: str) -> StreamingResponse:
    """Stream analysis events as Server-Sent Events."""
    request = _store.get(analysis_id)
    if request is None:
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found")

    return StreamingResponse(
        _sse_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/translate", response_model=TranslateResponse)
async def translate_results(request: TranslateRequest) -> TranslateResponse:
    """Return translated results for the given language.

    In DEMO_MODE: returns pre-generated mock results instantly (< 100ms).
    In real mode: use /translate/stream to avoid proxy timeouts.
    """
    settings = get_settings()
    if settings.demo_mode:
        agents_dict = get_mock_results(request.language)
        return TranslateResponse(agents=list(agents_dict.values()))
    if request.agents is None:
        raise HTTPException(
            status_code=400,
            detail="agents field is required for translation in real mode",
        )
    translated = await translate_agent_results(request.agents, request.language)
    return TranslateResponse(agents=translated)


@router.post("/translate/stream")
async def translate_results_stream(request: TranslateRequest) -> StreamingResponse:
    """Stream translation results as SSE events with keepalive.

    Avoids Next.js dev proxy timeouts by sending keepalive pings every 5s.
    Each agent emits an event when its translation completes.
    In DEMO_MODE: emits all agents instantly (no Claude calls).
    """
    settings = get_settings()

    if settings.demo_mode:
        agents_list = list(get_mock_results(request.language).values())
        return StreamingResponse(
            _translate_demo_generator(agents_list),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    if request.agents is None:
        raise HTTPException(
            status_code=400,
            detail="agents field is required for translation in real mode",
        )

    return StreamingResponse(
        _translate_sse_generator(request.agents, request.language),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/translate/prepare", status_code=202)
async def prepare_translate(request: TranslateRequest) -> dict[str, str]:
    """Store a translation request and return a translate_id for GET SSE streaming.

    This avoids POST SSE proxy-buffering issues in the Next.js dev environment.
    The stored entry is consumed (deleted) when the stream endpoint is called.
    """
    settings = get_settings()
    translate_id = str(uuid.uuid4())
    if settings.demo_mode:
        _translate_store[translate_id] = ([], request.language)
    else:
        if request.agents is None:
            raise HTTPException(
                status_code=400,
                detail="agents field is required for translation in real mode",
            )
        _translate_store[translate_id] = (request.agents, request.language)
    return {"translate_id": translate_id}


@router.get("/translate/{translate_id}/stream")
async def stream_translate_by_id(translate_id: str) -> StreamingResponse:
    """Stream translation results as SSE events (GET — EventSource-compatible).

    In DEMO_MODE: emits all mock agents instantly.
    In real mode: translates agents in parallel via Claude, one SSE event per agent.
    Keepalive pings prevent proxy/browser from closing an idle connection.
    """
    entry = _translate_store.pop(translate_id, None)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Translate session '{translate_id}' not found")
    agents, language = entry
    settings = get_settings()
    if settings.demo_mode:
        agents_list = list(get_mock_results(language).values())
        return StreamingResponse(
            _translate_demo_generator(agents_list),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    return StreamingResponse(
        _translate_sse_generator(agents, language),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


async def _translate_demo_generator(
    agents: list[AgentResult],
) -> AsyncGenerator[str, None]:
    for agent in agents:
        yield _format_translate_event(agent)
    yield "data: {\"type\": \"complete\"}\n\n"


async def _translate_sse_generator(
    agents: list[AgentResult], language: str
) -> AsyncGenerator[str, None]:
    """Translate agents in parallel, streaming each result as it completes."""
    queue: asyncio.Queue[AgentResult | None] = asyncio.Queue()

    async def _translate_and_enqueue(agent: AgentResult) -> None:
        result = await translate_one_agent(agent, language)
        await queue.put(result)

    async def _run_all() -> None:
        await asyncio.gather(*(_translate_and_enqueue(a) for a in agents))
        await queue.put(None)  # sentinel

    task = asyncio.create_task(_run_all())
    # Flush a real data event immediately so the Next.js dev proxy doesn't timeout
    # before the first Claude translation completes (30-60s).
    yield "data: {\"type\": \"started\"}\n\n"

    try:
        while True:
            try:
                agent = await asyncio.wait_for(queue.get(), timeout=5.0)
                if agent is None:
                    break
                yield _format_translate_event(agent)
            except TimeoutError:
                # Real data event (not a comment) so the proxy forwards it and resets its timer.
                yield "data: {\"type\": \"keepalive\"}\n\n"
        yield "data: {\"type\": \"complete\"}\n\n"
    finally:
        if not task.done():
            task.cancel()


def _format_translate_event(agent: AgentResult) -> str:
    payload = {
        "type": "agent_translated",
        "agent_id": agent.agent_id,
        "findings": [f.model_dump() for f in agent.findings],
        "summary": agent.summary,
    }
    return f"data: {json.dumps(payload)}\n\n"


async def _sse_generator(request: AnalysisRequest) -> AsyncGenerator[str, None]:
    """Yield SSE events with keepalive comments to flush proxy buffers.

    Next.js dev proxy (and nginx/other proxies) may buffer chunks until a
    certain size is reached. Sending a SSE comment (`:keepalive`) every few
    seconds forces a flush so the browser receives events in real time.
    """
    event_queue: asyncio.Queue[str | None] = asyncio.Queue()

    async def _pump() -> None:
        async for event in stream_analysis(request):
            await event_queue.put(_format_sse(event))
        await event_queue.put(None)  # sentinel

    pump_task = asyncio.create_task(_pump())

    try:
        while True:
            try:
                chunk = await asyncio.wait_for(event_queue.get(), timeout=5.0)
                if chunk is None:
                    break
                yield chunk
            except TimeoutError:
                yield ":keepalive\n\n"  # SSE comment — ignored by EventSource, flushes proxy
    finally:
        if not pump_task.done():
            pump_task.cancel()


def _format_sse(event: SSEEvent) -> str:
    return f"data: {json.dumps(event.model_dump(exclude_none=True))}\n\n"
