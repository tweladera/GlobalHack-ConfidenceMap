"""Unit tests for domain models."""

import pytest
from pydantic import ValidationError

from confidence_map.models.analysis import AnalysisRequest, ConfidenceDistribution
from confidence_map.models.events import SSEEvent, SSEEventType
from confidence_map.models.findings import AgentResult, AgentStatus, ConfidenceLevel, Finding


class TestConfidenceLevel:
    def test_values_are_strings(self) -> None:
        assert ConfidenceLevel.GREEN == "green"
        assert ConfidenceLevel.YELLOW == "yellow"
        assert ConfidenceLevel.RED == "red"

    def test_from_string(self) -> None:
        assert ConfidenceLevel("green") is ConfidenceLevel.GREEN


class TestFinding:
    def test_valid_finding(self) -> None:
        finding = Finding(
            title="Missing error state",
            description="No behavior defined for network failure",
            confidence=ConfidenceLevel.RED,
            confidence_score=0.1,
            evidence="Spec says nothing about failure",
            category="gap",
            agent_id="spec_analyst",
            agent_name="Spec Analyst",
        )
        assert finding.confidence == ConfidenceLevel.RED
        assert len(finding.id) > 0

    def test_id_is_auto_generated(self) -> None:
        f1 = Finding(
            title="A",
            description="B",
            confidence=ConfidenceLevel.GREEN,
            confidence_score=1.0,
            evidence="C",
            category="gap",
            agent_id="x",
            agent_name="X",
        )
        f2 = Finding(
            title="A",
            description="B",
            confidence=ConfidenceLevel.GREEN,
            confidence_score=1.0,
            evidence="C",
            category="gap",
            agent_id="x",
            agent_name="X",
        )
        assert f1.id != f2.id

    def test_confidence_score_bounds(self) -> None:
        with pytest.raises(ValidationError):
            Finding(
                title="X",
                description="Y",
                confidence=ConfidenceLevel.GREEN,
                confidence_score=1.5,  # out of bounds
                evidence="Z",
                category="gap",
                agent_id="x",
                agent_name="X",
            )

    def test_title_cannot_be_empty(self) -> None:
        with pytest.raises(ValidationError):
            Finding(
                title="",
                description="Y",
                confidence=ConfidenceLevel.GREEN,
                confidence_score=0.5,
                evidence="Z",
                category="gap",
                agent_id="x",
                agent_name="X",
            )

    def test_defaults_for_lists(self) -> None:
        finding = Finding(
            title="T",
            description="D",
            confidence=ConfidenceLevel.YELLOW,
            confidence_score=0.5,
            evidence="E",
            category="risk",
            agent_id="x",
            agent_name="X",
        )
        assert finding.assumptions == []
        assert finding.needs_validation == []


class TestAgentResult:
    def test_default_status_is_pending(self) -> None:
        result = AgentResult(
            agent_id="spec_analyst",
            agent_name="Spec Analyst",
            agent_icon="FileSearch",
        )
        assert result.status == AgentStatus.PENDING
        assert result.findings == []
        assert result.error is None


class TestAnalysisRequest:
    def test_requires_spec(self) -> None:
        with pytest.raises(ValidationError):
            AnalysisRequest(spec="")  # too short

    def test_optional_fields_default_to_empty(self) -> None:
        req = AnalysisRequest(spec="A" * 20)
        assert req.architecture == ""
        assert req.context == ""


class TestConfidenceDistribution:
    def test_total_property(self) -> None:
        dist = ConfidenceDistribution(green=3, yellow=2, red=1)
        assert dist.total == 6

    def test_default_zeros(self) -> None:
        dist = ConfidenceDistribution()
        assert dist.total == 0


class TestSSEEvent:
    def test_agent_start_event(self) -> None:
        event = SSEEvent(
            type=SSEEventType.AGENT_START,
            agent_id="spec_analyst",
            agent_name="Spec Analyst",
        )
        assert event.type == SSEEventType.AGENT_START
        assert event.result is None

    def test_analysis_complete_event(self) -> None:
        event = SSEEvent(
            type=SSEEventType.ANALYSIS_COMPLETE,
            total_findings=12,
            confidence_distribution={"green": 4, "yellow": 5, "red": 3},
        )
        assert event.total_findings == 12
