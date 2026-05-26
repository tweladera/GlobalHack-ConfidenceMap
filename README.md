# Confidence Map

**Plataforma de inteligencia para arquitectura y delivery de software basada en IA multiagente.**

Confidence Map analiza especificaciones de software con seis agentes especializados que trabajan en paralelo, generando un mapa visual de decisiones, riesgos e incertidumbres con niveles de confianza explícitos.

---

## El problema que resuelve

Los equipos de ingeniería:
- Trabajan con especificaciones ambiguas sin saberlo
- Toman decisiones arquitectónicas sin trazabilidad
- Descubren riesgos demasiado tarde en el ciclo de entrega
- Dependen de herramientas de IA que responden sin explicar su razonamiento

Confidence Map hace el razonamiento **visible** y **accesible** para todos.

---

## Diferenciador

> No es un chatbot. No es un copiloto. No es un generador de código.
> Es un **sistema de razonamiento visible** para ingeniería y delivery.

Cada respuesta incluye:
- Qué sabe con certeza
- Qué infiere razonablemente
- Qué asume
- Qué contradicciones encontró
- Qué necesita validación

---

## Los seis agentes

| Agente | Función |
|--------|---------|
| **Spec Analyst** | Detecta ambigüedad, contradicciones y requisitos incompletos |
| **Architecture Validator** | Valida arquitectura, coupling peligroso y drift |
| **Risk Intelligence** | Seguridad, riesgos de delivery y observabilidad |
| **Business Impact** | Costo cloud, velocidad de delivery y riesgo regulatorio |
| **Accessibility Advocate** | WCAG 2.1 AA, lectores de pantalla, navegación por teclado |
| **Delivery Historian** | Patrones históricos y post-mortems de la industria |

---

## Mapa de confianza

El mapa es la estrella visual de la plataforma.

| Nivel | Color | Significado |
|-------|-------|-------------|
| **Verde** | 🟢 | Explícitamente definido en la especificación |
| **Amarillo** | 🟡 | Inferido razonablemente del contexto |
| **Rojo** | 🔴 | Alta incertidumbre, contradicción o faltante |

---

## Arquitectura técnica

```
┌─────────────────────────────────┐
│         Frontend (Next.js)      │
│   React Flow · Tailwind CSS     │
│   Accessibility first           │
└──────────────┬──────────────────┘
               │ SSE streaming
┌──────────────▼──────────────────┐
│         Backend (FastAPI)       │
│   Python 3.12 · uv · mypy      │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│    Orquestador (asyncio)        │
│   Spec Analyst (fase 1)         │
│   5 agentes en paralelo         │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│   Anthropic API (Claude)        │
│   claude-sonnet-4-6             │
│   Tool use estructurado         │
└─────────────────────────────────┘
```

---

## Estructura del repositorio

```
confidence-map/
├── backend/              # API FastAPI + 6 agentes
│   ├── confidence_map/   # Paquete principal Python
│   ├── tests/            # pytest · ≥80% cobertura
│   └── pyproject.toml    # uv · mypy · ruff · pytest
├── frontend/             # Next.js 15 App Router
│   ├── app/              # Páginas
│   └── components/       # Componentes React
├── .specify/             # spec-kit: constitución y templates
│   └── memory/
│       └── constitution.md
├── QUICKSTART.md         # Guía de inicio rápido
└── PLAN.md               # Plan de trabajo por fases
```

---

## Inicio rápido

Consulta [QUICKSTART.md](./QUICKSTART.md) para instrucciones completas.

```bash
# Backend
cd backend && uv run uvicorn confidence_map.main:app --reload

# Frontend
cd frontend && npm run dev
```

---

## Estado del proyecto

**MVP para hackathon** — Fase 0 completada.

Ver [PLAN.md](./PLAN.md) para el roadmap por fases.

---

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.12, FastAPI, uv |
| IA | Anthropic SDK, Claude Sonnet 4.6 |
| Tipado | mypy --strict, Pydantic v2 |
| Tests | pytest, pytest-asyncio, cobertura ≥80% |
| Frontend | Next.js 15, TypeScript strict |
| Visualización | React Flow, dagre layout |
| Estilos | Tailwind CSS |
| Especificación | spec-kit v0.8.12 |

---

## Principios de desarrollo

Este proyecto sigue una [constitución](./.specify/memory/constitution.md) que establece:
- Tipado estático estricto (Python 3.12+, TypeScript strict)
- Tests obligatorios con cobertura mínima del 80%
- Gestión de dependencias exclusivamente con `uv`
- Accesibilidad WCAG 2.1 AA como requisito de producción
- Código limpio y mínimo (YAGNI)
