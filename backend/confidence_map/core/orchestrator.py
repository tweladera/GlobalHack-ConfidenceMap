"""Multi-agent orchestrator: Spec Analyst first, then 5 agents in parallel."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Coroutine
from typing import Any, Protocol

from confidence_map.agents import (
    accessibility_advocate,
    arch_validator,
    business_impact,
    delivery_historian,
    risk_intelligence,
    spec_analyst,
)
from confidence_map.core.mock_results import AGENT_DELAYS, get_mock_results
from confidence_map.core.settings import get_settings
from confidence_map.models.analysis import AnalysisRequest, ConfidenceDistribution
from confidence_map.models.events import SSEEvent, SSEEventType
from confidence_map.models.findings import AgentResult


class _AgentModule(Protocol):
    AGENT_ID: str
    AGENT_NAME: str

    def run(
        self, spec: str, architecture: str, context: str, language: str
    ) -> Coroutine[Any, Any, AgentResult]: ...


_AGENT_NAMES: dict[str, str] = {
    "spec_analyst": "Spec Analyst",
    "arch_validator": "Architecture Validator",
    "risk_intelligence": "Risk Intelligence",
    "business_impact": "Business Impact",
    "accessibility_advocate": "Accessibility Advocate",
    "delivery_historian": "Delivery Historian",
}

_PHASE2_AGENTS = [
    "arch_validator",
    "risk_intelligence",
    "business_impact",
    "accessibility_advocate",
    "delivery_historian",
]


async def _stream_mock_analysis(language: str = "en") -> AsyncGenerator[SSEEvent, None]:
    """Emit pre-generated NovaBank mock results with simulated timing."""
    mock_results = get_mock_results(language)
    queue: asyncio.Queue[SSEEvent | None] = asyncio.Queue()

    async def emit_agent(agent_id: str) -> None:
        agent_name = _AGENT_NAMES[agent_id]
        result = mock_results[agent_id]
        await queue.put(
            SSEEvent(type=SSEEventType.AGENT_START, agent_id=agent_id, agent_name=agent_name)
        )
        await asyncio.sleep(AGENT_DELAYS.get(agent_id, 2.0))
        event_type = (
            SSEEventType.AGENT_COMPLETE if result.error is None else SSEEventType.AGENT_ERROR
        )
        await queue.put(
            SSEEvent(
                type=event_type,
                agent_id=agent_id,
                agent_name=agent_name,
                result=result.model_dump(),
                error=result.error,
            )
        )

    async def orchestrate() -> None:
        await emit_agent("spec_analyst")
        await asyncio.gather(*(emit_agent(aid) for aid in _PHASE2_AGENTS))
        await queue.put(None)

    task = asyncio.create_task(orchestrate())
    dist = ConfidenceDistribution()
    total_findings = 0
    all_scores: list[float] = []

    try:
        while True:
            event = await asyncio.wait_for(queue.get(), timeout=120.0)
            if event is None:
                break
            if event.type == SSEEventType.AGENT_COMPLETE and event.result:
                for f in event.result.get("findings", []):
                    total_findings += 1
                    all_scores.append(float(f.get("confidence_score", 0.5)))
                    match f.get("confidence"):
                        case "green":
                            dist.green += 1
                        case "yellow":
                            dist.yellow += 1
                        case "red":
                            dist.red += 1
            yield event
    except TimeoutError:
        yield SSEEvent(type=SSEEventType.ERROR, error="Analysis timed out after 120 seconds")
        return
    finally:
        if not task.done():
            task.cancel()

    global_score = round(sum(all_scores) / len(all_scores), 3) if all_scores else 0.0
    yield SSEEvent(
        type=SSEEventType.ANALYSIS_COMPLETE,
        total_findings=total_findings,
        confidence_distribution={"green": dist.green, "yellow": dist.yellow, "red": dist.red},
        global_confidence_score=global_score,
    )


async def stream_analysis(request: AnalysisRequest) -> AsyncGenerator[SSEEvent, None]:
    """Orchestrate 6 agents and yield SSE events as each one completes.

    Phase 1: Spec Analyst runs alone (its output informs the parallel phase).
    Phase 2: Five remaining agents run concurrently via asyncio.gather.
    """
    if get_settings().demo_mode:
        async for mock_event in _stream_mock_analysis(request.language):
            yield mock_event
        return

    queue: asyncio.Queue[SSEEvent | None] = asyncio.Queue()

    async def run(
        agent_module: _AgentModule,
        agent_id: str,
        agent_name: str,
    ) -> None:
        await queue.put(
            SSEEvent(type=SSEEventType.AGENT_START, agent_id=agent_id, agent_name=agent_name)
        )
        result: AgentResult = await agent_module.run(
            spec=request.spec,
            architecture=request.architecture,
            context=request.context,
            language=request.language,
        )
        event_type = (
            SSEEventType.AGENT_COMPLETE
            if result.error is None
            else SSEEventType.AGENT_ERROR
        )
        await queue.put(
            SSEEvent(
                type=event_type,
                agent_id=agent_id,
                agent_name=agent_name,
                result=result.model_dump(),
                error=result.error,
            )
        )

    async def orchestrate() -> None:
        await run(spec_analyst, spec_analyst.AGENT_ID, spec_analyst.AGENT_NAME)
        await asyncio.gather(
            run(arch_validator, arch_validator.AGENT_ID, arch_validator.AGENT_NAME),
            run(risk_intelligence, risk_intelligence.AGENT_ID, risk_intelligence.AGENT_NAME),
            run(business_impact, business_impact.AGENT_ID, business_impact.AGENT_NAME),
            run(
                accessibility_advocate,
                accessibility_advocate.AGENT_ID,
                accessibility_advocate.AGENT_NAME,
            ),
            run(delivery_historian, delivery_historian.AGENT_ID, delivery_historian.AGENT_NAME),
        )
        await queue.put(None)  # sentinel

    task = asyncio.create_task(orchestrate())
    dist = ConfidenceDistribution()
    total_findings = 0
    all_scores: list[float] = []

    try:
        while True:
            event: SSEEvent | None = await asyncio.wait_for(queue.get(), timeout=120.0)
            if event is None:
                break

            if event.type == SSEEventType.AGENT_COMPLETE and event.result:
                for f in event.result.get("findings", []):
                    total_findings += 1
                    all_scores.append(float(f.get("confidence_score", 0.5)))
                    match f.get("confidence"):
                        case "green":
                            dist.green += 1
                        case "yellow":
                            dist.yellow += 1
                        case "red":
                            dist.red += 1

            yield event

    except TimeoutError:
        yield SSEEvent(type=SSEEventType.ERROR, error="Analysis timed out after 120 seconds")
        return
    finally:
        if not task.done():
            task.cancel()

    global_score = round(sum(all_scores) / len(all_scores), 3) if all_scores else 0.0

    yield SSEEvent(
        type=SSEEventType.ANALYSIS_COMPLETE,
        total_findings=total_findings,
        confidence_distribution={"green": dist.green, "yellow": dist.yellow, "red": dist.red},
        global_confidence_score=global_score,
    )
