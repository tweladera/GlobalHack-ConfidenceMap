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
from confidence_map.core.translator import translate_agent_results
from confidence_map.models.analysis import (
    AnalysisRequest,
    AnalysisStartResponse,
    TranslateRequest,
    TranslateResponse,
)
from confidence_map.models.events import SSEEvent

router = APIRouter(prefix="/api", tags=["analysis"])

# In-memory store: analysis_id → request
# Production would use Redis or a DB.
_store: dict[str, AnalysisRequest] = {}


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
    In real mode: translates the provided agent results via Claude in parallel (~10-20s).
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
