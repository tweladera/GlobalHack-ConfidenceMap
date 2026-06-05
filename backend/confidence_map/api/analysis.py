"""Analysis endpoints: start analysis and stream results via SSE."""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from confidence_map.core.orchestrator import stream_analysis
from confidence_map.core.settings import get_settings
from confidence_map.models.analysis import AnalysisRequest, AnalysisStartResponse
from confidence_map.models.events import SSEEvent

router = APIRouter(prefix="/api", tags=["analysis"])

# TTL-based in-memory store: analysis_id → request
# Entries expire after _TTL_SECONDS to avoid unbounded memory growth.
# Production would use Redis or a DB for persistence across restarts.
_TTL_SECONDS = 300  # 5 minutes — enough for any real analysis run


@dataclass
class _StoreEntry:
    request: AnalysisRequest
    expires_at: float


_store: dict[str, _StoreEntry] = {}


def _store_put(analysis_id: str, request: AnalysisRequest) -> None:
    """Store a request with TTL. Lazily evicts expired entries on write."""
    now = time.monotonic()
    expired = [k for k, v in _store.items() if v.expires_at < now]
    for k in expired:
        del _store[k]
    _store[analysis_id] = _StoreEntry(request=request, expires_at=now + _TTL_SECONDS)


def _store_get(analysis_id: str) -> AnalysisRequest | None:
    """Return the stored request if it exists and has not expired."""
    entry = _store.get(analysis_id)
    if entry is None:
        return None
    if time.monotonic() > entry.expires_at:
        del _store[analysis_id]
        return None
    return entry.request


@router.post("/analyze", response_model=AnalysisStartResponse, status_code=202)
async def start_analysis(request: AnalysisRequest) -> AnalysisStartResponse:
    """Queue a new analysis and return its ID for streaming."""
    analysis_id = str(uuid.uuid4())
    _store_put(analysis_id, request)
    return AnalysisStartResponse(analysis_id=analysis_id, demo_mode=get_settings().demo_mode)


@router.get("/analyze/{analysis_id}/stream")
async def stream_analysis_results(analysis_id: str) -> StreamingResponse:
    """Stream analysis events as Server-Sent Events."""
    request = _store_get(analysis_id)
    if request is None:
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found")

    return StreamingResponse(
        _sse_generator(request, analysis_id=analysis_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


async def _sse_generator(
    request: AnalysisRequest, *, analysis_id: str = ""
) -> AsyncGenerator[str, None]:
    """Yield SSE events with keepalive comments to flush proxy buffers.

    Next.js dev proxy (and nginx/other proxies) may buffer chunks until a
    certain size is reached. Sending a SSE comment (`:keepalive`) every few
    seconds forces a flush so the browser receives events in real time.
    """
    event_queue: asyncio.Queue[str | None] = asyncio.Queue()

    async def _pump() -> None:
        async for event in stream_analysis(request, analysis_id=analysis_id):
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
