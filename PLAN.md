# Plan de trabajo — Confidence Map

Plan de desarrollo por fases orientado al demo de hackathon.

**Contexto:** MVP con limitaciones de API key. Priorizamos lo que hace la demo memorable.

---

## Estado actual

**Fases 0–5 completadas.** Demo listo para presentar.
- 6 agentes especializados con Claude tool use
- API FastAPI con SSE streaming
- Frontend Next.js con React Flow
- Mapa de confianza visual con animaciones en tiempo real
- Tabla de decisiones filtrable
- Modo texto accesible (WCAG 2.1 AA)
- Atajos de teclado Alt+1/2/3
- Narración progresiva para lectores de pantalla
- URL compartible `?spec=pagos|auth`
- DEMO_MODE=true: demo sin API key, $0 costo
- 42 tests, cobertura 91.54%
- mypy --strict: 0 errores | ruff: 0 warnings
- pnpm como gestor de paquetes frontend

---

## Fase 1 — Estabilidad demo
**Estado: COMPLETA ✅**

### 1.1 Modo demo con datos mock
- [x] `backend/confidence_map/core/mock_results.py` con resultados pre-generados
- [x] Variable `DEMO_MODE=true` que bypasea Claude
- [x] Findings representativos de cada agente (4-6 por agente)
- [x] SSE streaming funciona igual que en modo real (con delays simulados)

### 1.2 Selección de modelo y timeout
- [x] `MODEL=claude-haiku-4-5-20251001` configurable en .env
- [x] Timeout visible en frontend (>90s): banner amarillo
- [x] Error de agente no bloquea los demás

**Criterio de éxito:** ✅ La demo corre de punta a punta en ~5s con DEMO_MODE.

---

## Fase 2 — Visual del mapa
**Estado: COMPLETA ✅**

### 2.1 Animaciones y estados
- [x] Nodo agente: glow animado (agentGlow keyframe) en estado running
- [x] Edges con color accent (#6366f1) durante análisis
- [x] Nodo finding: barra de confidence_score

### 2.2 Panel de detalle
- [x] Sección "Qué hacer" con `recommended_action` de cada finding
- [x] `recommended_action` en todos los 20 findings del mock (en español)

**Criterio de éxito:** ✅ Un observador sin contexto entiende el mapa en menos de 30 segundos.

---

## Fase 3 — Narrativa de la demo
**Estado: COMPLETA ✅**

### 3.1 Specs de demo
- [x] Spec de pagos NovaBank (con ambigüedades deliberadas)
- [x] Spec Auth MFA NovaBank (segundo preset con hallazgos de seguridad)
- [x] Selector de spec: pills "NovaBank · Pagos" / "NovaBank · Auth MFA"

### 3.2 Resumen ejecutivo
- [x] Tarjeta de resumen ejecutivo cuando el análisis completa
- [x] Score global, breakdown por nivel, top 3 críticos
- [x] Botón "Copiar resumen" (markdown para pegar en Slack)

### 3.3 Tabla de decisiones
- [x] Tabla filtrable por nivel: All / Critical / Inferred / Confirmed
- [x] Columnas: #, Finding, Agent, Level, Score
- [x] Navegación por teclado completa (tabIndex, Enter)

**Criterio de éxito:** ✅ Demo de 3 minutos que cuenta una historia completa.

---

## Fase 4 — Accesibilidad avanzada
**Estado: COMPLETA ✅**

### 4.1 Modo de solo texto
- [x] Toggle mapa/tabla/texto en header
- [x] Atajos: `Alt+1` (mapa), `Alt+2` (tabla), `Alt+3` (texto)
- [x] Vista texto: todos los findings organizados por agente

### 4.2 Narración progresiva
- [x] `aria-live="assertive"` narra: "Spec Analyst completó. Encontró 2 problemas críticos."
- [x] Patrón clear→set para que anuncios repetidos funcionen

**Criterio de éxito:** ✅ Un evaluador con lector de pantalla puede seguir el análisis completo.

---

## Fase 5 — Pulido para presentación
**Estado: COMPLETA ✅**

### 5.1 Git y repositorio
- [x] `.gitignore` completo
- [x] Migración a tweladera/Confidence-Map
- [x] Primer commit con todas las fases

### 5.2 Compartir análisis
- [x] URL con `?spec=pagos|auth` para presets
- [x] Auto-carga desde URL params al montar

### 5.3 Calidad
- [x] pnpm en lugar de npm (seguridad)
- [x] pyproject.toml sin dependencias duplicadas
- [x] Documentación completa y actualizada

---

## Fase 6 — Post-hackathon (futuro)
**Estado: BACKLOG 📋** (no relevante para el MVP)

Funcionalidades para una versión real del producto:

- [ ] Persistencia con PostgreSQL/Supabase (análisis históricos)
- [ ] Autenticación de usuarios
- [ ] Integración con Jira: crear tickets desde findings
- [ ] Integración con GitHub: analizar PRDs desde issues
- [ ] Historial de análisis por proyecto
- [ ] LangGraph para orquestación formal (actualmente asyncio)
- [ ] API pública para integrar en CI/CD

---

## Checklist de la demo

Antes de presentar, verificar:

- [ ] Backend corre en `localhost:8000` y responde `/health`
- [ ] Frontend corre en `localhost:3000` y carga sin errores
- [ ] `DEMO_MODE=true` configurado en `backend/.env`
- [ ] El preset "NovaBank · Pagos" carga correctamente
- [ ] El análisis completa sin errores (~5s en modo demo)
- [ ] El mapa muestra nodos de los 6 agentes con animaciones
- [ ] Al hacer clic en un nodo se muestra el detalle con "Qué hacer"
- [ ] La tabla de decisiones filtra correctamente
- [ ] El modo texto (Alt+3) muestra todos los findings
- [ ] El botón "Copiar resumen" funciona
- [ ] La demo dura menos de 3 minutos de punta a punta
