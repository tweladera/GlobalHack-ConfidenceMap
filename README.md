# Confidence Map

**Multi-agent AI platform for software architecture and delivery intelligence.**

Confidence Map analyzes software specifications and architecture documents using seven specialized AI agents working in parallel. It generates a live visual map of decisions, risks, and uncertainties — each with an explicit confidence level, evidence, and a recommended action.

---

## The Problem It Solves

Engineering teams:
- Work with ambiguous specifications without realizing it
- Make architectural decisions without traceability
- Discover risks too late in the delivery cycle
- Use AI tools that produce answers without exposing their reasoning

Confidence Map makes reasoning **visible** and **auditable** by everyone on the team.

---

## Differentiator

> It is not a chatbot. Not a copilot. Not a code generator.
> It is a **visible reasoning system** for engineering and delivery teams.

Every finding includes:
- What the agent knows for certain (green)
- What it reasonably infers (yellow)
- What it cannot determine — high uncertainty (red)
- Evidence from the spec or architecture
- Assumptions it made
- What needs validation
- A concrete recommended action

After the six specialists complete, a **Consolidator** cross-audits all findings and surfaces:
- **Confirmed Criticals** — risks flagged RED by two or more independent agents
- **Contradictions** — findings where agents disagree on severity or interpretation
- **Redundancies** — duplicate findings, with the most complete version kept

---

## The Seven Agents

| Agent | Function |
|-------|----------|
| **Spec Analyst** | Detects ambiguity, contradictions, and incomplete requirements |
| **Architecture Validator** | Validates architecture decisions, dangerous coupling, and drift |
| **Risk Intelligence** | Security posture, delivery risks, and observability gaps |
| **Business Impact** | Revenue risk, regulatory exposure, and delivery cost |
| **Accessibility Advocate** | WCAG 2.1 AA, screen readers, keyboard navigation |
| **Delivery Historian** | Historical failure patterns and industry post-mortems |
| **Consolidator** | Cross-audit: confirmed criticals, contradictions, redundancies |

---

## Confidence Levels

| Level | Color | Meaning |
|-------|-------|---------|
| **Green** | 🟢 | Explicitly defined in the specification |
| **Yellow** | 🟡 | Reasonably inferred from context |
| **Red** | 🔴 | High uncertainty, contradiction, or missing information |

---

## Views

| View | Shortcut | Description |
|------|----------|-------------|
| **Confidence Map** | Alt+1 | Live React Flow graph — hub → agents → findings |
| **Decision Table** | Alt+2 | Filterable table by confidence level and agent |
| **Text Mode** | Alt+3 | Full document view, copy executive summary |
| **Risk Heat Map** | Alt+4 | 5×5 Likelihood × Impact matrix |

---

## Technical Architecture

```
┌─────────────────────────────────────────────┐
│              Frontend (Next.js 15)           │
│   React Flow · Tailwind CSS · TypeScript     │
│   4 views · Export · Backlog · Chat · History│
└──────────────────┬──────────────────────────┘
                   │ SSE streaming
┌──────────────────▼──────────────────────────┐
│              Backend (FastAPI)               │
│          Python 3.12 · uv · mypy            │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         Orchestrator (asyncio)              │
│                                             │
│  Phase 1: Spec Analyst (sequential)         │
│        ↓  findings shared as blackboard     │
│  Phase 2: 5 agents in parallel              │
│           Semaphore(3) concurrency limit    │
│        ↓                                    │
│  Phase 3: Consolidator (cross-audit)        │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│        Anthropic API (Claude)               │
│        claude-sonnet-4-6                    │
│        Structured tool use (JSON output)    │
│        Optional extended thinking           │
└─────────────────────────────────────────────┘
```

### SSE Event Flow

```
agent_start (×6) → agent_complete/error (×6)
→ consolidation_start → consolidation_complete
→ analysis_complete
```

---

## Repository Structure

```
confidence-map/
├── backend/
│   ├── confidence_map/
│   │   ├── agents/        # 7 agents (base.py + 6 specialists + consolidator.py)
│   │   ├── api/           # FastAPI routes: analysis.py (SSE) + chat.py
│   │   ├── core/          # orchestrator.py, mock_results.py, settings.py
│   │   └── models/        # Pydantic v2: analysis, events, findings, chat
│   ├── evals/             # Golden spec evaluation framework (make eval)
│   ├── tests/             # 94 tests · 89.84% coverage
│   └── pyproject.toml     # uv · mypy --strict · ruff · pytest
├── frontend/
│   ├── app/               # Next.js App Router (page.tsx, analysis/page.tsx)
│   ├── components/        # ConfidenceMap, DecisionTable, HeatMap, FindingDetail,
│   │                      # AgentStatusCard, BacklogModal, ChatPanel, AccessibleSummary
│   ├── lib/               # demo-spec.ts, export.ts, history.ts, i18n.tsx
│   ├── messages/          # en.json (English only)
│   └── types/index.ts     # Shared TypeScript types
├── QUICKSTART.md          # Setup guide (under 10 minutes)
├── CHANGELOG.md           # Version history
└── AGENTS.md              # AI assistant instructions for this repo
```

---

## Architecture Diagrams

| Diagram | Description |
|---------|-------------|
| [Harness Engineering](./docs/diagram-harness-engineering.md) | End-to-end system architecture and component relationships |
| [LLM as a Judge](./docs/diagram-llm-as-a-judge.md) | How the Consolidator cross-audits agent findings |
| [Spec to Data Pipelines](./docs/diagram-spec-to-data-pipelines.md) | Data flow from spec input to confidence map output |

---

## Quick Start

See [QUICKSTART.md](./QUICKSTART.md) for full instructions.

```bash
make setup    # First time: verify tools, create .env, install deps
make demo     # Start backend (:8000) + frontend (:3000) — no API key needed
```

Open `http://localhost:3000`, select a preset spec, click **Run Analysis**.

**Demo mode**: ~5 seconds, $0 cost, uses pre-generated realistic results.
**Real mode**: ~5 minutes, requires `ANTHROPIC_API_KEY` in `backend/.env`.

---

## Features

| Feature | Description |
|---------|-------------|
| **Live confidence map** | Real-time React Flow graph, animates as agents complete |
| **Cross-agent audit** | Consolidator identifies confirmed criticals and contradictions |
| **Risk Heat Map** | 5×5 matrix — Likelihood × Impact (Alt+4) |
| **Export** | Markdown report · Styled PDF (no dependencies) |
| **Backlog generator** | JIRA-ready tickets from red/yellow findings |
| **AI Chat** | Ask questions about the analysis — full context streaming |
| **Analysis History** | Last 5 analyses saved locally |
| **Redundancy filter** | "Hide duplicates" — collapses findings flagged as redundant |
| **Extended thinking** | Optional chain-of-thought per agent (`ENABLE_THINKING=true`) |
| **Eval framework** | Golden spec recall scoring (`make eval`) |
| **Demo presets** | NovaBank Payments (`?spec=payments`) · Auth MFA (`?spec=auth`) |
| **WCAG 2.1 AA** | ARIA live regions, keyboard navigation, screen reader tested |

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, uv |
| AI | Anthropic SDK, Claude Sonnet 4.6, structured tool use |
| Type safety | mypy --strict, Pydantic v2 |
| Tests | pytest, pytest-asyncio, 94 tests, 89.84% coverage |
| Frontend | Next.js 15, TypeScript strict, pnpm 10 |
| Visualization | React Flow, dagre auto-layout |
| Styles | Tailwind CSS |

---

## Environment Variables (`backend/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `DEMO_MODE` | `true` | `true` = pre-generated results, $0 cost |
| `ANTHROPIC_API_KEY` | — | Required when `DEMO_MODE=false` |
| `MODEL` | `claude-sonnet-4-6` | Claude model (`claude-haiku-4-5-20251001` for lower cost) |
| `ENABLE_THINKING` | `false` | Extended chain-of-thought per agent (~+$0.45/analysis on Sonnet) |
| `THINKING_BUDGET_TOKENS` | `5000` | Token budget per agent when thinking is enabled |
| `FRONTEND_URL` | `http://localhost:3000` | CORS allowed origin |

---

## Development

```bash
make check    # ruff + mypy + pytest + tsc — all gates must pass
make test     # pytest only (94 tests, ≥80% coverage required)
make eval     # golden spec evaluations (requires real API key)
make stop     # kill processes on :8000 and :3000
```

### Pre-push checklist

```bash
cd backend && uv run ruff check confidence_map/           # 0 errors
cd backend && uv run mypy --strict confidence_map/        # 0 errors
cd backend && ANTHROPIC_API_KEY=test uv run pytest -q     # 81 passed
cd frontend && pnpm exec tsc --noEmit                     # no output = ok
```

Or: `make check`
