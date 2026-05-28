"""Unit tests for the orchestrator — global confidence score calculation."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from confidence_map.models.analysis import AnalysisRequest
from confidence_map.models.events import SSEEventType
from confidence_map.models.findings import AgentResult, AgentStatus, ConfidenceLevel, ConsolidatorResult, Finding


def _make_finding(score: float, confidence: str) -> Finding:
    return Finding(
        title="Test",
        description="Desc",
        confidence=ConfidenceLevel(confidence),
        confidence_score=score,
        evidence="E",
        category="gap",
        agent_id="spec_analyst",
        agent_name="Spec Analyst",
    )


def _make_result(scores: list[tuple[float, str]]) -> AgentResult:
    return AgentResult(
        agent_id="spec_analyst",
        agent_name="Spec Analyst",
        agent_icon="X",
        status=AgentStatus.COMPLETED,
        findings=[_make_finding(s, c) for s, c in scores],
        summary="Summary",
    )


class TestGlobalConfidenceScore:
    async def test_score_is_average_of_all_findings(self) -> None:
        """Global score = average confidence_score across all findings."""
        request = AnalysisRequest(spec="A" * 20)

        result = _make_result([(1.0, "green"), (0.5, "yellow"), (0.0, "red")])
        # avg = (1.0 + 0.5 + 0.0) / 3 = 0.5

        async def fake_run(*args, **kwargs):  # type: ignore[no-untyped-def]
            return result

        mock_module = MagicMock()
        mock_module.AGENT_ID = "spec_analyst"
        mock_module.AGENT_NAME = "Spec Analyst"
        mock_module.run = AsyncMock(side_effect=fake_run)

        from confidence_map.core.orchestrator import stream_analysis

        mock_settings = type("S", (), {"demo_mode": False})()

        mock_consolidator = MagicMock()
        mock_consolidator.run = AsyncMock(return_value=ConsolidatorResult(audit_summary="ok"))

        with (
            patch("confidence_map.core.orchestrator.get_settings", return_value=mock_settings),
            patch("confidence_map.core.orchestrator.spec_analyst", mock_module),
            patch("confidence_map.core.orchestrator.arch_validator", mock_module),
            patch("confidence_map.core.orchestrator.risk_intelligence", mock_module),
            patch("confidence_map.core.orchestrator.business_impact", mock_module),
            patch("confidence_map.core.orchestrator.accessibility_advocate", mock_module),
            patch("confidence_map.core.orchestrator.delivery_historian", mock_module),
            patch("confidence_map.core.orchestrator.consolidator", mock_consolidator),
        ):
            events = [e async for e in stream_analysis(request)]

        complete = next(e for e in events if e.type == SSEEventType.ANALYSIS_COMPLETE)
        assert complete.global_confidence_score is not None
        # 6 agents x 3 findings each = 18 findings, avg of (1.0,0.5,0.0) repeated = 0.5
        assert abs(complete.global_confidence_score - 0.5) < 0.01

    async def test_score_is_none_equivalent_when_no_findings(self) -> None:
        """If all agents return no findings, global score is 0.0."""
        request = AnalysisRequest(spec="A" * 20)

        empty_result = AgentResult(
            agent_id="spec_analyst",
            agent_name="Spec Analyst",
            agent_icon="X",
            status=AgentStatus.ERROR,
            findings=[],
            error="No findings",
        )

        mock_module = MagicMock()
        mock_module.AGENT_ID = "spec_analyst"
        mock_module.AGENT_NAME = "Spec Analyst"
        mock_module.run = AsyncMock(return_value=empty_result)

        from confidence_map.core.orchestrator import stream_analysis

        mock_settings = type("S", (), {"demo_mode": False})()

        mock_consolidator = MagicMock()
        mock_consolidator.run = AsyncMock(return_value=ConsolidatorResult(audit_summary="ok"))

        with (
            patch("confidence_map.core.orchestrator.get_settings", return_value=mock_settings),
            patch("confidence_map.core.orchestrator.spec_analyst", mock_module),
            patch("confidence_map.core.orchestrator.arch_validator", mock_module),
            patch("confidence_map.core.orchestrator.risk_intelligence", mock_module),
            patch("confidence_map.core.orchestrator.business_impact", mock_module),
            patch("confidence_map.core.orchestrator.accessibility_advocate", mock_module),
            patch("confidence_map.core.orchestrator.delivery_historian", mock_module),
            patch("confidence_map.core.orchestrator.consolidator", mock_consolidator),
        ):
            events = [e async for e in stream_analysis(request)]

        complete = next(e for e in events if e.type == SSEEventType.ANALYSIS_COMPLETE)
        assert complete.global_confidence_score == 0.0
        assert complete.total_findings == 0
