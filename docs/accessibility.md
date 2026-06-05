# Accessibility — Confidence Map

Confidence Map fue construido con accesibilidad como requisito de primera clase, no como añadido.
Esta guía documenta qué existe, dónde vive, y cómo funciona.

---

## 1. Navegación por teclado

### Atajos de vista (Alt + número)

| Atajo | Acción |
|-------|--------|
| `Alt+1` | Vista Mapa (React Flow — ConfidenceMap) |
| `Alt+2` | Vista Tabla (DecisionTable — filtrable) |
| `Alt+3` | Modo Texto (documento accesible completo) |
| `Alt+4` | Risk Heat Map (matriz 5×5 probabilidad × impacto) |

**Implementación:** `frontend/app/analysis/page.tsx:82–93`

```ts
window.addEventListener("keydown", (e) => {
  if (!e.altKey) return;
  if (e.key === "1") { /* mapa */   }
  if (e.key === "2") { /* tabla */  }
  if (e.key === "3") { /* texto */  }
  if (e.key === "4") { /* heatmap */}
});
```

Los botones del header tienen `aria-pressed` y `title="Alt+N"` para que el lector de pantalla
y el tooltip del mouse comuniquen el atajo disponible.

Todos los controles interactivos (botones, inputs, links) son alcanzables con `Tab` mediante
HTML semántico estándar — sin `tabIndex` manual necesario.

---

## 2. Soporte para lectores de pantalla

Existen dos mecanismos independientes que funcionan en paralelo:

### 2a. `announce()` — narración en tiempo real

**Archivo:** `frontend/app/analysis/page.tsx:62–71`

Función que actualiza una región `aria-live="assertive"` + `sr-only` con cada evento del
análisis:

| Evento SSE | Anuncio |
|-----------|---------|
| `agent_start` | `"${agentName} has started analysis."` |
| `agent_complete` | `"${agentName} has completed analysis. Found N findings."` |
| `consolidation_start` | `"Cross-agent audit in progress."` |
| `consolidation_complete` | `"Cross-agent audit complete."` |
| `analysis_complete` | `"Analysis complete. N findings found."` |

**Técnica:** clear → re-set con delay de 60ms para forzar reanuncio aunque el texto anterior
sea similar. Esto garantiza que el lector de pantalla dispare el evento incluso para mensajes
repetidos.

### 2b. `AccessibleSummary` — narración pasiva continua

**Archivo:** `frontend/components/AccessibleSummary.tsx`

Componente con dos partes:

**Región invisible (siempre activa):**
```tsx
<div aria-live="polite" aria-atomic="false" className="sr-only" role="status">
  {statusText}  {/* actualiza automáticamente al completar cada agente */}
</div>
```

**Panel visible (toggle manual):**
- Botón flotante bottom-left: `aria-expanded`, `aria-controls`, `aria-label`
- Panel con `role="region"`, `aria-label="Accessible text summary of confidence map"`
- Conteos por nivel con `role="group"` y `aria-label` individuales
- Top 3 hallazgos críticos en `<ul aria-label="High uncertainty findings">`
- Resumen narrativo por agente en lenguaje natural

### 2c. ARIA en toda la interfaz

Elementos clave instrumentados:

| Elemento | Atributos ARIA |
|----------|---------------|
| Barra de progreso | `role="progressbar"` · `aria-valuenow/min/max` · `aria-label` |
| Toggle de vistas | `role="group"` · `aria-pressed` · `aria-label` con atajos |
| Lista de hallazgos | `role="list"` · `aria-label` con conteo · `aria-current` en seleccionado |
| Paneles colapsables | `aria-expanded` · `aria-controls` |
| Estados de carga | `aria-busy="true"` · `role="status"` · `aria-live="polite"` |
| Errores | `role="alert"` · `aria-live="assertive"` |
| Íconos decorativos | `aria-hidden="true"` en todos |
| Score global | `aria-label="Global confidence: 78%"` |

---

## 3. Modo texto (Alt+3)

Vista completa de todos los hallazgos como documento de texto estructurado.

**Activación:** `Alt+3` o click en el toggle "Text" del header.

**Implementación:** `frontend/app/analysis/page.tsx:494–600`

```tsx
<div role="document" aria-label="Text view — all findings">
  {/* heading por agente → lista de findings → botón "ver detalle" con aria-label */}
</div>
```

Características:
- `role="document"` — declara la región como documento navegable
- Headings `<h2>` / `<h3>` para estructura semántica
- Cada hallazgo con nivel de confianza en texto (`[RED]`, `[YELLOW]`, `[GREEN]`)
- Botón "Ver detalle" con `aria-label={f.title}` — unívoco para el lector de pantalla
- Botón "Copy executive summary" con `aria-label` explícito

---

## 4. Agente de accesibilidad — Accessibility Advocate

Además de la accesibilidad de la plataforma misma, existe el agente **Accessibility Advocate**
que evalúa el **producto analizado** contra WCAG 2.1 AA.

**Archivo:** `backend/confidence_map/agents/accessibility_advocate.py`

Detecta en las especificaciones:
- Dependencia exclusiva de señales visuales (sin alternativa auditiva o textual)
- Falta de soporte para lectores de pantalla en flujos críticos
- Navegación sin soporte de teclado
- Contraste insuficiente declarado en la spec
- Barreras de idioma o complejidad cognitiva

---

## 5. Limitaciones conocidas

| Limitación | Contexto |
|-----------|---------|
| React Flow canvas no es navegable nodo-a-nodo con teclado | Límite de la librería, no del proyecto. El Modo Texto (Alt+3) cubre este caso. |
| AccessibleSummary (botón ◎) solapa visualmente con el sidebar derecho en pantallas pequeñas | Issue cosmético, no funcional. |

---

## 6. Archivos clave

| Archivo | Qué implementa |
|---------|---------------|
| `frontend/app/analysis/page.tsx` | Atajos Alt+1/2/3/4 · announce() · aria en header y vistas |
| `frontend/components/AccessibleSummary.tsx` | Narración pasiva · panel de resumen accesible |
| `frontend/components/ConfidenceMap.tsx` | role/aria-label en nodos del mapa visual |
| `frontend/components/DecisionTable.tsx` | Tabla con semántica HTML correcta |
| `backend/confidence_map/agents/accessibility_advocate.py` | Agente evaluador WCAG 2.1 AA |
