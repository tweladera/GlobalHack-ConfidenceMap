# STATUS — Confidence Map

> **Fuente de verdad del estado del proyecto.**
> Actualizar al completar cada tarea y al final de cada sesión de trabajo.

---

## Último checkpoint

```
Fecha:    2026-05-26
Sesión:   5
Estado:   Fases 1-5 completas. pnpm migrado. pyproject.toml consolidado. API key validada.
          Proyecto migrado al repo tweladera/Confidence-Map.
Tests:    42/42 ✅ | Cobertura: 91.54% ✅ | mypy: 0 errores ✅ | ruff: 0 warnings ✅ | frontend build: ✅
```

---

## Cómo usar este documento

- **Al iniciar:** leer "Próxima acción" y "Verificación rápida"
- **Al completar una tarea:** marcar `[x]` y actualizar "Último checkpoint"
- **Al interrumpir:** escribir exactamente dónde se quedó en "Próxima acción"
- **Si algo no funciona:** documentar en "Problemas conocidos"

---

## Verificación rápida del entorno

Ejecutar estos comandos para confirmar que todo está en orden:

```bash
# 1. Backend instala y tests pasan
cd backend && ANTHROPIC_API_KEY=test uv run pytest -q
# Esperado: 42 passed, coverage: 91%+

# 2. Tipado y linting
cd backend && uv run mypy --strict confidence_map/ && uv run ruff check confidence_map/
# Esperado: Success / All checks passed

# 3. Frontend compila
cd frontend && pnpm exec tsc --noEmit
# Esperado: (sin output = ok)

# 4. Backend arranca
cd backend && ANTHROPIC_API_KEY=test uv run uvicorn confidence_map.main:app &
curl http://localhost:8000/health
# Esperado: {"status":"ok","version":"0.1.0"}
kill %1
```

---

## Progreso por fases

### FASE 0 — Infraestructura base
**Estado: COMPLETA ✅**

| Tarea | Estado | Verificado |
|-------|--------|-----------|
| Estructura de proyecto (backend + frontend) | ✅ | sí |
| 6 agentes con Claude tool use | ✅ | sí |
| API FastAPI con SSE streaming | ✅ | sí |
| Frontend Next.js con React Flow | ✅ | build ok |
| Mapa de confianza con dagre layout | ✅ | build ok |
| Accesibilidad WCAG 2.1 AA base | ✅ | build ok |
| Tipado estático mypy --strict | ✅ | 0 errores |
| Linting ruff | ✅ | 0 warnings |
| Tests pytest (42 tests, ≥80%) | ✅ | 91.54% |
| README raíz | ✅ | sí |
| README backend | ✅ | sí |
| README frontend | ✅ | sí |
| QUICKSTART.md | ✅ | sí |
| PLAN.md | ✅ | sí |
| uv migración (desde pip/venv) | ✅ | sí |
| pyproject.toml (dependency-groups, sin duplicados) | ✅ | sí |
| pnpm migrado (sin npm) | ✅ | sí |

---

### FASE 1 — Estabilidad demo
**Estado: COMPLETA ✅**

| Tarea | Estado | Verificado |
|-------|--------|-----------|
| `DEMO_MODE=true`: mock results para spec de pagos | ✅ | sí |
| Mock con delay simulado (SSE funciona igual) | ✅ | sí |
| Variable `MODEL` documentada en .env | ✅ | sí |
| Timeout visible en frontend (>90s) | ✅ | sí |
| Error de agente no bloquea los demás | ✅ | sí |
| Test end-to-end con mock mode | ✅ | sí |

---

### FASE 2 — Visual del mapa
**Estado: COMPLETA ✅**

| Tarea | Estado | Verificado |
|-------|--------|-----------|
| Nodo agente: glow animado en running | ✅ | sí |
| Edges con color accent durante análisis | ✅ | sí |
| Nodo finding: barra de confidence score | ✅ | sí |
| Panel de detalle: sección "Qué hacer" | ✅ | sí |
| `recommended_action` en todos los findings mock | ✅ | sí |

---

### FASE 3 — Narrativa de la demo
**Estado: COMPLETA ✅**

| Tarea | Estado | Verificado |
|-------|--------|-----------|
| Spec Auth MFA (segundo preset) | ✅ | sí |
| Selector de spec: Pagos / Auth | ✅ | sí |
| Resumen ejecutivo al finalizar | ✅ | sí |
| Tabla de decisiones (filtrable por nivel) | ✅ | sí |
| Botón "Copiar resumen" (markdown) | ✅ | sí |

---

### FASE 4 — Accesibilidad avanzada
**Estado: COMPLETA ✅**

| Tarea | Estado | Verificado |
|-------|--------|-----------|
| Modo de solo texto (toggle mapa/tabla/texto) | ✅ | sí |
| Atajos de teclado Alt+1/2/3 | ✅ | sí |
| Narración progresiva por agente (aria-live assertive) | ✅ | sí |

---

### FASE 5 — Pulido presentación
**Estado: COMPLETA ✅**

| Tarea | Estado | Verificado |
|-------|--------|-----------|
| .gitignore completo | ✅ | sí |
| Migración a tweladera/Confidence-Map | ✅ | sí |
| URL compartible con ?spec=pagos\|auth | ✅ | sí |
| pnpm en lugar de npm | ✅ | sí |
| pyproject.toml sin dependencias duplicadas | ✅ | sí |
| API key validada (necesita recarga de créditos) | ✅ | sí |

---

### FASE 6 — Post-hackathon
**Estado: BACKLOG 📋** (no relevante para el MVP)

---

## Problemas conocidos

| # | Problema | Impacto | Estado |
|---|---------|---------|--------|
| 1 | API key sin créditos — cuenta necesita recarga | Medio | Usar DEMO_MODE=true mientras tanto |

---

## Decisiones técnicas registradas

| Fecha | Decisión | Razón |
|-------|---------|-------|
| 2026-05-20 | uv en lugar de pip/venv | Constitución: gestor único oficial |
| 2026-05-20 | asyncio.gather en lugar de LangGraph puro | Confiabilidad demo > sofisticación |
| 2026-05-20 | Tool use de Claude para output estructurado | Evita parseo frágil de texto libre |
| 2026-05-20 | dagre layout para React Flow | Auto-posicionamiento, sin coordenadas manuales |
| 2026-05-22 | DEMO_MODE planificado | Limitar consumo API key en desarrollo |
| 2026-05-26 | pnpm en lugar de npm | Seguridad: vulnerabilidades recientes en npm |
| 2026-05-26 | [dependency-groups] en lugar de [project.optional-dependencies] | PEP 735, uv estándar moderno |

---

## Contexto de sesiones anteriores

### Sesión 5 — 2026-05-26
- Migración npm → pnpm (package.json + pnpm-lock.yaml)
- pyproject.toml: consolidado en [dependency-groups], eliminados duplicados
- .env.example: API key real removida → placeholder
- API key probada: válida, cuenta sin créditos (usar DEMO_MODE=true)
- Documentación actualizada: QUICKSTART, README, backend/README, frontend/README
- STATUS.md y PLAN.md actualizados al estado real
- Repo tweladera/Confidence-Map: commit inicial limpio

### Sesión 4 — 2026-05-25
- DEMO_MODE=true implementado end-to-end
- _stream_mock_analysis() emite los mismos eventos SSE que el modo real
- 42/42 tests, 91.54% cobertura
- Fases 2, 3, 4, 5 implementadas en frontend

### Sesión 3 — 2026-05-25
- Spec NovaBank reemplaza spec genérico
- Score de confianza global en header del dashboard
- 2 nuevos tests del orquestador

### Sesión 2 — 2026-05-22
- Migración a uv + Python 3.12 + estructura de paquete canónica
- mypy strict: 0 errores; ruff: 0 warnings; pytest: 29/29

### Sesión 1 — 2026-05-20
- MVP completo: 6 agentes, API SSE, React Flow, accesibilidad base

---

## Próxima acción

```
TAREA:    Push a tweladera/Confidence-Map con commit limpio
OBJETIVO: Primer commit público con todas las fases implementadas
NOTA:     Recargar créditos en console.anthropic.com para habilitar modo real
```

---

## Checklist de demo (pre-presentación)

- [ ] Backend responde `/health`
- [ ] Frontend carga sin errores de consola
- [ ] Preset "NovaBank · Pagos" carga correctamente
- [ ] Análisis inicia y agentes se activan en secuencia
- [ ] El mapa construye en tiempo real con animaciones
- [ ] Al hacer clic en un nodo se ve el detalle con "Qué hacer"
- [ ] Tabla de decisiones muestra y filtra findings
- [ ] Panel de accesibilidad (texto) funciona
- [ ] Alt+1/2/3 cambia vistas
- [ ] Demo completa < 3 minutos
- [ ] Sin errores visibles en UI
