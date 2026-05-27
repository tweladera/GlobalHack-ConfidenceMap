"""Integration tests for the FastAPI endpoints."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from confidence_map.main import app
from confidence_map.models.events import SSEEventType
from confidence_map.models.findings import AgentResult, AgentStatus, ConfidenceLevel, Finding


def _make_finding(confidence: str = "green") -> Finding:
    return Finding(
        title="Test finding",
        description="Description",
        confidence=ConfidenceLevel(confidence),
        confidence_score=0.8,
        evidence="Evidence",
        category="gap",
        agent_id="spec_analyst",
        agent_name="Spec Analyst",
    )


def _make_result(agent_id: str = "spec_analyst", status: str = "completed") -> AgentResult:
    return AgentResult(
        agent_id=agent_id,
        agent_name=agent_id.replace("_", " ").title(),
        agent_icon="X",
        status=AgentStatus(status),
        findings=[_make_finding()],
        summary="Test summary",
    )


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestStartAnalysis:
    def test_returns_202_with_analysis_id(self, client: TestClient) -> None:
        response = client.post(
            "/api/analyze",
            json={"spec": "A" * 20},
        )
        assert response.status_code == 202
        body = response.json()
        assert "analysis_id" in body
        assert len(body["analysis_id"]) > 0

    def test_rejects_short_spec(self, client: TestClient) -> None:
        response = client.post("/api/analyze", json={"spec": "short"})
        assert response.status_code == 422

    def test_rejects_missing_spec(self, client: TestClient) -> None:
        response = client.post("/api/analyze", json={})
        assert response.status_code == 422


class TestStreamAnalysis:
    def test_returns_404_for_unknown_id(self, client: TestClient) -> None:
        response = client.get("/api/analyze/nonexistent-id/stream")
        assert response.status_code == 404

    async def test_streams_sse_events(self) -> None:
        async def fake_stream(request):
            from confidence_map.models.events import SSEEvent, SSEEventType

            yield SSEEvent(
                type=SSEEventType.AGENT_START,
                agent_id="spec_analyst",
                agent_name="Spec Analyst",
            )
            result = _make_result()
            yield SSEEvent(
                type=SSEEventType.AGENT_COMPLETE,
                agent_id="spec_analyst",
                agent_name="Spec Analyst",
                result=result.model_dump(),
            )
            yield SSEEvent(
                type=SSEEventType.ANALYSIS_COMPLETE,
                total_findings=1,
                confidence_distribution={"green": 1, "yellow": 0, "red": 0},
                global_confidence_score=0.78,
            )

        with patch("confidence_map.api.analysis.stream_analysis", side_effect=fake_stream):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                # Start analysis first
                start_resp = await ac.post("/api/analyze", json={"spec": "A" * 50})
                assert start_resp.status_code == 202
                analysis_id = start_resp.json()["analysis_id"]

                # Stream results
                events: list[dict] = []
                async with ac.stream("GET", f"/api/analyze/{analysis_id}/stream") as resp:
                    assert resp.status_code == 200
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            events.append(json.loads(line[6:]))

        event_types = [e["type"] for e in events]
        assert SSEEventType.AGENT_START in event_types
        assert SSEEventType.AGENT_COMPLETE in event_types
        assert SSEEventType.ANALYSIS_COMPLETE in event_types

        complete_event = next(e for e in events if e["type"] == SSEEventType.ANALYSIS_COMPLETE)
        assert complete_event["global_confidence_score"] == 0.78


class TestTranslatePrepare:
    """Tests for POST /api/translate/prepare."""

    def test_returns_202_with_translate_id_demo(self, client: TestClient) -> None:
        with patch("confidence_map.api.analysis.get_settings") as mock_settings:
            mock_settings.return_value.demo_mode = True
            response = client.post("/api/translate/prepare", json={"language": "es"})
        assert response.status_code == 202
        body = response.json()
        assert "translate_id" in body
        assert len(body["translate_id"]) > 0

    def test_returns_202_with_translate_id_real_mode(self, client: TestClient) -> None:
        agents = [_make_result().model_dump()]
        with patch("confidence_map.api.analysis.get_settings") as mock_settings:
            mock_settings.return_value.demo_mode = False
            response = client.post(
                "/api/translate/prepare",
                json={"language": "pt", "agents": agents},
            )
        assert response.status_code == 202
        assert "translate_id" in response.json()

    def test_real_mode_requires_agents(self, client: TestClient) -> None:
        with patch("confidence_map.api.analysis.get_settings") as mock_settings:
            mock_settings.return_value.demo_mode = False
            response = client.post("/api/translate/prepare", json={"language": "es"})
        assert response.status_code == 400


class TestStreamTranslateById:
    """Tests for GET /api/translate/{translate_id}/stream."""

    def test_returns_404_for_unknown_id(self, client: TestClient) -> None:
        response = client.get("/api/translate/nonexistent-id/stream")
        assert response.status_code == 404

    def test_streams_demo_translation(self, client: TestClient) -> None:
        """Prepare then stream in demo mode — must emit agent_translated + complete events."""
        with patch("confidence_map.api.analysis.get_settings") as mock_settings:
            mock_settings.return_value.demo_mode = True
            prepare_resp = client.post("/api/translate/prepare", json={"language": "es"})
            assert prepare_resp.status_code == 202
            translate_id = prepare_resp.json()["translate_id"]

            with client.stream("GET", f"/api/translate/{translate_id}/stream") as stream_resp:
                assert stream_resp.status_code == 200
                assert "text/event-stream" in stream_resp.headers["content-type"]
                events: list[dict] = []
                for line in stream_resp.iter_lines():
                    if line.startswith("data: "):
                        events.append(json.loads(line[6:]))

        event_types = [e["type"] for e in events]
        assert "agent_translated" in event_types
        assert "complete" in event_types

    def test_translate_id_consumed_after_stream(self, client: TestClient) -> None:
        """The stored entry is deleted after streaming — prevents double-use."""
        with patch("confidence_map.api.analysis.get_settings") as mock_settings:
            mock_settings.return_value.demo_mode = True
            prepare_resp = client.post("/api/translate/prepare", json={"language": "en"})
            translate_id = prepare_resp.json()["translate_id"]

            with client.stream("GET", f"/api/translate/{translate_id}/stream") as r:
                for _ in r.iter_lines():
                    pass

        # Entry was popped — second call must 404
        second = client.get(f"/api/translate/{translate_id}/stream")
        assert second.status_code == 404
