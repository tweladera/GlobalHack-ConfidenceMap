"""Unit tests for mock_results and _stream_mock_analysis (DEMO_MODE path)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from confidence_map.core.mock_results import AGENT_DELAYS, get_mock_results
from confidence_map.models.events import SSEEventType
from confidence_map.models.findings import AgentStatus, ConfidenceLevel


_ALL_AGENT_IDS = {
    "spec_analyst",
    "arch_validator",
    "risk_intelligence",
    "business_impact",
    "accessibility_advocate",
    "delivery_historian",
}


class TestGetMockResults:
    def test_returns_all_six_agents(self) -> None:
        results = get_mock_results()
        assert set(results.keys()) == _ALL_AGENT_IDS

    def test_all_agents_completed_without_error(self) -> None:
        for agent_id, result in get_mock_results().items():
            assert result.status == AgentStatus.COMPLETED, f"{agent_id} has status {result.status}"
            assert result.error is None, f"{agent_id} has error: {result.error}"

    def test_all_agents_have_findings(self) -> None:
        for agent_id, result in get_mock_results().items():
            assert len(result.findings) >= 3, (
                f"{agent_id} has only {len(result.findings)} findings (expected ≥3)"
            )

    def test_all_confidence_levels_are_valid(self) -> None:
        valid = {ConfidenceLevel.GREEN, ConfidenceLevel.YELLOW, ConfidenceLevel.RED}
        for agent_id, result in get_mock_results().items():
            for finding in result.findings:
                assert finding.confidence in valid, (
                    f"{agent_id} finding '{finding.title}' has invalid confidence: {finding.confidence}"
                )

    def test_all_scores_in_range(self) -> None:
        for agent_id, result in get_mock_results().items():
            for finding in result.findings:
                assert 0.0 <= finding.confidence_score <= 1.0, (
                    f"{agent_id} finding '{finding.title}' score out of range: {finding.confidence_score}"
                )

    def test_each_result_has_summary(self) -> None:
        for agent_id, result in get_mock_results().items():
            assert result.summary, f"{agent_id} has empty summary"

    def test_agent_delays_cover_all_agents(self) -> None:
        assert set(AGENT_DELAYS.keys()) == _ALL_AGENT_IDS

    def test_delays_are_positive(self) -> None:
        for agent_id, delay in AGENT_DELAYS.items():
            assert delay > 0, f"{agent_id} delay is not positive: {delay}"


class TestStreamMockAnalysis:
    async def test_emits_start_and_complete_for_all_agents(self) -> None:
        from confidence_map.core.orchestrator import stream_analysis
        from confidence_map.models.analysis import AnalysisRequest

        request = AnalysisRequest(spec="A" * 20)

        mock_settings = type("S", (), {"demo_mode": True})()

        with (
            patch("confidence_map.core.orchestrator.get_settings", return_value=mock_settings),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            events = [e async for e in stream_analysis(request)]

        agent_starts = [e for e in events if e.type == SSEEventType.AGENT_START]
        agent_completes = [e for e in events if e.type == SSEEventType.AGENT_COMPLETE]
        complete_events = [e for e in events if e.type == SSEEventType.ANALYSIS_COMPLETE]

        assert len(agent_starts) == 6
        assert len(agent_completes) == 6
        assert len(complete_events) == 1

    async def test_analysis_complete_has_global_score(self) -> None:
        from confidence_map.core.orchestrator import stream_analysis
        from confidence_map.models.analysis import AnalysisRequest

        request = AnalysisRequest(spec="A" * 20)
        mock_settings = type("S", (), {"demo_mode": True})()

        with (
            patch("confidence_map.core.orchestrator.get_settings", return_value=mock_settings),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            events = [e async for e in stream_analysis(request)]

        complete = next(e for e in events if e.type == SSEEventType.ANALYSIS_COMPLETE)
        assert complete.global_confidence_score is not None
        assert 0.0 <= complete.global_confidence_score <= 1.0
        assert complete.total_findings > 0

    async def test_all_agent_ids_present_in_events(self) -> None:
        from confidence_map.core.orchestrator import stream_analysis
        from confidence_map.models.analysis import AnalysisRequest

        request = AnalysisRequest(spec="A" * 20)
        mock_settings = type("S", (), {"demo_mode": True})()

        with (
            patch("confidence_map.core.orchestrator.get_settings", return_value=mock_settings),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            events = [e async for e in stream_analysis(request)]

        started_ids = {e.agent_id for e in events if e.type == SSEEventType.AGENT_START}
        completed_ids = {e.agent_id for e in events if e.type == SSEEventType.AGENT_COMPLETE}

        assert started_ids == _ALL_AGENT_IDS
        assert completed_ids == _ALL_AGENT_IDS
