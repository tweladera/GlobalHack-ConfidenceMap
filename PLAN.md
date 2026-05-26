# Plan de trabajo — Confidence Map

Plan de desarrollo por fases orientado al demo de hackathon.

**Contexto:** MVP con limitaciones de API key. Priorizamos lo que hace la demo memorable.

---

## Estado actual

**Fase 0 completada.** La base técnica está lista:
- 6 agentes especializados con Claude tool use
- API FastAPI con SSE streaming
- Frontend Next.js con React Flow
- Mapa de confianza visual con dagre layout
- Accesibilidad WCAG 2.1 AA
- 29 tests, cobertura 80.34%
- mypy --strict: 0 errores
- spec-kit v0.8.12 integrado con constitución del proyecto

---

## Fase 1 — Estabilidad demo
**Prioridad: CRÍTICA**

El objetivo es que la demo funcione de manera confiable sin depender de la API key en cada prueba.

### 1.1 Modo demo con datos mock
- [ ] Crear `backend/confidence_map/core/mock_results.py` con resultados pre-generados para el spec de pagos
- [ ] Agregar variable de entorno `DEMO_MODE=true` que bypasea las llamadas a Claude
- [ ] Los mocks deben incluir findings representativos de cada agente (4-6 por agente)
- [ ] El streaming SSE debe funcionar igual que en modo real (con delays simulados)

**Por qué:** Para demos en vivo con conectividad inestable o sin créditos disponibles.

### 1.2 Selección de modelo por variable de entorno
- [x] `MODEL=claude-haiku-4-5-20251001` ya funciona (configurado en .env)
- [ ] Documentar tiempos y calidad esperada por modelo en QUICKSTART.md

### 1.3 Timeout y manejo de errores visible
- [ ] Si un agente falla, mostrar el error en el nodo del mapa (no bloquear los demás)
- [ ] Si el análisis tarda más de 90s, mostrar indicador de "tomando más de lo esperado"
- [ ] Botón "Reintentar agente" en el panel lateral

**Criterio de éxito:** La demo corre de punta a punta en menos de 2 minutos, con o sin API key.

---

## Fase 2 — Visual del mapa
**Prioridad: ALTA**

El mapa de confianza es la estrella. Debe verse profesional y narrar la historia.

### 2.1 Animación de construcción del mapa
- [ ] Los nodos de findings aparecen con animación `fadeIn` cuando llega `agent_complete`
- [ ] El nodo del agente pulsa mientras está en estado `running`
- [ ] Edges animadas (stroke-dasharray) durante el análisis, estáticas al completar

### 2.2 Colores y estados del nodo agente
- [ ] Pending: borde gris, texto apagado
- [ ] Running: borde accent, glow animado
- [ ] Completed: borde sutil, badge con conteo de findings por color
- [ ] Error: borde rojo, ícono de advertencia

### 2.3 Nodos de findings mejorados
- [ ] Truncar título a 2 líneas con ellipsis
- [ ] Mostrar barra de confidence score debajo del título
- [ ] Hover state con elevación visual

### 2.4 Panel de detalle mejorado
- [ ] Sección "Qué hacer" con las acciones de `needs_validation` como checklist
- [ ] Enlace "Ver agente" que hace scroll al nodo del agente en el mapa
- [ ] Exportar finding como texto (para pegar en Jira/ticket)

**Criterio de éxito:** Un observador sin contexto entiende el mapa en menos de 30 segundos.

---

## Fase 3 — Narrativa de la demo
**Prioridad: ALTA**

La demo necesita una historia. No es solo técnica, es una propuesta de valor.

### 3.1 Spec de demo mejorado
- [ ] El spec de pagos actual es bueno. Agregar más ambigüedades deliberadas para que los agentes encuentren más hallazgos
- [ ] Opcional: spec alternativo de un sistema de autenticación (más hallazgos de seguridad)
- [ ] Botón de selección de spec: "Pagos" / "Auth" / "Personalizado"

### 3.2 Resumen ejecutivo al finalizar
- [ ] Tarjeta de "Resumen ejecutivo" cuando el análisis completa:
  - Total de findings por nivel
  - Top 3 hallazgos críticos (rojo)
  - Agente con más hallazgos
  - Tiempo de análisis
- [ ] Botón "Copiar resumen" (para pegar en Slack/presentación)

### 3.3 Tabla de decisiones (el concepto de spec-kit)
- [ ] Tabla debajo del mapa con columnas: Decisión | Nivel | Razón | Agente
- [ ] Filtrable por nivel de confianza
- [ ] Exportable como Markdown

**Criterio de éxito:** Se puede hacer una demo de 3 minutos que cuente una historia completa.

---

## Fase 4 — Accesibilidad avanzada
**Prioridad: MEDIA**

Ya tenemos lo básico. Esta fase lleva la accesibilidad al nivel que sea memorable en el hackathon.

### 4.1 Modo de solo texto
- [ ] Botón "Ver como texto" que oculta el mapa y muestra solo la tabla de findings
- [ ] Navegación por teclado completa en la tabla
- [ ] Atajos: `Alt+1` (mapa), `Alt+2` (tabla), `Alt+3` (resumen)

### 4.2 Narración progresiva
- [ ] Cuando completa cada agente, `aria-live` narra: "Spec Analyst completó. Encontró 2 problemas críticos."
- [ ] Al seleccionar un finding, `aria-live` narra el título y nivel de confianza

### 4.3 Alto contraste
- [ ] Toggle de alto contraste (prefers-contrast: more)
- [ ] Modo daltónico: usar íconos además de colores para los niveles

**Criterio de éxito:** Un evaluador con lector de pantalla puede seguir el análisis completo.

---

## Fase 5 — Pulido para presentación
**Prioridad: MEDIA** (si hay tiempo)

### 5.1 Git y repositorio
- [ ] `.gitignore` completo (ya parcialmente configurado por spec-kit)
- [ ] Git inicializado con primer commit limpio
- [ ] README con badges de cobertura y calidad

### 5.2 Pantalla de carga inicial
- [ ] Splash screen con logo mientras carga el mapa
- [ ] Mensaje de estado: "Iniciando 6 agentes especializados..."

### 5.3 Compartir análisis
- [ ] URL con `?spec=<encoded>` para compartir un análisis específico
- [ ] La página de análisis puede cargar desde URL params (no solo sessionStorage)

---

## Fase 6 — Post-hackathon (futuro)
**Prioridad: BAJA para el MVP**

Funcionalidades para una versión real del producto:

- [ ] Persistencia con PostgreSQL/Supabase (análisis históricos)
- [ ] Autenticación de usuarios
- [ ] Integración con Jira: crear tickets desde findings
- [ ] Integración con GitHub: analizar PRDs desde issues
- [ ] Historial de análisis por proyecto
- [ ] LangGraph para orquestación formal (actualmente asyncio)
- [ ] Harness: quality gates automáticos basados en findings
- [ ] API pública para integrar en CI/CD

---

## Priorización para el hackathon

Si el tiempo es limitado, este es el orden de impacto:

```
1. Fase 1.1 (mock mode)       → Demo confiable sin API key
2. Fase 3.3 (tabla decisiones) → Concepto central visible
3. Fase 2.1 (animaciones)      → Impacto visual inmediato
4. Fase 3.2 (resumen ejecutivo)→ Cierre memorable de la demo
5. Fase 2.3 (findings mejorado)→ Detalle profesional
```

---

## Estimación de consumo de API key

| Escenario | Modelo | Costo estimado por análisis |
|-----------|--------|----------------------------|
| Desarrollo / prueba | Haiku | ~$0.003 |
| Demo con calidad | Sonnet | ~$0.05–$0.10 |
| 10 demos en vivo | Sonnet | ~$0.50–$1.00 |
| Modo mock | — | $0.00 |

**Recomendación:** Generar los mocks una vez con Sonnet, luego usar DEMO_MODE=true para todas las pruebas.

---

## Checklist de la demo

Antes de presentar, verificar:

- [ ] Backend corre en `localhost:8000` y responde `/health`
- [ ] Frontend corre en `localhost:3000` y carga sin errores
- [ ] `DEMO_MODE=true` configurado (o API key con créditos disponibles)
- [ ] El spec de demo carga correctamente con "Load demo"
- [ ] El análisis completa sin errores
- [ ] El mapa muestra nodos de los 6 agentes
- [ ] Al hacer clic en un nodo se muestra el detalle
- [ ] El panel de accesibilidad (texto) funciona
- [ ] La demo dura menos de 3 minutos de punta a punta
