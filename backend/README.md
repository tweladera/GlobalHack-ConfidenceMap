# Confidence Map — Backend

API REST con streaming SSE que orquesta seis agentes de IA especializados para analizar especificaciones de software.

---

## Tecnologías

| Herramienta | Versión | Rol |
|-------------|---------|-----|
| Python | 3.12+ | Lenguaje |
| uv | 0.11+ | Gestión de paquetes |
| FastAPI | 0.136+ | Framework HTTP |
| Anthropic SDK | 0.103+ | Integración Claude |
| Pydantic v2 | 2.13+ | Modelos y validación |
| mypy | 2.1+ | Tipado estático strict |
| ruff | 0.15+ | Linter y formatter |
| pytest | 9.0+ | Tests (cobertura ≥80%) |

---

## Estructura del paquete

```
backend/
├── confidence_map/
│   ├── agents/
│   │   ├── base.py                    # Motor: Claude tool-use estructurado
│   │   ├── spec_analyst.py            # Agente 1: ambigüedad y gaps
│   │   ├── arch_validator.py          # Agente 2: arquitectura y drift
│   │   ├── risk_intelligence.py       # Agente 3: seguridad y delivery
│   │   ├── business_impact.py         # Agente 4: costo y negocio
│   │   ├── accessibility_advocate.py  # Agente 5: WCAG 2.1 AA
│   │   └── delivery_historian.py      # Agente 6: patrones históricos
│   ├── api/
│   │   └── analysis.py                # POST /api/analyze · GET /api/analyze/{id}/stream
│   ├── core/
│   │   ├── orchestrator.py            # Fase 1 secuencial + Fase 2 paralela
│   │   └── settings.py                # Variables de entorno (pydantic-settings)
│   ├── models/
│   │   ├── findings.py                # Finding, AgentResult, ConfidenceLevel
│   │   ├── analysis.py                # AnalysisRequest, ConfidenceDistribution
│   │   └── events.py                  # SSEEvent, SSEEventType
│   └── main.py                        # create_app() + CORS
├── tests/
│   ├── unit/
│   │   ├── test_models.py             # 14 tests de modelos de dominio
│   │   └── test_base_agent.py         # 9 tests del motor de agentes
│   └── integration/
│       └── test_api.py                # 6 tests de endpoints HTTP
└── pyproject.toml                     # Toda la configuración
```

---

## Instalación

### Requisitos previos
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) instalado

### Instalar dependencias

```bash
cd backend
uv sync --extra dev
```

### Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tu ANTHROPIC_API_KEY
```

---

## Ejecución

```bash
# Desarrollo (hot reload)
uv run uvicorn confidence_map.main:app --reload

# Producción
uv run uvicorn confidence_map.main:app --host 0.0.0.0 --port 8000
```

La API queda disponible en `http://localhost:8000`.
Documentación interactiva: `http://localhost:8000/docs`

---

## API Reference

### `POST /api/analyze`
Inicia un análisis y retorna su ID.

**Request:**
```json
{
  "spec": "## Feature: Payment Notifications...",
  "architecture": "Opcional: descripción de arquitectura",
  "context": "Opcional: contexto adicional"
}
```

**Response `202`:**
```json
{ "analysis_id": "uuid-v4" }
```

---

### `GET /api/analyze/{analysis_id}/stream`
Stream de eventos SSE mientras los agentes analizan.

**Eventos emitidos:**

```jsonc
// Agente inicia
{"type": "agent_start", "agent_id": "spec_analyst", "agent_name": "Spec Analyst"}

// Agente completa
{"type": "agent_complete", "agent_id": "spec_analyst", "result": {...}}

// Análisis finalizado
{"type": "analysis_complete", "total_findings": 28, "confidence_distribution": {"green": 8, "yellow": 12, "red": 8}}
```

---

### `GET /health`
Health check.

```json
{"status": "ok", "version": "0.1.0"}
```

---

## Flujo de orquestación

```
POST /api/analyze
        │
        ▼
[Spec Analyst]          ← Fase 1: corre solo, establece contexto
        │
        ▼
┌───────────────────────────────────────┐
│           Fase 2: paralelo            │
│  [Arch]  [Risk]  [Business]           │
│  [Accessibility]  [Historian]         │
└───────────────────────────────────────┘
        │
        ▼
SSE: analysis_complete
```

---

## Variables de entorno

| Variable | Requerida | Default | Descripción |
|----------|-----------|---------|-------------|
| `ANTHROPIC_API_KEY` | **Sí** | — | API key de Anthropic |
| `MODEL` | No | `claude-sonnet-4-6` | Modelo Claude a usar |
| `FRONTEND_URL` | No | `http://localhost:3000` | Origen permitido en CORS |

Para reducir costos en desarrollo, usar `MODEL=claude-haiku-4-5-20251001`.

---

## Quality gates

```bash
# Tipado estático estricto
uv run mypy --strict confidence_map/

# Linting + formato
uv run ruff check confidence_map/
uv run ruff format confidence_map/

# Tests con cobertura
ANTHROPIC_API_KEY=test uv run pytest

# Todo junto (pre-commit)
uv run mypy --strict confidence_map/ && uv run ruff check confidence_map/ && ANTHROPIC_API_KEY=test uv run pytest
```

---

## Cómo funciona cada agente

Cada agente usa **Claude tool use** con una herramienta `report_findings` que fuerza output JSON estructurado con niveles de confianza. Esto garantiza que:

1. El output siempre es parseable (no falla por texto libre)
2. Los campos `confidence`, `confidence_score`, `evidence` y `assumptions` son siempre explícitos
3. El `summary` está optimizado para lectores de pantalla

```python
# Ejemplo de finding retornado por un agente
{
  "title": "Sin estrategia de retry para el servicio externo",
  "description": "El spec no define comportamiento cuando el proveedor de email falla",
  "confidence": "red",
  "confidence_score": 0.1,
  "evidence": "La historia US-001 no menciona manejo de errores del proveedor",
  "assumptions": [],
  "needs_validation": ["¿Cuál es la política de retry?", "¿Hay circuit breaker?"],
  "category": "risk"
}
```

---

## Agregar un nuevo agente

1. Crear `confidence_map/agents/mi_agente.py` con `AGENT_ID`, `AGENT_NAME`, `AGENT_ICON` y `async def run(...) -> AgentResult`
2. Importar en `confidence_map/agents/__init__.py`
3. Agregar al `orchestrate()` en `confidence_map/core/orchestrator.py`
4. Escribir tests en `tests/unit/`
