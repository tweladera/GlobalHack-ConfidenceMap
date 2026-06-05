"""Unit tests for the Consolidator agent."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import anthropic
import pytest

from confidence_map.agents.consolidator import _format_all_findings, _parse_consolidation
from confidence_map.models.findings import (
    AgentResult,
    AgentStatus,
    ConfidenceLevel,
    Finding,
)


# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_finding(
    title: str = "T",
    confidence: str = "red",
    score: float = 0.1,
    evidence: str = "E",
) -> Finding:
    return Finding(
        title=title,
        description="D",
        confidence=ConfidenceLevel(confidence),
        confidence_score=score,
        evidence=evidence,
        category="risk",
        agent_id="spec_analyst",
        agent_name="Spec Analyst",
    )


def _make_result(
    agent_id: str = "spec_analyst",
    agent_name: str = "Spec Analyst",
    findings: list[Finding] | None = None,
    error: str | None = None,
) -> AgentResult:
    return AgentResult(
        agent_id=agent_id,
        agent_name=agent_name,
        agent_icon="X",
        status=AgentStatus.COMPLETED if error is None else AgentStatus.ERROR,
        findings=findings if findings is not None else [],
        error=error,
    )


# ── _format_all_findings ───────────────────────────────────────────────────────


class TestFormatAllFindings:
    def test_renders_agent_header_and_finding(self) -> None:
        result = _make_result(findings=[_make_finding(title="Missing retry logic")])
        block = _format_all_findings([result])
        assert "=== SPEC ANALYST ===" in block
        assert "Missing retry logic" in block
        assert "[RED | 10%]" in block

    def test_skips_errored_agents(self) -> None:
        errored = _make_result(error="API failure")
        block = _format_all_findings([errored])
        assert block.strip() == ""

    def test_skips_agents_with_no_findings(self) -> None:
        empty = _make_result(findings=[])
        block = _format_all_findings([empty])
        assert block.strip() == ""

    def test_truncates_evidence_at_200_chars(self) -> None:
        long_evidence = "X" * 300
        result = _make_result(findings=[_make_finding(evidence=long_evidence)])
        block = _format_all_findings([result])
        assert "..." in block

    def test_multiple_agents_all_rendered(self) -> None:
        r1 = _make_result(agent_id="spec_analyst", agent_name="Spec Analyst",
                          findings=[_make_finding(title="F1")])
        r2 = _make_result(agent_id="arch_validator", agent_name="Architecture Validator",
                          findings=[_make_finding(title="F2", confidence="green", score=0.9)])
        block = _format_all_findings([r1, r2])
        assert "=== SPEC ANALYST ===" in block
        assert "=== ARCHITECTURE VALIDATOR ===" in block
        assert "F1" in block
        assert "F2" in block

    def test_short_evidence_not_truncated(self) -> None:
        result = _make_result(findings=[_make_finding(evidence="Short.")])
        block = _format_all_findings([result])
        assert "..." not in block


# ── _parse_consolidation ───────────────────────────────────────────────────────


class TestParseConsolidation:
    def test_parses_all_fields(self) -> None:
        raw = {
            "contradictions": [
                {
                    "topic": "Timeout conflict",
                    "agents": ["spec_analyst", "arch_validator"],
                    "description": "They disagree.",
                    "resolution": "Spec Analyst is more accurate.",
                }
            ],
            "confirmed_criticals": [
                {
                    "topic": "No idempotency",
                    "agents": ["arch_validator", "delivery_historian"],
                    "combined_evidence": "Both flagged this independently.",
                }
            ],
            "redundancies": [
                {"topic": "Thread starvation", "agents": ["arch_validator", "risk_intelligence"],
                 "kept": "risk_intelligence"}
            ],
            "audit_summary": "Three blockers must be resolved before Sprint 1.",
        }
        result = _parse_consolidation(raw)
        assert len(result.contradictions) == 1
        assert result.contradictions[0].topic == "Timeout conflict"
        assert len(result.confirmed_criticals) == 1
        assert result.confirmed_criticals[0].agents == ["arch_validator", "delivery_historian"]
        assert len(result.redundancies) == 1
        assert result.redundancies[0].kept == "risk_intelligence"
        assert "Sprint 1" in result.audit_summary

    def test_missing_optional_lists_default_to_empty(self) -> None:
        result = _parse_consolidation({"audit_summary": "OK"})
        assert result.contradictions == []
        assert result.confirmed_criticals == []
        assert result.redundancies == []

    def test_audit_summary_defaults_to_empty_string(self) -> None:
        result = _parse_consolidation({})
        assert result.audit_summary == ""


# ── run() ─────────────────────────────────────────────────────────────────────


class TestConsolidatorRun:
    @pytest.fixture
    def mock_settings(self):  # type: ignore[no-untyped-def]
        with patch("confidence_map.agents.consolidator.get_settings") as mock:
            settings = MagicMock()
            settings.anthropic_api_key = "test-key"
            settings.model = "claude-sonnet-4-6"
            mock.return_value = settings
            yield mock

    @pytest.fixture
    def mock_anthropic(self):  # type: ignore[no-untyped-def]
        with patch("confidence_map.agents.consolidator.anthropic.AsyncAnthropic") as mock:
            yield mock

    async def test_returns_warning_summary_when_no_findings(self) -> None:
        from confidence_map.agents.consolidator import run

        # All agent results have no findings
        result = await run([_make_result(findings=[])])
        assert result.audit_summary != ""
        assert "No findings" in result.audit_summary
        assert result.contradictions == []

    async def test_returns_parsed_result_on_success(
        self, mock_settings: MagicMock, mock_anthropic: MagicMock
    ) -> None:
        from confidence_map.agents.consolidator import run

        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.name = "report_consolidation"
        tool_block.input = {
            "contradictions": [],
            "confirmed_criticals": [
                {
                    "topic": "No idempotency",
                    "agents": ["arch_validator", "delivery_historian"],
                    "combined_evidence": "Two agents confirmed this.",
                }
            ],
            "redundancies": [],
            "audit_summary": "Critical finding confirmed by two agents.",
        }
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            return_value=MagicMock(content=[tool_block])
        )
        mock_anthropic.return_value = mock_client

        result = await run([_make_result(findings=[_make_finding()])])

        assert len(result.confirmed_criticals) == 1
        assert result.confirmed_criticals[0].topic == "No idempotency"
        assert result.audit_summary == "Critical finding confirmed by two agents."
        assert result.contradictions == []

    async def test_returns_error_summary_on_api_failure(
        self, mock_settings: MagicMock, mock_anthropic: MagicMock
    ) -> None:
        from confidence_map.agents.consolidator import run

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=anthropic.APIStatusError(
                message="Internal server error",
                response=MagicMock(status_code=500, headers={}),
                body={},
            )
        )
        mock_anthropic.return_value = mock_client

        with patch("confidence_map.agents.consolidator.asyncio.sleep"):
            result = await run([_make_result(findings=[_make_finding()])])

        assert result.contradictions == []
        assert result.confirmed_criticals == []
        assert result.audit_summary != ""

    async def test_retries_on_rate_limit_then_succeeds(
        self, mock_settings: MagicMock, mock_anthropic: MagicMock
    ) -> None:
        from confidence_map.agents.consolidator import run

        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.name = "report_consolidation"
        tool_block.input = {
            "contradictions": [],
            "confirmed_criticals": [],
            "redundancies": [],
            "audit_summary": "All clear after retry.",
        }
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=[
                anthropic.RateLimitError(
                    message="Too many requests",
                    response=MagicMock(status_code=429, headers={}),
                    body={},
                ),
                MagicMock(content=[tool_block]),
            ]
        )
        mock_anthropic.return_value = mock_client

        with patch("confidence_map.agents.consolidator.asyncio.sleep"):
            result = await run([_make_result(findings=[_make_finding()])])

        assert result.audit_summary == "All clear after retry."
        assert mock_client.messages.create.call_count == 2

    async def test_exhausts_rate_limit_retries(
        self, mock_settings: MagicMock, mock_anthropic: MagicMock
    ) -> None:
        from confidence_map.agents.consolidator import run

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=anthropic.RateLimitError(
                message="Too many requests",
                response=MagicMock(status_code=429, headers={}),
                body={},
            )
        )
        mock_anthropic.return_value = mock_client

        with patch("confidence_map.agents.consolidator.asyncio.sleep"):
            result = await run([_make_result(findings=[_make_finding()])])

        assert "rate limit" in result.audit_summary.lower()
        assert mock_client.messages.create.call_count == 3  # initial + 2 retries

    async def test_no_retry_on_4xx_error(
        self, mock_settings: MagicMock, mock_anthropic: MagicMock
    ) -> None:
        from confidence_map.agents.consolidator import run

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=anthropic.APIStatusError(
                message="Bad request",
                response=MagicMock(status_code=400, headers={}),
                body={},
            )
        )
        mock_anthropic.return_value = mock_client

        result = await run([_make_result(findings=[_make_finding()])])

        assert result.audit_summary != ""
        assert mock_client.messages.create.call_count == 1  # no retry on 4xx

    async def test_returns_error_summary_when_no_tool_block(
        self, mock_settings: MagicMock, mock_anthropic: MagicMock
    ) -> None:
        from confidence_map.agents.consolidator import run

        text_block = MagicMock()
        text_block.type = "text"
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            return_value=MagicMock(content=[text_block])
        )
        mock_anthropic.return_value = mock_client

        result = await run([_make_result(findings=[_make_finding()])])

        assert "no structured output" in result.audit_summary.lower()
        assert result.contradictions == []
