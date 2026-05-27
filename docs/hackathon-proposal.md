# Confidence Map — Hackathon Proposal

**Track:** AI / Developer Tooling
**Team:** Evans Ladera
**Date:** May 2026

---

## The Problem

Engineering teams make critical decisions every day based on incomplete or ambiguous specifications. The current state is broken:

- Teams work with **ambiguous specs without knowing it** — requirements are vague, contradictory, or missing key behaviors
- **Architectural decisions lack traceability** — no one knows why a pattern was chosen or what risks it carries
- **Risks surface too late** — security holes, compliance gaps, and accessibility barriers are discovered in production, not design
- **AI tools answer without explaining their reasoning** — current copilots generate output but cannot surface what they assume, infer, or are uncertain about

The result: wasted sprints, production incidents, and expensive rework that could have been prevented before the first line of code was written.

---

## The Solution

**Confidence Map** is a multi-agent AI platform that analyzes software specifications and makes engineering reasoning **visible** and **actionable**.

It is not a chatbot. It is not a code generator. It is a **visible reasoning system** for engineering and delivery teams.

### How it works

1. The team pastes a PRD, user stories, or any engineering specification
2. Six specialized AI agents analyze it **simultaneously in parallel**
3. Each agent returns structured findings with explicit confidence levels
4. Results stream in real-time onto an **interactive visual confidence map**
5. Every finding includes: what is known, what is inferred, what is assumed, and what needs validation

---

## The Six Agents

| Agent | Responsibility |
|-------|---------------|
| **Spec Analyst** | Detects ambiguity, contradictions, and incomplete requirements |
| **Architecture Validator** | Validates architectural decisions, dangerous coupling, and SLA contradictions |
| **Risk Intelligence** | Identifies security gaps, delivery risks, and observability blind spots |
| **Business Impact** | Connects engineering decisions to business outcomes and quantified costs |
| **Accessibility Advocate** | Evaluates against WCAG 2.1 AA — inclusion from day one, not as an afterthought |
| **Delivery Historian** | Draws from software delivery history and industry post-mortems |

---

## The Confidence Map

The visual map is the heart of the platform. Every finding is plotted with an explicit confidence level:

| Level | Color | Meaning |
|-------|-------|---------|
| **Green** | 🟢 | Explicitly and clearly defined in the specification |
| **Yellow** | 🟡 | Reasonably inferred from context — not explicit |
| **Red** | 🔴 | Missing, contradictory, or too ambiguous to implement safely |

This visual language gives any stakeholder — engineer, PM, CTO, or auditor — an immediate understanding of where the risks are and how confident the team should be before starting development.

---

## Why This Matters for Inclusion

Confidence Map was built with accessibility as a first-class requirement, not an afterthought:

- **WCAG 2.1 AA compliance** throughout the interface
- **Screen reader support** with progressive narration — every agent completion is announced
- **Keyboard navigation** — full analysis workflow accessible without a mouse (Alt+1/2/3 view shortcuts)
- **Text mode** — a complete accessible document view alongside the visual map
- **Multi-language support** — English, Spanish, and Portuguese (Brazilian), removing language barriers for global teams
- The **Accessibility Advocate agent** ensures the analyzed product itself will not exclude users with disabilities

Confidence Map fights the same barriers it helps teams avoid.

---

## Demo Scenarios

Two pre-built specifications demonstrate the platform's value:

### NovaBank · International Payments
A fintech spec with deliberate ambiguities: an SLA regulators require but the architecture cannot meet, missing idempotency that would cause duplicate payments, and a single point of failure. The agents surface all of this in under 5 seconds.

### NovaBank · MFA Authentication
A security-critical spec with AES-128 encryption (weak for a financial institution), recovery codes hashed with MD5, and a Twilio integration with no fallback. The agents identify every vulnerability before a line of code is written.

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

### Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, uv |
| AI | Anthropic SDK, Claude Sonnet 4.6 |
| Type safety | mypy --strict, Pydantic v2 |
| Tests | pytest, pytest-asyncio, 42 tests, ≥80% coverage |
| Frontend | Next.js 15, TypeScript strict |
| Package manager | pnpm 10 |
| Visualization | React Flow, dagre auto-layout |
| Styles | Tailwind CSS |
| i18n | React Context + JSON message files (EN/ES/PT) |

---

## What Makes This Different

**Existing tools** (GitHub Copilot, ChatGPT, Cursor) answer questions. They do not explain:
- What they assume
- What they infer vs. what is explicitly stated
- Where uncertainty is high
- What contradictions exist in the source material

**Confidence Map surfaces the reasoning**, not just the answer. It makes the invisible visible: the ambiguities your team works around without noticing, the assumptions baked into your architecture, the compliance gaps that will surface in production.

---

## Running the Demo

```bash
# Clone and start in demo mode (no API key required, $0 cost)
make setup
make demo

# Open http://localhost:3000
# Select "NovaBank · Payments" or "NovaBank · Auth MFA"
# Click "Run Analysis"
# Watch 6 agents activate in real time
```

Demo mode (`DEMO_MODE=true`) uses pre-generated realistic results. The analysis completes in approximately 5 seconds.

With a real Anthropic API key (`DEMO_MODE=false`), the analysis runs against Claude claude-sonnet-4-6 and takes 60–120 seconds for 6 parallel agents.

---

## Engineering Quality

Built to production standards, not just hackathon standards:

- `mypy --strict` — zero type errors across 20 source files
- `ruff` — zero linting warnings
- 42 tests — 91.54% code coverage (80% minimum enforced)
- WCAG 2.1 AA — accessibility tested with screen readers
- No secrets committed — CI/CD ready

---

## Future Roadmap (Post-Hackathon)

- **Persistent analysis history** — PostgreSQL/Supabase storage, compare specs over time
- **Jira integration** — create tickets directly from findings
- **GitHub integration** — analyze PRDs from issues, trigger on PR
- **CI/CD plugin** — run confidence analysis on every spec change
- **LangGraph orchestration** — formal agent state machine
- **Extended language support** — French, German, Japanese

---

*Confidence Map was designed in 5 sessions over one week, built with Claude Code, and tested on real-world fintech specifications. The goal: make the reasoning that engineers do every day visible to the entire team — regardless of technical background, language, or ability.*
