# Quick Start Guide — Confidence Map

This guide takes the project from zero to running in under 10 minutes.

---

## Prerequisites

Install these tools before starting:

| Tool | Minimum version | Verify |
|------|----------------|--------|
| Python | 3.12+ | `python3 --version` |
| uv | 0.11+ | `uv --version` |
| Node.js | 20+ | `node --version` |
| pnpm | 8+ | `pnpm --version` |

### Install uv (if not present)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install pnpm (if not present)
```bash
npm install -g pnpm
```

---

## Recommended: Makefile (one command)

```bash
make setup    # First time: verify tools, create .env, install dependencies
make demo     # Start backend + frontend in DEMO_MODE (no API key needed)
```

Open `http://localhost:3000`, select a preset, and click **Run Analysis**.

---

## Manual Setup

### Step 1 — Get an Anthropic API key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create an account or sign in
3. Go to **API Keys** → **Create Key**
4. Copy the key (starts with `sk-ant-...`)

> **Note:** The **demo mode** (`DEMO_MODE=true`) does not use any credits — it uses pre-generated results. An API key is only needed for real analysis.

---

### Step 2 — Configure the backend

```bash
cd backend
cp .env.example .env
```

Edit `backend/.env`:

```env
# Demo mode: true = no API key ($0 cost), false = real Claude API
DEMO_MODE=true

# Only required when DEMO_MODE=false
ANTHROPIC_API_KEY=sk-ant-api03-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Model to use (switch to haiku to reduce costs)
MODEL=claude-sonnet-4-6

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:3000
```

Install dependencies:

```bash
uv sync
```

Verify:

```bash
ANTHROPIC_API_KEY=test uv run pytest --no-header -q
# Expected: 42 passed, coverage ≥80%
```

Start the server:

```bash
uv run uvicorn confidence_map.main:app --reload
```

Health check: `http://localhost:8000/health` → `{"status":"ok","version":"0.1.0"}`

---

### Step 3 — Configure the frontend

Open a new terminal:

```bash
cd frontend
pnpm install --registry https://registry.npmjs.org
pnpm dev
```

> The `--registry` flag is required if your system has a private registry configured (Artifactory, Nexus, etc.).

Open `http://localhost:3000`.

---

### Step 4 — Run the demo

1. Open `http://localhost:3000`
2. Click **"NovaBank · Payments"** or **"NovaBank · Auth MFA"** to load a demo spec
3. Click **"Run Analysis"**
4. Watch the 6 agents activate in real time on the map

With `DEMO_MODE=true`: completes in approximately **5 seconds**.
With real API: takes **60–120 seconds** (6 agents × ~20s with parallelism).

---

## Environment Variables Reference

### Backend (`backend/.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEMO_MODE` | No | `false` | `true` = pre-generated results, no API |
| `ANTHROPIC_API_KEY` | Only if `DEMO_MODE=false` | — | Anthropic API key |
| `MODEL` | No | `claude-sonnet-4-6` | Claude model to use |
| `FRONTEND_URL` | No | `http://localhost:3000` | Allowed CORS origin |

### Available models

| Model | Speed | Relative cost | Recommended for |
|-------|-------|---------------|-----------------|
| `claude-haiku-4-5-20251001` | Fast | Low (~1x) | Development and testing |
| `claude-sonnet-4-6` | Medium | Medium (~5x) | Demo and production |

### Frontend

No environment variables required for local development. The `next.config.ts` proxy redirects `/api/*` → `localhost:8000` automatically.

---

## Reducing API Key Usage

### Option 1: Demo mode with pre-generated results (recommended)
```env
DEMO_MODE=true
```
The analysis uses realistic pre-generated results — $0 cost.

### Option 2: Use Haiku in `.env`
```env
DEMO_MODE=false
MODEL=claude-haiku-4-5-20251001
```

### Option 3: Mock the API in tests
Tests use mocks and never call the real API:
```bash
ANTHROPIC_API_KEY=test uv run pytest
```

---

## Verify Everything Works

```bash
# Terminal 1: backend
cd backend && uv run uvicorn confidence_map.main:app --reload

# Terminal 2: frontend
cd frontend && pnpm dev

# Terminal 3: verify health
curl http://localhost:8000/health
# → {"status":"ok","version":"0.1.0"}
```

Open `http://localhost:3000`, load a preset, run the analysis.

---

## Troubleshooting

### Error: `ANTHROPIC_API_KEY` not configured
```
pydantic_settings.main.SettingsError: field required
```
Solution: create `backend/.env` with `DEMO_MODE=true` (or add the key).

### Error: `Connection refused` when running analysis
The backend is not running. Execute:
```bash
cd backend && uv run uvicorn confidence_map.main:app --reload
```

### Error: `pnpm install` fails with 401
Private registry detected. Use:
```bash
pnpm install --registry https://registry.npmjs.org
```

### Analysis takes too long
Switch to demo mode in `backend/.env`:
```env
DEMO_MODE=true
```
Or use Haiku:
```env
MODEL=claude-haiku-4-5-20251001
```

### Tests fail with import error
```bash
cd backend && uv sync
```

---

## Quick Reference

```bash
# Install everything
make setup

# Start (demo mode, no API key)
make demo

# Start (real mode, needs API key in backend/.env)
make dev

# Quality gates
make check

# Tests only
make test

# Stop all services
make stop
```
