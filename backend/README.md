# Confidence Map — Backend

REST API with SSE streaming that orchestrates six specialized AI agents to analyze software specifications.

---

## Technologies

| Tool | Version | Role |
|------|---------|------|
| Python | 3.12+ | Language |
| uv | 0.11+ | Package management |
| FastAPI | 0.136+ | HTTP framework |
| Anthropic SDK | 0.103+ | Claude integration |
| Pydantic v2 | 2.13+ | Models and validation |
| mypy | 2.1+ | Strict static typing |
| ruff | 0.15+ | Linter and formatter |
| pytest | 9.0+ | Tests (coverage >=80%) |

---

## Package structure

```
backend/
├── confidence_map/
│   ├── agents/
│   │   ├── base.py                    # Engine: structured Claude tool-use
│   │   ├── spec_analyst.py            # Agent 1: ambiguity and gaps
│   │   ├── arch_validator.py          # Agent 2: architecture and drift
│   │   ├── risk_intelligence.py       # Agent 3: security and delivery
│   │   ├── business_impact.py         # Agent 4: cost and business
│   │   ├── accessibility_advocate.py  # Agent 5: WCAG 2.1 AA
│   │   └── delivery_historian.py      # Agent 6: historical patterns
│   ├── api/
│   │   ├── analysis.py                # POST /api/analyze · GET /api/analyze/{id}/stream
│   │   └── chat.py                    # POST /api/chat/stream
│   ├── core/
│   │   ├── orchestrator.py            # Phase 1 sequential + Phase 2 parallel
│   │   └── settings.py                # Environment variables (pydantic-settings)
│   ├── models/
│   │   ├── findings.py                # Finding, AgentResult, ConfidenceLevel
│   │   ├── analysis.py                # AnalysisRequest, ConfidenceDistribution
│   │   ├── events.py                  # SSEEvent, SSEEventType
│   │   └── chat.py                    # ChatRequest, ChatResponse
│   └── main.py                        # FastAPI app entry point + CORS
├── tests/
│   ├── unit/
│   │   ├── test_models.py             # Domain model tests
│   │   ├── test_base_agent.py         # Agent engine tests
│   │   ├── test_mock_results.py       # Demo mode tests
│   │   ├── test_orchestrator.py       # Orchestrator tests
│   │   ├── test_chat.py               # Chat endpoint tests
│   │   └── test_consolidator.py       # Consolidator retry tests
│   └── integration/
│       └── test_api.py                # HTTP endpoint tests (SSE end-to-end)
└── pyproject.toml                     # All configuration
```

---

## Installation

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) installed

### Install dependencies

```bash
cd backend
uv sync
```

### Configure environment variables

```bash
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY
```

---

## Running

```bash
# Development (hot reload)
uv run uvicorn confidence_map.main:app --reload

# Production
uv run uvicorn confidence_map.main:app --host 0.0.0.0 --port 8000
```

The API is available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

---

## API Reference

### `POST /api/analyze`
Starts an analysis and returns its ID.

**Request:**
```json
{
  "spec": "## Feature: Payment Notifications...",
  "architecture": "Optional: architecture description",
  "context": "Optional: additional context"
}
```

**Response `202`:**
```json
{ "analysis_id": "uuid-v4", "demo_mode": false }
```

---

### `GET /api/analyze/{analysis_id}/stream`
SSE event stream while agents analyze.

**Emitted events:**

```jsonc
// Agent starts
{"type": "agent_start", "agent_id": "spec_analyst", "agent_name": "Spec Analyst"}

// Agent completes
{"type": "agent_complete", "agent_id": "spec_analyst", "result": {...}}

// Analysis finished
{"type": "analysis_complete", "total_findings": 28, "confidence_distribution": {"green": 8, "yellow": 12, "red": 8}}
```

---

### `POST /api/chat/stream`
Streams an AI response with full analysis context.

**Request:**
```json
{
  "message": "What is the most critical risk?",
  "findings": [...],
  "global_confidence_score": 0.72
}
```

---

### `GET /health`
Health check.

```json
{"status": "ok", "version": "0.1.0", "mode": "demo"}
```

---

## Orchestration flow

```
POST /api/analyze
        |
        v
[Spec Analyst]          <- Phase 1: runs alone, establishes context
        |
        v
+---------------------------------------+
|           Phase 2: parallel           |
|  [Arch]  [Risk]  [Business]           |
|  [Accessibility]  [Historian]         |
+---------------------------------------+
        |
        v
[Consolidator]          <- Phase 3: cross-examines all findings
        |
        v
SSE: analysis_complete
```

---

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEMO_MODE` | No | `false` | `true` = pre-generated results, no API |
| `ANTHROPIC_API_KEY` | Only if `DEMO_MODE=false` | — | Anthropic API key |
| `MODEL` | No | `claude-sonnet-4-6` | Claude model to use |
| `FRONTEND_URL` | No | `http://localhost:3000` | Allowed origin for CORS |

To reduce costs in development, use `MODEL=claude-haiku-4-5-20251001`.

---

## Quality gates

```bash
# Strict static typing
uv run mypy --strict confidence_map/

# Linting + formatting
uv run ruff check confidence_map/
uv run ruff format confidence_map/

# Tests with coverage
ANTHROPIC_API_KEY=test uv run pytest

# All together (pre-commit)
uv run mypy --strict confidence_map/ && uv run ruff check confidence_map/ && ANTHROPIC_API_KEY=test uv run pytest
```

---

## How each agent works

Each agent uses **Claude tool use** with a `report_findings` tool that forces structured JSON output with confidence levels. This guarantees that:

1. Output is always parseable (no free-text failures)
2. The `confidence`, `confidence_score`, `evidence` and `assumptions` fields are always explicit
3. The `summary` is optimized for screen readers

```python
# Example finding returned by an agent
{
  "title": "No retry strategy for external service",
  "description": "The spec does not define behavior when the email provider fails",
  "confidence": "red",
  "confidence_score": 0.1,
  "evidence": "User story US-001 does not mention error handling for the provider",
  "assumptions": [],
  "needs_validation": ["What is the retry policy?", "Is there a circuit breaker?"],
  "category": "risk"
}
```

---

## Adding a new agent

1. Create `confidence_map/agents/my_agent.py` with `AGENT_ID`, `AGENT_NAME`, `AGENT_ICON` and `async def run(...) -> AgentResult`
2. Import in `confidence_map/agents/__init__.py`
3. Add to `orchestrate()` in `confidence_map/core/orchestrator.py`
4. Write tests in `tests/unit/`
