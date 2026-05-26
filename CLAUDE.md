# Confidence Map — Guía para Claude Code

Plataforma de inteligencia para arquitectura/delivery con 6 agentes IA especializados.
Analiza especificaciones de software y genera un mapa visual de decisiones, riesgos e
incertidumbres con niveles de confianza explícitos.

---

## Comandos esenciales

```bash
make setup          # Primera vez: verifica tools, crea .env, instala deps
make dev            # Levanta backend (:8000) + frontend (:3000)
make demo           # Igual que dev pero fuerza DEMO_MODE=true (sin API key)
make stop           # Mata procesos en :8000 y :3000
make check          # Quality gates completos: lint + tipos + tests
make test           # 42 tests con cobertura (≥80% requerido)
make lint           # ruff check
make format         # ruff format + fix
make typecheck      # mypy backend + tsc frontend
make build          # next build (producción)
make health         # curl /health al backend
```

### Comandos directos (cuando Makefile no aplica)

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

## Estructura del proyecto

```
backend/
  confidence_map/
    agents/         # 6 agentes: spec_analyst, arch_validator, risk_intelligence,
                    #             business_impact, accessibility_advocate, delivery_historian
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
  lib/demo-spec.ts  # Specs NovaBank Pagos + Auth MFA (presets de demo)
  types/index.ts    # Tipos TypeScript compartidos

docs/               # PDFs de propuesta y arquitectura de referencia
```

---

## Reglas críticas

- **NUNCA** commitear `.env` — contiene la API key. Solo `.env.example` va al repo.
- **NUNCA** usar `pip` directamente — siempre `uv run` o `uv sync`.
- **NUNCA** usar `npm` — siempre `pnpm`.
- Los tests **no necesitan API key real**: `ANTHROPIC_API_KEY=test uv run pytest`.
- ruff, mypy y pytest se ejecutan **desde `backend/`**, no desde la raíz.
- `make demo` / `DEMO_MODE=true` para correr la demo sin consumir créditos ($0).

---

## Convenciones de código

### Backend (Python 3.12+)
- Tipado estático: `mypy --strict` — 0 errores es el único estado aceptable.
- Linting: `ruff` con `line-length = 100`.
- Tests: `pytest-asyncio` en modo `auto`, cobertura mínima 80% (actual: 91.54%).
- Dependencias runtime: `pyproject.toml [project.dependencies]`.
- Dependencias dev: `pyproject.toml [dependency-groups] dev`.
- Los agentes heredan de `BaseAgent` (`agents/base.py`) y usan Claude tool use para output estructurado.
- El orquestador (`core/orchestrator.py`) lanza Spec Analyst primero, luego 5 agentes en `asyncio.gather`.

### Frontend (TypeScript strict)
- `tsconfig.json` con `strict: true`.
- Gestor de paquetes: `pnpm` (lockfile: `pnpm-lock.yaml`).
- Visualización: React Flow + dagre layout (auto-posicionamiento de nodos).
- Estilos: Tailwind CSS.
- Proxy API: `next.config.ts` redirige `/api/*` → `localhost:8000`.

---

## DEMO_MODE

Con `DEMO_MODE=true` en `backend/.env` (o `make demo`):
- El backend usa `core/mock_results.py` en lugar de llamar a Claude.
- El SSE streaming funciona igual (con delays simulados).
- El análisis completa en ~5 segundos.
- $0 de costo de API.

Sin `DEMO_MODE` (modo real): 60–120 segundos, requiere créditos en la cuenta Anthropic.

---

## Referencias clave

| Archivo | Propósito |
|---------|-----------|
| `STATUS.md` | Fuente de verdad: estado, checkpoints, checklist de demo |
| `PLAN.md` | Roadmap por fases (Fases 0–5 completas, Fase 6 backlog) |
| `QUICKSTART.md` | Guía de inicio paso a paso para nuevos colaboradores |
| `backend/.env.example` | Plantilla de configuración con todas las variables |

---

## Checklist antes de hacer push

```bash
cd backend && uv run ruff check confidence_map/           # 0 errores
cd backend && uv run mypy --strict confidence_map/        # 0 errores
cd backend && ANTHROPIC_API_KEY=test uv run pytest -q     # 42 passed, ≥80% cov
cd frontend && pnpm exec tsc --noEmit                     # sin output = ok
```

O simplemente: `make check`
