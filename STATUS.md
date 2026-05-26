# STATUS — Confidence Map

> **Fuente de verdad del estado del proyecto.**
> Actualizar al completar cada tarea y al final de cada sesión de trabajo.

---

## Último checkpoint

```
Fecha:    2026-05-25
Sesión:   4
Estado:   DEMO_MODE implementado. Backend corre sin API key. 42 tests, 91.52% cobertura.
Próxima acción: Fase 1.2 — Timeout visible en frontend (>90s) + Fase 2 Visual del mapa
Tests:    42/42 ✅ | Cobertura: 91.52% ✅ | mypy: 0 errores ✅ | ruff: 0 warnings ✅ | frontend build: ✅
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
# Esperado: 29 passed, coverage: 80%+

# 2. Tipado y linting
cd backend && uv run mypy --strict confidence_map/ && uv run ruff check confidence_map/
# Esperado: Success / All checks passed

# 3. Frontend compila
cd frontend && npx tsc --noEmit
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
| Tests pytest (29 tests, ≥80%) | ✅ | 80.34% |
| spec-kit v0.8.12 instalado | ✅ | sí |
| Constitución del proyecto | ✅ | sí |
| README raíz | ✅ | sí |
| README backend | ✅ | sí |
| README frontend | ✅ | sí |
| QUICKSTART.md | ✅ | sí |
| PLAN.md | ✅ | sí |
| uv migración (desde pip/venv) | ✅ | sí |
| pyproject.toml (reemplaza requirements.txt) | ✅ | sí |

**Lo que NO se ha verificado en Fase 0:**
- [ ] Frontend corriendo con backend real (solo build compilado)
- [ ] Análisis end-to-end con ANTHROPIC_API_KEY real
- [ ] React Flow renderizando el mapa en el browser

---

### FASE 1 — Estabilidad demo
**Estado: NO INICIADA ⬜**

| Tarea | Estado | Verificado |
|-------|--------|-----------|
| `DEMO_MODE=true`: mock results para spec de pagos | ✅ | sí |
| Mock con delay simulado (SSE funciona igual) | ✅ | sí |
| Variable `MODEL` documentada en .env | ✅ | sí |
| Timeout visible en frontend (>90s) | ⬜ | — |
| Error de agente no bloquea los demás | ⬜ | — |
| Test end-to-end con mock mode | ✅ | sí |

---

### FASE 2 — Visual del mapa
**Estado: NO INICIADA ⬜**

| Tarea | Estado | Verificado |
|-------|--------|-----------|
| Animación fadeIn en nodos de findings | ⬜ | — |
| Nodo agente: glow animado en running | ⬜ | — |
| Edges animadas → estáticas al completar | ⬜ | — |
| Nodo finding: barra de confidence score | ⬜ | — |
| Panel de detalle: sección "Qué hacer" | ⬜ | — |

---

### FASE 3 — Narrativa de la demo
**Estado: NO INICIADA ⬜**

| Tarea | Estado | Verificado |
|-------|--------|-----------|
| Spec mejorado con más ambigüedades | ⬜ | — |
| Selector de spec (Pagos / Auth / Custom) | ⬜ | — |
| Resumen ejecutivo al finalizar | ⬜ | — |
| Tabla de decisiones (filtrable por nivel) | ⬜ | — |
| Botón "Copiar resumen" | ⬜ | — |

---

### FASE 4 — Accesibilidad avanzada
**Estado: NO INICIADA ⬜**

| Tarea | Estado | Verificado |
|-------|--------|-----------|
| Modo de solo texto (toggle mapa/tabla) | ⬜ | — |
| Atajos de teclado Alt+1/2/3 | ⬜ | — |
| Narración progresiva por agente | ⬜ | — |

---

### FASE 5 — Pulido presentación
**Estado: NO INICIADA ⬜**

| Tarea | Estado | Verificado |
|-------|--------|-----------|
| .gitignore completo | ⬜ | — |
| Git inicializado con primer commit | ⬜ | — |
| URL compartible con ?spec= | ⬜ | — |

---

### FASE 6 — Post-hackathon
**Estado: BACKLOG 📋** (no relevante para el MVP)

---

## Problemas conocidos

| # | Problema | Impacto | Estado |
|---|---------|---------|--------|
| 1 | Frontend no verificado end-to-end en browser | Alto | Pendiente verificar en Fase 1 |
| 2 | Sin API key real no se puede probar el flujo completo | Alto | Fase 1.1 (mock mode) lo resuelve |
| 3 | ~~`requirements.txt` antiguo en backend/ (obsoleto)~~ | Bajo | ✅ Eliminado 2026-05-22 |
| 4 | ~~`backend/models.py`, `backend/main.py`, `backend/agents/` raíz (obsoletos)~~ | Medio | ✅ Eliminado 2026-05-22 |

---

## Archivos obsoletos a eliminar

Estos archivos fueron reemplazados por la estructura del paquete `confidence_map/` pero pueden seguir existiendo:

```bash
# Verificar si existen y eliminar
ls backend/models.py 2>/dev/null && echo "OBSOLETO: backend/models.py"
ls backend/main.py 2>/dev/null && echo "OBSOLETO: backend/main.py"
ls backend/requirements.txt 2>/dev/null && echo "OBSOLETO: backend/requirements.txt"
ls backend/agents/ 2>/dev/null && echo "OBSOLETO: backend/agents/ (raíz)"
```

---

## Decisiones técnicas registradas

| Fecha | Decisión | Razón |
|-------|---------|-------|
| 2026-05-20 | uv en lugar de pip/venv | Constitución: gestor único oficial |
| 2026-05-20 | asyncio.gather en lugar de LangGraph puro | Confiabilidad demo > sofisticación |
| 2026-05-20 | Tool use de Claude para output estructurado | Evita parseo frágil de texto libre |
| 2026-05-20 | dagre layout para React Flow | Auto-posicionamiento, no requiere coordenadas manuales |
| 2026-05-22 | DEMO_MODE planificado | Limitar consumo API key en desarrollo |

---

## Contexto de sesiones anteriores

### Sesión 1 — 2026-05-20
- Construido MVP completo (backend + frontend)
- 6 agentes, API SSE, React Flow, accesibilidad base

### Sesión 4 — 2026-05-25
- DEMO_MODE=true implementado end-to-end (settings.py + mock_results.py + orchestrator.py)
- _stream_mock_analysis() emite los mismos eventos SSE que el modo real, con delays simulados
- 11 nuevos tests (test_mock_results.py): 42/42 total, 91.52% cobertura
- mypy: 0 errores | ruff: 0 warnings
- Backend puede iniciarse con solo DEMO_MODE=true, sin ANTHROPIC_API_KEY

### Sesión 3 — 2026-05-25
- Spec NovaBank reemplaza spec genérico (personajes + contexto del PDF alineados)
- Score de confianza global agregado al backend (promedio de confidence_score de todos los findings)
- Score visible en header del dashboard con color adaptativo (verde/amarillo/rojo)
- 2 nuevos tests unitarios para el orquestador (test_orchestrator.py)
- Cobertura subió de 80.34% → 90.97%

### Sesión 2 — 2026-05-22
- Migración a uv + Python 3.12 + estructura de paquete canónica
- spec-kit instalado y constitución creada
- mypy strict: 0 errores; ruff: 0 warnings; pytest: 29/29
- README raíz, backend, frontend, QUICKSTART, PLAN generados
- STATUS.md creado (este documento)

---

## Próxima acción

```
TAREA:    Fase 1.2 — Timeout visible en frontend (>90s)
ARCHIVO:  frontend/app/analysis/page.tsx (agregar indicador de timeout)
OBJETIVO: Si el análisis demora >90s, mostrar mensaje visible al usuario
          (aplica en modo real — mock mode siempre completa en ~5s)
TAREA_2:  Fase 2 — Visual del mapa (animaciones, glow en nodos, barra de score)
```

---

## Checklist de demo (pre-presentación)

- [ ] Backend responde `/health`
- [ ] Frontend carga sin errores de consola
- [ ] "Load demo" carga el spec correctamente
- [ ] Análisis inicia y agentes se activan en secuencia
- [ ] El mapa construye en tiempo real
- [ ] Al hacer clic en un nodo se ve el detalle
- [ ] Panel de accesibilidad (texto) funciona
- [ ] Demo completa < 3 minutos
- [ ] Sin errores visibles en UI
