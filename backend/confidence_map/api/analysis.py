"""Analysis endpoints: start analysis and stream results via SSE."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from confidence_map.core.orchestrator import stream_analysis
from confidence_map.models.analysis import AnalysisRequest, AnalysisStartResponse
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


async def _sse_generator(request: AnalysisRequest) -> AsyncGenerator[str, None]:
    async for event in stream_analysis(request):
        yield _format_sse(event)


def _format_sse(event: SSEEvent) -> str:
    return f"data: {json.dumps(event.model_dump(exclude_none=True))}\n\n"
