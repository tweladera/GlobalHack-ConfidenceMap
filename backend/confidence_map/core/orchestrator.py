"""Multi-agent orchestrator: Spec Analyst first, then 5 agents in parallel."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncGenerator, Coroutine
from typing import Any, Protocol

from confidence_map.agents import (
    accessibility_advocate,
    arch_validator,
    business_impact,
    consolidator,
    delivery_historian,
    risk_intelligence,
    spec_analyst,
)
from confidence_map.core.mock_results import AGENT_DELAYS, get_mock_consolidation, get_mock_results
from confidence_map.core.settings import get_settings
from confidence_map.models.analysis import AnalysisRequest, ConfidenceDistribution
from confidence_map.models.events import SSEEvent, SSEEventType
from confidence_map.models.findings import AgentResult, AgentStatus, Finding

logger = logging.getLogger(__name__)

_AGENT_TIMEOUT = 180.0  # hard Python-level timeout per agent (asyncio cancellation)


class _AgentModule(Protocol):
    AGENT_ID: str
    AGENT_NAME: str

    def run(
        self,
        spec: str,
        architecture: str,
        context: str,
        spec_findings: list[Finding] | None,
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

# Maximum number of agents allowed to call Claude concurrently.
# Keeps 5 parallel agents from saturating rate limits simultaneously.
_MAX_CONCURRENT_AGENTS = 3


async def _stream_mock_analysis() -> AsyncGenerator[SSEEvent, None]:
    """Emit pre-generated NovaBank mock results with simulated timing."""
    mock_results = get_mock_results()
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
        # Phase 3: cross-agent consolidation
        await queue.put(
            SSEEvent(
                type=SSEEventType.CONSOLIDATION_START,
                agent_id="consolidator",
                agent_name="Consolidator",
            )
        )
        await asyncio.sleep(1.5)  # simulate consolidator running
        await queue.put(
            SSEEvent(
                type=SSEEventType.CONSOLIDATION_COMPLETE,
                agent_id="consolidator",
                agent_name="Consolidator",
                consolidation=get_mock_consolidation(),
            )
        )
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


async def stream_analysis(
    request: AnalysisRequest, *, analysis_id: str = ""
) -> AsyncGenerator[SSEEvent, None]:
    """Orchestrate 6 agents and yield SSE events as each one completes.

    Phase 1: Spec Analyst runs alone (its output informs the parallel phase).
    Phase 2: Five remaining agents run concurrently via asyncio.gather.
    """
    _ctx = f"[orchestrator][{analysis_id}]" if analysis_id else "[orchestrator]"

    if get_settings().demo_mode:
        async for mock_event in _stream_mock_analysis():
            yield mock_event
        return

    queue: asyncio.Queue[SSEEvent | None] = asyncio.Queue()

    async def run(
        agent_module: _AgentModule,
        agent_id: str,
        agent_name: str,
        spec_findings: list[Finding] | None = None,
    ) -> AgentResult:
        t0 = time.monotonic()
        async with semaphore:
            # Semaphore acquired: this agent now has a Claude API slot
            logger.info("%s AGENT_START %s", _ctx, agent_id)
            await queue.put(
                SSEEvent(type=SSEEventType.AGENT_START, agent_id=agent_id, agent_name=agent_name)
            )
            try:
                result: AgentResult = await asyncio.wait_for(
                    agent_module.run(
                        spec=request.spec,
                        architecture=request.architecture,
                        context=request.context,
                        spec_findings=spec_findings,
                    ),
                    timeout=_AGENT_TIMEOUT,
                )
            except TimeoutError:
                logger.warning("%s AGENT_TIMEOUT %s after %.0fs", _ctx, agent_id, _AGENT_TIMEOUT)
                result = AgentResult(
                    agent_id=agent_id,
                    agent_name=agent_name,
                    agent_icon="AlertCircle",
                    status=AgentStatus.ERROR,
                    error=f"Agent timed out after {int(_AGENT_TIMEOUT)} seconds",
                )
        # Semaphore released — next waiting agent can proceed
        elapsed = time.monotonic() - t0
        logger.info(
            "%s AGENT_DONE %s status=%s elapsed=%.1fs findings=%d",
            _ctx, agent_id, result.status, elapsed, len(result.findings),
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
        return result

    async def orchestrate() -> None:
        # Phase 1: Spec Analyst runs first — its findings seed the shared blackboard
        spec_result = await run(spec_analyst, spec_analyst.AGENT_ID, spec_analyst.AGENT_NAME)
        blackboard: list[Finding] = spec_result.findings if spec_result.error is None else []
        logger.info(
            "[orchestrator] Blackboard seeded with %d spec_analyst findings", len(blackboard)
        )

        # Phase 2: five agents run in parallel, each receiving the shared blackboard
        phase2_results: list[AgentResult] = list(
            await asyncio.gather(
                run(
                    arch_validator,
                    arch_validator.AGENT_ID,
                    arch_validator.AGENT_NAME,
                    blackboard,
                ),
                run(
                    risk_intelligence,
                    risk_intelligence.AGENT_ID,
                    risk_intelligence.AGENT_NAME,
                    blackboard,
                ),
                run(
                    business_impact,
                    business_impact.AGENT_ID,
                    business_impact.AGENT_NAME,
                    blackboard,
                ),
                run(
                    accessibility_advocate,
                    accessibility_advocate.AGENT_ID,
                    accessibility_advocate.AGENT_NAME,
                    blackboard,
                ),
                run(
                    delivery_historian,
                    delivery_historian.AGENT_ID,
                    delivery_historian.AGENT_NAME,
                    blackboard,
                ),
            )
        )

        # Phase 3: Consolidator cross-examines all findings
        all_results: list[AgentResult] = [spec_result, *phase2_results]
        logger.info("%s Starting consolidation over %d agent results", _ctx, len(all_results))
        await queue.put(
            SSEEvent(
                type=SSEEventType.CONSOLIDATION_START,
                agent_id="consolidator",
                agent_name="Consolidator",
            )
        )
        consolidation_result = await consolidator.run(all_results)
        logger.info(
            "%s Consolidation done: criticals=%d contradictions=%d",
            _ctx,
            len(consolidation_result.confirmed_criticals),
            len(consolidation_result.contradictions),
        )
        await queue.put(
            SSEEvent(
                type=SSEEventType.CONSOLIDATION_COMPLETE,
                agent_id="consolidator",
                agent_name="Consolidator",
                consolidation=consolidation_result,
            )
        )
        await queue.put(None)  # sentinel

    semaphore = asyncio.Semaphore(_MAX_CONCURRENT_AGENTS)
    logger.info("%s Starting real-mode analysis", _ctx)
    task = asyncio.create_task(orchestrate())
    dist = ConfidenceDistribution()
    total_findings = 0
    all_scores: list[float] = []

    try:
        while True:
            event: SSEEvent | None = await asyncio.wait_for(queue.get(), timeout=240.0)
            if event is None:
                break
            logger.info("%s event=%s", _ctx, event.type)

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
        yield SSEEvent(type=SSEEventType.ERROR, error="Analysis timed out after 240 seconds")
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
