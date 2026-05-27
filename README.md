# Confidence Map

**Multi-agent AI platform for software architecture and delivery intelligence.**

Confidence Map analyzes software specifications with six specialized agents working in parallel, generating a visual map of decisions, risks, and uncertainties with explicit confidence levels.

---

## The Problem It Solves

Engineering teams:
- Work with ambiguous specifications without knowing it
- Make architectural decisions without traceability
- Discover risks too late in the delivery cycle
- Rely on AI tools that answer without explaining their reasoning

Confidence Map makes reasoning **visible** and **accessible** to everyone.

---

## Differentiator

> It is not a chatbot. Not a copilot. Not a code generator.
> It is a **visible reasoning system** for engineering and delivery.

Every response includes:
- What it knows for certain
- What it reasonably infers
- What it assumes
- What contradictions it found
- What needs validation

---

## The Six Agents

| Agent | Function |
|-------|----------|
| **Spec Analyst** | Detects ambiguity, contradictions, and incomplete requirements |
| **Architecture Validator** | Validates architecture, dangerous coupling, and drift |
| **Risk Intelligence** | Security, delivery risks, and observability gaps |
| **Business Impact** | Cloud cost, delivery velocity, and regulatory risk |
| **Accessibility Advocate** | WCAG 2.1 AA, screen readers, keyboard navigation |
| **Delivery Historian** | Historical patterns and industry post-mortems |

---

## The Confidence Map

The visual map is the star of the platform.

| Level | Color | Meaning |
|-------|-------|---------|
| **Green** | 🟢 | Explicitly defined in the specification |
| **Yellow** | 🟡 | Reasonably inferred from context |
| **Red** | 🔴 | High uncertainty, contradiction, or missing |

---

## Technical Architecture

```
┌─────────────────────────────────┐
│         Frontend (Next.js 15)   │
│   React Flow · Tailwind CSS     │
│   i18n EN/ES/PT · WCAG 2.1 AA  │
└──────────────┬──────────────────┘
               │ SSE streaming
┌──────────────▼──────────────────┐
│         Backend (FastAPI)       │
│   Python 3.12 · uv · mypy      │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│    Orchestrator (asyncio)       │
│   Spec Analyst (sequential)     │
│   5 agents in parallel          │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│   Anthropic API (Claude)        │
│   claude-sonnet-4-6             │
│   Structured tool use           │
└─────────────────────────────────┘
```

---

## Repository Structure

```
confidence-map/
├── backend/              # FastAPI + 6 agents
│   ├── confidence_map/   # Main Python package
│   ├── tests/            # pytest · 42 tests · ≥80% coverage
│   └── pyproject.toml    # uv · mypy · ruff · pytest
├── frontend/             # Next.js 15 App Router
│   ├── app/              # Pages
│   └── components/       # React components
├── docs/                 # Architecture reference and proposal
├── QUICKSTART.md         # Quick start guide
└── CHANGELOG.md          # Version history
```

---

## Quick Start

See [QUICKSTART.md](./QUICKSTART.md) for full instructions.

```bash
# Option 1: Makefile (recommended)
make setup && make demo

# Option 2: Manual
cd backend && uv run uvicorn confidence_map.main:app --reload
cd frontend && pnpm dev
```

---

## Project Status

**Full demo — Phases 0–5 implemented.**

- DEMO_MODE: analysis without API key, $0 cost
- Visual map with real-time animations
- Filterable decision table
- Accessible text mode (WCAG 2.1 AA)
- Two demo specs: NovaBank Payments + Auth MFA
- Shareable URL with `?spec=payments|auth`
- Multi-language support: English, Spanish, Portuguese (BR)

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, uv |
| AI | Anthropic SDK, Claude Sonnet 4.6 |
| Type safety | mypy --strict, Pydantic v2 |
| Tests | pytest, pytest-asyncio, 42 tests, coverage ≥80% |
| Frontend | Next.js 15, TypeScript strict |
| Package manager | pnpm 10 |
| Visualization | React Flow, dagre layout |
| Styles | Tailwind CSS |
| i18n | React Context + JSON messages (EN/ES/PT) |

---

## Development Principles

- Strict static typing (Python 3.12+, TypeScript strict)
- Mandatory tests with minimum 80% coverage
- Dependency management: `uv` (backend) · `pnpm` (frontend)
- WCAG 2.1 AA accessibility as a production requirement
- Clean and minimal code (YAGNI)
