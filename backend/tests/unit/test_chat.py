"""Unit tests for the chat endpoint."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import anthropic
import pytest
from fastapi.testclient import TestClient

from confidence_map.api.chat import _build_system_prompt
from confidence_map.main import app
from confidence_map.models.chat import AgentRef, ChatRequest, FindingRef


def _finding() -> dict[str, object]:
    return {
        "title": "Missing auth spec",
        "description": "Auth flow is not documented",
        "confidence": "red",
        "confidence_score": 0.05,
        "category": "gap",
        "agent_name": "Spec Analyst",
        "recommended_action": "Define the auth flow",
    }


def _agent() -> dict[str, str]:
    return {"agent_name": "Spec Analyst", "summary": "Several gaps found."}


def test_chat_demo_mode_streams_text() -> None:
    client = TestClient(app)
    with patch("confidence_map.api.chat.get_settings") as mock_settings:
        mock_settings.return_value.demo_mode = True
        with client.stream(
            "POST",
            "/api/chat/stream",
            json={
                "question": "What are the critical risks?",
                "findings": [_finding()],
                "agents": [_agent()],
                "global_score": 0.42,
            },
        ) as resp:
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers["content-type"]
            events: list[dict[str, object]] = []
            for line in resp.iter_lines():
                if line.startswith("data: "):
                    events.append(json.loads(line[6:]))

    text_events = [e for e in events if "text" in e]
    complete_events = [e for e in events if e.get("type") == "complete"]
    assert len(text_events) > 0
    assert len(complete_events) == 1
    full_text = "".join(str(e["text"]) for e in text_events)
    assert len(full_text) > 50


def test_chat_rejects_empty_question() -> None:
    client = TestClient(app)
    resp = client.post(
        "/api/chat/stream",
        json={"question": "", "findings": [], "agents": []},
    )
    assert resp.status_code == 422


def test_chat_rejects_question_too_long() -> None:
    client = TestClient(app)
    resp = client.post(
        "/api/chat/stream",
        json={"question": "x" * 2001, "findings": [], "agents": []},
    )
    assert resp.status_code == 422


def test_chat_accepts_empty_findings_and_agents() -> None:
    client = TestClient(app)
    with patch("confidence_map.api.chat.get_settings") as mock_settings:
        mock_settings.return_value.demo_mode = True
        with client.stream(
            "POST",
            "/api/chat/stream",
            json={"question": "How do I improve this?", "findings": [], "agents": []},
        ) as resp:
            assert resp.status_code == 200


def test_chat_accepts_conversation_history() -> None:
    client = TestClient(app)
    with patch("confidence_map.api.chat.get_settings") as mock_settings:
        mock_settings.return_value.demo_mode = True
        with client.stream(
            "POST",
            "/api/chat/stream",
            json={
                "question": "Follow-up question",
                "findings": [_finding()],
                "agents": [_agent()],
                "history": [
                    {"role": "user", "content": "What is the risk?"},
                    {"role": "assistant", "content": "The risk is high."},
                ],
            },
        ) as resp:
            assert resp.status_code == 200


# ── _build_system_prompt ───────────────────────────────────────────────────────


class TestBuildSystemPrompt:
    def _request(self, score: float | None = 0.42) -> ChatRequest:
        return ChatRequest(
            question="What should I fix first?",
            findings=[
                FindingRef(
                    title="Missing auth spec",
                    description="Auth flow not documented",
                    confidence="red",
                    confidence_score=0.05,
                    category="gap",
                    agent_name="Spec Analyst",
                    recommended_action="Define the auth flow",
                )
            ],
            agents=[AgentRef(agent_name="Spec Analyst", summary="Several gaps found.")],
            global_score=score,
        )

    def test_includes_finding_title_and_category(self) -> None:
        prompt = _build_system_prompt(self._request())
        assert "Missing auth spec" in prompt
        assert "gap" in prompt

    def test_includes_global_score_as_percentage(self) -> None:
        prompt = _build_system_prompt(self._request(score=0.42))
        assert "42%" in prompt

    def test_omits_score_line_when_none(self) -> None:
        prompt = _build_system_prompt(self._request(score=None))
        assert "Global confidence score" not in prompt

    def test_includes_agent_summary(self) -> None:
        prompt = _build_system_prompt(self._request())
        assert "Several gaps found." in prompt

    def test_includes_recommended_action(self) -> None:
        prompt = _build_system_prompt(self._request())
        assert "Define the auth flow" in prompt


# ── _claude_generator (real API path) ─────────────────────────────────────────


class TestClaudeGenerator:
    @pytest.fixture
    def live_settings(self):
        with patch("confidence_map.api.chat.get_settings") as mock_gs:
            s = MagicMock()
            s.demo_mode = False
            s.model = "claude-sonnet-4-6"
            s.anthropic_api_key = "test-key"
            mock_gs.return_value = s
            yield mock_gs

    def _stream_events(self, stream_ctx: MagicMock) -> list[dict]:
        with patch(
            "confidence_map.api.chat.anthropic.AsyncAnthropic",
            return_value=MagicMock(messages=MagicMock(stream=MagicMock(return_value=stream_ctx))),
        ):
            client = TestClient(app)
            with client.stream(
                "POST",
                "/api/chat/stream",
                json={
                    "question": "What are the risks?",
                    "findings": [_finding()],
                    "agents": [_agent()],
                },
            ) as resp:
                assert resp.status_code == 200
                events = []
                for line in resp.iter_lines():
                    if line.startswith("data: "):
                        events.append(json.loads(line[6:]))
        return events

    def test_streams_text_chunks_and_complete_event(self, live_settings: MagicMock) -> None:
        async def _fake_text_stream():
            yield "Hello"
            yield " world"

        stream_ctx = MagicMock()
        stream_ctx.__aenter__ = AsyncMock(return_value=stream_ctx)
        stream_ctx.__aexit__ = AsyncMock(return_value=False)
        stream_ctx.text_stream = _fake_text_stream()

        events = self._stream_events(stream_ctx)

        text_events = [e for e in events if "text" in e]
        complete_events = [e for e in events if e.get("type") == "complete"]
        assert len(text_events) == 2
        assert "".join(str(e["text"]) for e in text_events) == "Hello world"
        assert len(complete_events) == 1

    def test_api_error_yields_error_event(self, live_settings: MagicMock) -> None:
        stream_ctx = MagicMock()
        stream_ctx.__aenter__ = AsyncMock(
            side_effect=anthropic.APIStatusError(
                message="Service unavailable",
                response=MagicMock(status_code=503, headers={}),
                body={},
            )
        )
        stream_ctx.__aexit__ = AsyncMock(return_value=False)

        events = self._stream_events(stream_ctx)

        error_events = [e for e in events if e.get("type") == "error"]
        assert len(error_events) == 1
        assert "503" in error_events[0].get("message", "") or error_events[0].get("message")
