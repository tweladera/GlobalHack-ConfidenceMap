"""Unit tests for the base agent — mocking the Anthropic API."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, call, patch

import anthropic
import pytest

from confidence_map.agents.base import (
    _apply_guardrails,
    _extract_findings,
    _extract_summary,
    _parse_finding,
)
from confidence_map.models.findings import AgentStatus, ConfidenceLevel, Finding


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


def _make_finding(
    *,
    title: str = "T",
    confidence: str = "green",
    score: float = 0.9,
    evidence: str = "Spec says so.",
) -> Finding:
    return Finding(
        title=title,
        description="D",
        confidence=ConfidenceLevel(confidence),
        confidence_score=score,
        evidence=evidence,
        category="gap",
        agent_id="test",
        agent_name="Test",
    )


class TestGuardrails:
    def test_valid_findings_pass_through_unchanged(self) -> None:
        f = _make_finding(confidence="green", score=0.85)
        result = _apply_guardrails([f], agent_id="test")
        assert result[0].confidence_score == 0.85
        assert result[0].evidence == "Spec says so."

    def test_clamps_green_score_below_minimum(self) -> None:
        f = _make_finding(confidence="green", score=0.2)  # green requires ≥ 0.60
        result = _apply_guardrails([f], agent_id="test")
        assert result[0].confidence_score == 0.60

    def test_clamps_red_score_above_maximum(self) -> None:
        f = _make_finding(confidence="red", score=0.9)  # red requires ≤ 0.45
        result = _apply_guardrails([f], agent_id="test")
        assert result[0].confidence_score == 0.45

    def test_clamps_yellow_score_above_maximum(self) -> None:
        f = _make_finding(confidence="yellow", score=0.95)  # yellow requires ≤ 0.75
        result = _apply_guardrails([f], agent_id="test")
        assert result[0].confidence_score == 0.75

    def test_substitutes_empty_evidence(self) -> None:
        f = _make_finding(evidence="")
        result = _apply_guardrails([f], agent_id="test")
        assert result[0].evidence != ""
        assert "No direct quote" in result[0].evidence

    def test_substitutes_whitespace_only_evidence(self) -> None:
        f = _make_finding(evidence="   ")
        result = _apply_guardrails([f], agent_id="test")
        assert "No direct quote" in result[0].evidence

    def test_all_green_distribution_does_not_raise(self) -> None:
        findings = [_make_finding(title=f"F{i}", confidence="green", score=0.9) for i in range(4)]
        # Must not raise — just logs a warning
        result = _apply_guardrails(findings, agent_id="test")
        assert len(result) == 4

    def test_empty_findings_list_returns_empty(self) -> None:
        assert _apply_guardrails([], agent_id="test") == []

    def test_score_at_exact_boundary_is_valid(self) -> None:
        f_green = _make_finding(confidence="green", score=0.60)
        f_red = _make_finding(confidence="red", score=0.45)
        assert _apply_guardrails([f_green], agent_id="test")[0].confidence_score == 0.60
        assert _apply_guardrails([f_red], agent_id="test")[0].confidence_score == 0.45


class TestRetryPolicy:
    """Tests for _make_api_call retry behaviour."""

    @pytest.fixture
    def mock_settings(self):
        with patch("confidence_map.agents.base.get_settings") as mock:
            settings = MagicMock()
            settings.anthropic_api_key = "test-key"
            settings.model = "claude-sonnet-4-6"
            mock.return_value = settings
            yield mock

    @pytest.fixture
    def mock_sleep(self):
        with patch("confidence_map.agents.base.asyncio.sleep", new_callable=AsyncMock) as mock:
            yield mock

    @pytest.fixture
    def mock_anthropic(self):
        with patch("confidence_map.agents.base.anthropic.AsyncAnthropic") as mock:
            yield mock

    def _tool_block(self) -> MagicMock:
        block = MagicMock()
        block.type = "tool_use"
        block.name = "report_findings"
        block.input = {
            "findings": [{
                "title": "T", "description": "D", "confidence": "yellow",
                "confidence_score": 0.5, "evidence": "E", "category": "gap",
            }],
            "summary": "S",
        }
        return block

    async def test_succeeds_on_first_attempt_without_sleep(
        self, mock_settings, mock_sleep, mock_anthropic
    ) -> None:
        from confidence_map.agents.base import call_agent

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            return_value=MagicMock(content=[self._tool_block()])
        )
        mock_anthropic.return_value = mock_client

        result = await call_agent(
            agent_id="x", agent_name="X", agent_icon="X",
            system_prompt="s", user_prompt="u",
        )

        assert result.status.value == "completed"
        mock_sleep.assert_not_called()

    async def test_retries_on_rate_limit_and_succeeds(
        self, mock_settings, mock_sleep, mock_anthropic
    ) -> None:
        from confidence_map.agents.base import call_agent

        good_response = MagicMock(content=[self._tool_block()])
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=[
                anthropic.RateLimitError(
                    message="rate limit", response=MagicMock(status_code=429, headers={}), body={}
                ),
                good_response,
            ]
        )
        mock_anthropic.return_value = mock_client

        result = await call_agent(
            agent_id="x", agent_name="X", agent_icon="X",
            system_prompt="s", user_prompt="u",
        )

        assert result.status.value == "completed"
        assert mock_client.messages.create.call_count == 2
        mock_sleep.assert_called_once()

    async def test_retries_on_server_error_500(
        self, mock_settings, mock_sleep, mock_anthropic
    ) -> None:
        from confidence_map.agents.base import call_agent

        good_response = MagicMock(content=[self._tool_block()])
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=[
                anthropic.APIStatusError(
                    message="internal error",
                    response=MagicMock(status_code=500, headers={}),
                    body={},
                ),
                good_response,
            ]
        )
        mock_anthropic.return_value = mock_client

        result = await call_agent(
            agent_id="x", agent_name="X", agent_icon="X",
            system_prompt="s", user_prompt="u",
        )

        assert result.status.value == "completed"
        assert mock_client.messages.create.call_count == 2

    async def test_no_retry_on_auth_error_401(
        self, mock_settings, mock_sleep, mock_anthropic
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
            agent_id="x", agent_name="X", agent_icon="X",
            system_prompt="s", user_prompt="u",
        )

        assert result.status.value == "error"
        assert mock_client.messages.create.call_count == 1  # no retry
        mock_sleep.assert_not_called()

    async def test_exhausted_rate_limit_retries_returns_error(
        self, mock_settings, mock_sleep, mock_anthropic
    ) -> None:
        from confidence_map.agents.base import _MAX_RETRIES, call_agent

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=anthropic.RateLimitError(
                message="rate limit", response=MagicMock(status_code=429, headers={}), body={}
            )
        )
        mock_anthropic.return_value = mock_client

        result = await call_agent(
            agent_id="x", agent_name="X", agent_icon="X",
            system_prompt="s", user_prompt="u",
        )

        assert result.status.value == "error"
        assert "retries exhausted" in (result.error or "")
        assert mock_client.messages.create.call_count == _MAX_RETRIES + 1
        assert mock_sleep.call_count == _MAX_RETRIES

    async def test_backoff_delays_increase_exponentially(
        self, mock_settings, mock_sleep, mock_anthropic
    ) -> None:
        from confidence_map.agents.base import _RETRY_BASE_DELAY, call_agent

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=anthropic.RateLimitError(
                message="rate limit", response=MagicMock(status_code=429, headers={}), body={}
            )
        )
        mock_anthropic.return_value = mock_client

        await call_agent(
            agent_id="x", agent_name="X", agent_icon="X",
            system_prompt="s", user_prompt="u",
        )

        from confidence_map.agents.base import _MAX_RETRIES

        # First sleep: base * 2^0 = 2.0s, second sleep: base * 2^1 = 4.0s
        expected_calls = [call(_RETRY_BASE_DELAY * (2.0**i)) for i in range(_MAX_RETRIES)]
        mock_sleep.assert_has_calls(expected_calls)


class TestExtractThinking:
    def test_returns_empty_when_no_thinking_blocks(self) -> None:
        from confidence_map.agents.base import _extract_thinking

        text_block = MagicMock()
        text_block.type = "text"
        assert _extract_thinking([text_block]) == ""

    def test_extracts_single_thinking_block(self) -> None:
        from confidence_map.agents.base import _extract_thinking

        block = MagicMock()
        block.type = "thinking"
        block.thinking = "Let me reason about this spec..."
        result = _extract_thinking([block])
        assert "Let me reason about this spec..." in result

    def test_concatenates_multiple_thinking_blocks(self) -> None:
        from confidence_map.agents.base import _extract_thinking

        b1, b2 = MagicMock(), MagicMock()
        b1.type = "thinking"
        b1.thinking = "First thought."
        b2.type = "thinking"
        b2.thinking = "Second thought."
        result = _extract_thinking([b1, b2])
        assert "First thought." in result
        assert "Second thought." in result

    def test_skips_non_thinking_blocks(self) -> None:
        from confidence_map.agents.base import _extract_thinking

        tool_block = MagicMock()
        tool_block.type = "tool_use"
        thinking_block = MagicMock()
        thinking_block.type = "thinking"
        thinking_block.thinking = "Only this."
        result = _extract_thinking([tool_block, thinking_block])
        assert result == "Only this."


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

    async def test_captures_thinking_block_in_result(
        self, mock_settings: MagicMock, mock_anthropic: MagicMock
    ) -> None:
        from confidence_map.agents.base import call_agent

        thinking_block = MagicMock()
        thinking_block.type = "thinking"
        thinking_block.thinking = "I'm reasoning about this spec..."

        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.name = "report_findings"
        tool_block.input = {
            "findings": [
                {
                    "title": "T", "description": "D", "confidence": "green",
                    "confidence_score": 0.9, "evidence": "E", "category": "gap",
                }
            ],
            "summary": "Summary",
        }

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            return_value=MagicMock(content=[thinking_block, tool_block])
        )
        mock_anthropic.return_value = mock_client

        result = await call_agent(
            agent_id="test", agent_name="Test", agent_icon="X",
            system_prompt="sys", user_prompt="user",
        )

        assert result.status == AgentStatus.COMPLETED
        assert "reasoning about this spec" in result.thinking

    async def test_thinking_is_empty_string_when_no_thinking_blocks(
        self, mock_settings: MagicMock, mock_anthropic: MagicMock
    ) -> None:
        from confidence_map.agents.base import call_agent

        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.name = "report_findings"
        tool_block.input = {
            "findings": [
                {
                    "title": "T", "description": "D", "confidence": "green",
                    "confidence_score": 0.9, "evidence": "E", "category": "gap",
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
            agent_id="test", agent_name="Test", agent_icon="X",
            system_prompt="sys", user_prompt="user",
        )

        assert result.thinking == ""

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
