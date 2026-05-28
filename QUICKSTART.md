# Quick Start Guide — Confidence Map

From zero to running in under 10 minutes.

---

## Prerequisites

| Tool | Minimum version | Verify |
|------|----------------|--------|
| Python | 3.12+ | `python3 --version` |
| uv | 0.11+ | `uv --version` |
| Node.js | 20+ | `node --version` |
| pnpm | 8+ | `pnpm --version` |

```bash
# Install uv (if missing)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install pnpm (if missing)
npm install -g pnpm
```

---

## Option A — Makefile (recommended)

```bash
make setup    # Verify tools, create backend/.env, install all deps
make demo     # Start backend (:8000) + frontend (:3000) in demo mode
```

Open `http://localhost:3000`, select a preset, click **Run Analysis**.

---

## Option B — Manual setup

### 1. Configure the backend

```bash
cd backend
cp .env.example .env
```

Edit `backend/.env`:

```env
# Demo mode: no API key needed, pre-generated results, $0 cost
DEMO_MODE=true

# Only needed when DEMO_MODE=false
ANTHROPIC_API_KEY=sk-ant-api03-XXXXXXXX

# Model (haiku = faster/cheaper for dev, sonnet = quality for demo)
MODEL=claude-sonnet-4-6

# Extended thinking (optional — adds ~$0.45/analysis on Sonnet)
ENABLE_THINKING=false
THINKING_BUDGET_TOKENS=5000

FRONTEND_URL=http://localhost:3000
```

```bash
uv sync
ANTHROPIC_API_KEY=test uv run pytest --no-header -q
# → 81 passed, coverage 87.94%

uv run uvicorn confidence_map.main:app --reload
# → http://localhost:8000/health
```

### 2. Start the frontend

```bash
cd frontend
pnpm install --registry https://registry.npmjs.org
pnpm dev
# → http://localhost:3000
```

---

## Running an Analysis

1. Open `http://localhost:3000`
2. Click **"NovaBank · Payments"** or **"NovaBank · Auth MFA"** to load a preset
   - Or paste your own spec (PRD) and architecture document
3. Click **Run Analysis**

### What happens

**Phase 1** — Spec Analyst runs first and shares its findings with the other agents.

**Phase 2** — Five agents run in parallel (max 3 concurrent API calls):
- Architecture Validator
- Risk Intelligence
- Business Impact
- Accessibility Advocate
- Delivery Historian

**Phase 3** — Consolidator cross-audits all findings:
- **Confirmed Criticals**: risks flagged RED by ≥2 independent agents
- **Contradictions**: findings where agents disagree
- **Redundancies**: duplicate findings (one canonical version kept)

### Timing

| Mode | Duration | Cost |
|------|----------|------|
| `DEMO_MODE=true` | ~5 seconds | $0 |
| Real · Haiku | ~60–90 seconds | ~$0.003 |
| Real · Sonnet | ~4–6 minutes | ~$0.05–0.10 |
| Real · Sonnet + Thinking | ~8–12 minutes | ~$0.50–0.55 |

---

## Navigating the Results

### Views (keyboard shortcuts)
- **Alt+1** — Confidence Map (React Flow graph)
- **Alt+2** — Decision Table (filterable)
- **Alt+3** — Text Mode (copy executive summary)
- **Alt+4** — Risk Heat Map (5×5 Likelihood × Impact)

### Confidence Map
- **Hub node** — shows global confidence % once analysis completes
- **Agent nodes** — stacked colored bar shows severity distribution (green/yellow/red)
- **Finding nodes** — left accent strip indicates severity; click to open detail panel
- **Cross-Agent Audit** (right sidebar) — Confirmed Criticals with ⚠ marker appear first

### Finding Detail
- **Evidence** — exact quote from spec/architecture, border color matches confidence level
- **Assumptions** — what the agent assumed when the spec was silent
- **Needs validation** — open questions that block implementation
- **→ What to do** — highlighted recommended action

### Post-analysis tools (header buttons)
- **Export ▾** — Download Markdown `.md` or open styled PDF report
- **Backlog** — Generate JIRA-ready tickets from red/yellow findings
- **Ask AI** — Inline chat panel with full analysis context

### Sidebar features
- **Findings list** — all findings scrollable; "Hide duplicates" toggle appears when the
  consolidator identified redundant findings
- **Show reasoning** — per-agent toggle if `ENABLE_THINKING=true` in backend

---

## Demo Presets

| Preset | URL param | Spec |
|--------|-----------|------|
| NovaBank · Payments | `?spec=payments` | International instant payments — legacy SWIFT gateway |
| NovaBank · Auth MFA | `?spec=auth` | Multi-factor authentication — regulatory deadline |

Both presets are split into two separate inputs:
- **Spec** — pure PRD (business context, user stories, NFRs, compliance)
- **Architecture** — technical document (system design, constraints, infrastructure)

---

## Eval Framework

Evaluates agents against golden specs with recall-based scoring:

```bash
make eval                    # run all golden specs (requires real API key)
cd backend && uv run python -m evals --spec simplebank   # single spec
```

Specs: `SIMPLEBANK` (4 criteria, 3 agents) · `MEDIPAY` (4 criteria, 3 agents).
Minimum recall threshold: 0.60.

---

## Environment Variables Reference

### `backend/.env`

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEMO_MODE` | No | `false` | `true` = pre-generated results |
| `ANTHROPIC_API_KEY` | When not demo | — | Anthropic API key |
| `MODEL` | No | `claude-sonnet-4-6` | Claude model |
| `ENABLE_THINKING` | No | `false` | Per-agent extended chain-of-thought |
| `THINKING_BUDGET_TOKENS` | No | `5000` | Token budget per agent for thinking |
| `FRONTEND_URL` | No | `http://localhost:3000` | CORS allowed origin |

### Model options

| Model | Speed | Cost (per full analysis) | Use for |
|-------|-------|--------------------------|---------|
| `claude-haiku-4-5-20251001` | Fast | ~$0.003 | Development |
| `claude-sonnet-4-6` | Medium | ~$0.05–0.10 | Demo / production |

---

## Makefile Reference

```bash
make setup    # First-time setup
make demo     # DEMO_MODE=true — no API key needed
make dev      # Real mode — needs API key in backend/.env
make stop     # Kill :8000 and :3000
make check    # All quality gates: ruff + mypy + tsc + pytest
make test     # pytest only
make eval     # Golden spec evaluations (real API key required)
make health   # curl /health
```

---

## Troubleshooting

### `pydantic_settings.main.SettingsError: field required`
Create `backend/.env` (copy from `.env.example`) and set `DEMO_MODE=true`.

### `Connection refused` when running analysis
Backend is not running:
```bash
cd backend && uv run uvicorn confidence_map.main:app --reload
```

### `pnpm install` fails with 401
Private registry active. Override:
```bash
pnpm install --registry https://registry.npmjs.org
```

### Analysis never completes (real mode)
Check that your `ANTHROPIC_API_KEY` has credits. Switch to demo mode:
```env
DEMO_MODE=true
```

### Tests fail with import errors
```bash
cd backend && uv sync
```
