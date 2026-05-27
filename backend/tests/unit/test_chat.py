"""Unit tests for the chat endpoint."""

from __future__ import annotations

import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from confidence_map.main import app


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
