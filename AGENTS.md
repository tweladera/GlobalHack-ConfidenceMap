# Confidence Map — Guide for Claude Code

Intelligence platform for architecture/delivery with 6 specialized AI agents.
Analyzes software specifications and generates a visual map of decisions, risks and
uncertainties with explicit confidence levels.

**Repository:** https://github.com/tweladera/GlobalHack-ConfidenceMap
**Team:** Confidence Map — Evans Ladera & Daniel Santibanez (Thoughtworks)
**Hackathon:** AI/works™ 2026 · Naming convention: GlobalHack-ConfidenceMap

---

## Essential commands

```bash
make setup          # First time: checks tools, creates .env, installs deps
make dev            # Starts backend (:8000) + frontend (:3000)
make demo           # Same as dev but forces DEMO_MODE=true (no API key)
make stop           # Kills processes on :8000 and :3000
make check          # Full quality gates: lint + types + tests
make test           # Tests with coverage (>=80% required)
make lint           # ruff check
make format         # ruff format + fix
make typecheck      # mypy backend + tsc frontend
make build          # next build (production)
make health         # curl /health to backend
```

### Direct commands (when Makefile doesn't apply)

```bash
# Backend
cd backend && ANTHROPIC_API_KEY=test uv run pytest --no-header -q
cd backend && uv run mypy --strict confidence_map/
cd backend && uv run ruff check confidence_map/
cd backend && uv run ruff format confidence_map/

# Frontend
cd frontend && pnpm exec tsc --noEmit
cd frontend && pnpm dev
cd frontend && pnpm build
```

---

## Project structure

```
backend/
  confidence_map/
    agents/         # 6 agents: spec_analyst, arch_validator, risk_intelligence,
                    #           business_impact, accessibility_advocate, delivery_historian
    api/            # FastAPI routes (analysis.py — SSE streaming endpoint)
    core/           # orchestrator.py, mock_results.py, settings.py
    models/         # Pydantic v2: analysis.py, events.py, findings.py
    main.py         # FastAPI app entry point
  tests/
    unit/           # test_base_agent, test_mock_results, test_models, test_orchestrator
    integration/    # test_api (SSE endpoint end-to-end)
  pyproject.toml    # uv, ruff, mypy, pytest config

frontend/
  app/              # Next.js 15 App Router (page.tsx, analysis/page.tsx)
  components/       # ConfidenceMap, DecisionTable, FindingDetail,
                    # AgentStatusCard, AccessibleSummary
  lib/demo-spec.ts  # NovaBank Payments + Auth MFA specs (demo presets)
  types/index.ts    # Shared TypeScript types

docs/               # Architecture diagrams and reference documents (English)
docs_es/            # Original Spanish versions of all documents
```

---

## Critical rules

- **NEVER** commit `.env` — it contains the API key. Only `.env.example` goes to the repo.
- **NEVER** use `pip` directly — always `uv run` or `uv sync`.
- **NEVER** use `npm` — always `pnpm`.
- Tests **do not need a real API key**: `ANTHROPIC_API_KEY=test uv run pytest`.
- ruff, mypy and pytest run **from `backend/`**, not from root.
- `make demo` / `DEMO_MODE=true` to run the demo without consuming credits ($0).

---

## Code conventions

### Backend (Python 3.12+)
- Static typing: `mypy --strict` — 0 errors is the only acceptable state.
- Linting: `ruff` with `line-length = 100`.
- Tests: `pytest-asyncio` in `auto` mode, minimum 80% coverage (current: 90.06%).
- Runtime dependencies: `pyproject.toml [project.dependencies]`.
- Dev dependencies: `pyproject.toml [dependency-groups] dev`.
- Agents inherit from `BaseAgent` (`agents/base.py`) and use Claude tool use for structured output.
- The orchestrator (`core/orchestrator.py`) runs Spec Analyst first, then 5 agents in `asyncio.gather`.

### Frontend (TypeScript strict)
- `tsconfig.json` with `strict: true`.
- Package manager: `pnpm` (lockfile: `pnpm-lock.yaml`).
- Visualization: React Flow + dagre layout (auto-positioning of nodes).
- Styles: Tailwind CSS.
- API proxy: `next.config.ts` redirects `/api/*` -> `localhost:8000`.

---

## DEMO_MODE

With `DEMO_MODE=true` in `backend/.env` (or `make demo`):
- The backend uses `core/mock_results.py` instead of calling Claude.
- SSE streaming works the same (with simulated delays).
- The analysis completes in ~5 seconds.
- $0 API cost.

Without `DEMO_MODE` (real mode): 60–120 seconds, requires credits in the Anthropic account.

---

## Key references

| File | Purpose |
|------|---------|
| `STATUS.md` | Source of truth: status, checkpoints, demo checklist |
| `QUICKSTART.md` | Step-by-step start guide for new contributors |
| `backend/.env.example` | Configuration template with all variables |
| `docs/submission-round1.md` | Round 1 submission document (June 8–12, 2026) |
| `docs/video-script-round1.md` | Full video presentation script |

---

## Pre-push checklist

```bash
cd backend && uv run ruff check confidence_map/           # 0 errors
cd backend && uv run mypy --strict confidence_map/        # 0 errors
cd backend && ANTHROPIC_API_KEY=test uv run pytest -q     # all passed, >=80% cov
cd frontend && pnpm exec tsc --noEmit                     # no output = ok
```

Or simply: `make check`
