# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
- `CLAUDE.md` — completed with full project context
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
- `CLAUDE.md` — complete project guide for Claude Code

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
