# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased] — feat/shared-blackboard (merged to main)

### Added — Backend
- **Consolidator agent** (7th agent): cross-audits all 6 specialist agents; detects
  confirmed criticals (≥2 agents flagging RED), contradictions, and redundancies;
  emits `CONSOLIDATION_START` / `CONSOLIDATION_COMPLETE` SSE events; never raises
- **Shared blackboard**: Spec Analyst findings passed to Phase 2 agents for context
- **Orchestrator Phase 3**: sequential Consolidator run after parallel Phase 2
- **Semaphore(3)**: concurrency limit on Phase 2 Claude API calls
- **Retry policy**: exponential backoff (base 2s) on `RateLimitError` and 5xx errors (max 2 retries)
- **Score guardrails**: green [0.60–1.00], yellow [0.30–0.75], red [0.00–0.45]
- **Extended thinking**: `ENABLE_THINKING` + `THINKING_BUDGET_TOKENS` env vars;
  per-agent chain-of-thought extraction; "Show reasoning" toggle in UI
- **Eval framework** (`backend/evals/`): golden spec recall scoring, `make eval` CLI;
  SIMPLEBANK and MEDIPAY golden specs with DetectionCriteria
- **AI Chat endpoint**: `POST /api/chat/stream` — full analysis context, multi-turn,
  streaming SSE, demo mode canned response
- **New models**: `Contradiction`, `ConfirmedCritical`, `Redundancy`, `ConsolidatorResult`,
  `ChatRequest`, `ChatMessage`; `thinking: str` field on `AgentResult`
- **81 tests** (up from 42): added test_consolidator.py, test_chat.py; extended
  test_base_agent.py (thinking extraction, call_agent thinking capture)

### Added — Frontend
- **Cross-Agent Audit panel**: Confirmed Criticals (⚠ + red accent strip), Contradictions,
  Audit Summary — rendered above the findings list after consolidation
- **Risk Heat Map**: 5×5 Likelihood × Impact matrix (`HeatMap.tsx`, Alt+4)
- **Export**: Markdown `.md` download + styled PDF report (no external deps)
- **Backlog generator**: JIRA-ready tickets from red/yellow findings (`BacklogModal.tsx`)
- **AI Chat**: inline sidebar panel (`ChatPanel.tsx`), multi-turn, streaming
- **Analysis History**: localStorage, last 5 analyses shown on home page (`history.ts`)
- **Redundancy filter**: "Hide duplicates" toggle using consolidation redundancy data
- `globalScore` prop on `ConfidenceMap` — hub node displays score post-analysis

### Changed — Frontend UI (visual polish)
- **HubNode**: w-28, shows global confidence % with severity color once analysis completes;
  animated ◎ while in progress
- **AgentNode**: stacked severity bar (green/yellow/red proportional) above count badges
- **FindingNode**: left accent strip (1.5px RED, 1px Y/G), `border-2` for RED findings,
  score in bold, `line-clamp-2` on title; `overflow-hidden` + `relative` for clean layout
- **FindingDetail**: evidence border color matches confidence level; Recommended Action
  promoted to highlighted accent card with `→` prefix
- **Confirmed Criticals**: absolute-positioned red accent strip + ⚠ icon + `text-slate-100`
- Panel reorder: Cross-Agent Audit now appears above findings list

### Changed — Demo specs
- `DEMO_SPEC` is now pure PRD: business context, user stories (acceptance criteria only),
  NFRs, security/compliance, out of scope — no implementation details
- `DEMO_ARCHITECTURE` now opens with a full Technical Constraints section (CoreBanking
  latency, FraudShield timing, Oracle 11g, infra, no retry/timeout/idempotency)
- Same split applied to `DEMO_SPEC_AUTH` / `DEMO_ARCH_AUTH`

### Removed
- Multi-language i18n: LanguageSwitcher component, `es.json`, `pt-br.json`, translator.py
- Language field from all agent models and API payloads

---

## [Unreleased] — feat/global-hackathon-presentation

### Added
- Multi-language support (EN / ES / PT-BR) with React Context i18n
- Language switcher component in the analysis header
- `docs/hackathon-proposal.md` — professional project proposal in Markdown
- `CHANGELOG.md` — this file

### Changed
- Full English migration: UI, mock findings, demo specs, documentation
- Demo specs translated: NovaBank Payments + Auth MFA (English)
- Mock findings translated to English (all 6 agents × 4–5 findings each)
- `README.md` — rewritten in English
- `QUICKSTART.md` — rewritten in English
- `AGENTS.md` — completed with full project context
- Preset labels: "NovaBank · Pagos" → "NovaBank · Payments", URL param `?spec=payments`

### Removed
- PDF documents removed from git tracking (kept locally): `Confidence_Map_*.pdf`
- `STATUS.md` and `PLAN.md` moved to local-only (added to `.gitignore`)

### Branch naming convention established
- Format: `<type>/<short-description>`
- Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`
- Example: `feat/global-hackathon-presentation`

---

## [0.3.0] — 2026-05-26 · commit `f9919a8`

### Added
- `Makefile` with full project orchestration (`make setup/dev/demo/check/test/stop`)
- `.claude/commands/` — custom Claude Code slash commands (`/check`, `/demo`, `/status`)
- `AGENTS.md` — complete project guide for Claude Code

### Fixed
- Ruff E501 lint error in `agents/base.py` tool description string

---

## [0.2.0] — 2026-05-26 · commit `1dc67aa`

### Changed
- Migrated frontend package manager: npm → pnpm 10
- `pyproject.toml` consolidated: `[dependency-groups]` (PEP 735), no duplicate entries
- `backend/.env.example` — removed real API key, replaced with placeholder

### Fixed
- `package-lock.json` removed, `pnpm-lock.yaml` added
- All documentation updated to reflect pnpm usage

---

## [0.1.0] — 2026-05-25 · commit `20ae883`

### Added
- **6 specialized agents** powered by Claude Sonnet 4.6 with structured tool use:
  - Spec Analyst, Architecture Validator, Risk Intelligence
  - Business Impact, Accessibility Advocate, Delivery Historian
- **FastAPI backend** with SSE streaming endpoint (`/api/analyze/{id}/stream`)
- **Next.js 15 frontend** with React Flow confidence map visualization
- **DEMO_MODE** — full analysis without API key, pre-generated realistic mock results
- **Confidence map** with dagre auto-layout, animated agent nodes, confidence score bars
- **Decision table** — filterable by confidence level (All / Critical / Inferred / Confirmed)
- **Text mode** — full accessible document view (Alt+3)
- **Keyboard shortcuts** — Alt+1 Map · Alt+2 Table · Alt+3 Text
- **Aria-live progressive narration** — screen readers follow agent completion in real time
- **Executive summary** with global confidence score, copy to clipboard (Markdown)
- **Shareable URLs** — `?spec=payments` and `?spec=auth` auto-load presets
- **42 tests** — 91.54% coverage, mypy --strict (0 errors), ruff (0 warnings)
- **Two demo scenarios**: NovaBank Payments + NovaBank MFA Authentication
- WCAG 2.1 AA accessibility throughout

### Technical decisions
- `asyncio.gather` for parallel agent execution (reliability over LangGraph complexity)
- Anthropic tool use for structured output (avoids fragile free-text parsing)
- dagre layout for React Flow (automatic node positioning)
- `uv` as Python package manager
- `pnpm` as Node.js package manager (migrated from npm in v0.2.0)

---

## [0.0.1] — 2026-05-20 · commit `2852b05`

### Added
- Initial project structure: `backend/` + `frontend/` monorepo
- Python package scaffold with FastAPI + Pydantic v2
- Next.js 15 App Router scaffold with TypeScript strict
- Base agent architecture with `call_agent()` runner
- `pyproject.toml` with uv, ruff, mypy, pytest configuration
