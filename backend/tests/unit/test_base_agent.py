"""Unit tests for the base agent — mocking the Anthropic API."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import anthropic
import pytest

from confidence_map.agents.base import _extract_findings, _extract_summary, _parse_finding
from confidence_map.models.findings import AgentStatus, ConfidenceLevel


class TestParseFinding:
    def test_parses_all_fields(self) -> None:
        raw = {
            "title": "Missing retry logic",
            "description": "No retry strategy defined",
            "confidence": "red",
            "confidence_score": 0.1,
            "evidence": "Spec does not mention retry",
            "assumptions": ["External service is unreliable"],
            "needs_validation": ["What is the retry policy?"],
            "category": "risk",
        }
        finding = _parse_finding(raw, agent_id="risk_intelligence", agent_name="Risk Intelligence")
        assert finding.title == "Missing retry logic"
        assert finding.confidence == ConfidenceLevel.RED
        assert finding.confidence_score == 0.1
        assert finding.agent_id == "risk_intelligence"

    def test_defaults_missing_optional_fields(self) -> None:
        raw = {
            "title": "T",
            "description": "D",
            "confidence": "green",
            "confidence_score": 1.0,
            "evidence": "E",
            "category": "gap",
        }
        finding = _parse_finding(raw, agent_id="x", agent_name="X")
        assert finding.assumptions == []
        assert finding.needs_validation == []


class TestExtractHelpers:
    def _make_tool_block(self, findings: list[dict], summary: str) -> list:
        block = MagicMock()
        block.type = "tool_use"
        block.name = "report_findings"
        block.input = {"findings": findings, "summary": summary}
        return [block]

    def test_extract_findings_from_tool_block(self) -> None:
        raw_finding = {
            "title": "T",
            "description": "D",
            "confidence": "yellow",
            "confidence_score": 0.5,
            "evidence": "E",
            "category": "gap",
        }
        content = self._make_tool_block([raw_finding], "Summary text")
        findings = _extract_findings(content, agent_id="a", agent_name="A")
        assert len(findings) == 1
        assert findings[0].confidence == ConfidenceLevel.YELLOW

    def test_extract_findings_returns_empty_when_no_tool_block(self) -> None:
        block = MagicMock()
        block.type = "text"
        findings = _extract_findings([block], agent_id="a", agent_name="A")
        assert findings == []

    def test_extract_summary(self) -> None:
        content = self._make_tool_block([], "This is the summary.")
        summary = _extract_summary(content)
        assert summary == "This is the summary."

    def test_extract_summary_returns_empty_when_no_tool_block(self) -> None:
        block = MagicMock()
        block.type = "text"
        summary = _extract_summary([block])
        assert summary == ""


class TestCallAgent:
    @pytest.fixture
    def mock_settings(self):
        with patch("confidence_map.agents.base.get_settings") as mock:
            settings = MagicMock()
            settings.anthropic_api_key = "test-key"
            settings.model = "claude-sonnet-4-6"
            mock.return_value = settings
            yield mock

    @pytest.fixture
    def mock_anthropic(self):
        with patch("confidence_map.agents.base.anthropic.AsyncAnthropic") as mock:
            yield mock

    async def test_returns_completed_result_on_success(
        self, mock_settings, mock_anthropic
    ) -> None:
        from confidence_map.agents.base import call_agent

        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.name = "report_findings"
        tool_block.input = {
            "findings": [
                {
                    "title": "T",
                    "description": "D",
                    "confidence": "green",
                    "confidence_score": 0.9,
                    "evidence": "E",
                    "category": "gap",
                }
            ],
            "summary": "Summary",
        }

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            return_value=MagicMock(content=[tool_block])
        )
        mock_anthropic.return_value = mock_client

        result = await call_agent(
            agent_id="test",
            agent_name="Test",
            agent_icon="X",
            system_prompt="sys",
            user_prompt="user",
        )

        assert result.status == AgentStatus.COMPLETED
        assert len(result.findings) == 1
        assert result.summary == "Summary"

    async def test_returns_error_on_api_failure(
        self, mock_settings, mock_anthropic
    ) -> None:
        from confidence_map.agents.base import call_agent

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=anthropic.APIStatusError(
                message="Unauthorized",
                response=MagicMock(status_code=401, headers={}),
                body={},
            )
        )
        mock_anthropic.return_value = mock_client

        result = await call_agent(
            agent_id="test",
            agent_name="Test",
            agent_icon="X",
            system_prompt="sys",
            user_prompt="user",
        )

        assert result.status == AgentStatus.ERROR
        assert result.error is not None
        assert "401" in result.error

    async def test_returns_error_when_no_findings_returned(
        self, mock_settings, mock_anthropic
    ) -> None:
        from confidence_map.agents.base import call_agent

        text_block = MagicMock()
        text_block.type = "text"

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            return_value=MagicMock(content=[text_block])
        )
        mock_anthropic.return_value = mock_client

        result = await call_agent(
            agent_id="test",
            agent_name="Test",
            agent_icon="X",
            system_prompt="sys",
            user_prompt="user",
        )

        assert result.status == AgentStatus.ERROR
