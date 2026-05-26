# Confidence Map — Frontend

Interfaz web que visualiza el análisis multiagente en tiempo real mediante un mapa de confianza interactivo construido con React Flow.

---

## Tecnologías

| Herramienta | Versión | Rol |
|-------------|---------|-----|
| Next.js | 15 (App Router) | Framework React |
| TypeScript | 5 strict | Tipado estático |
| React Flow | 11 | Visualización del mapa |
| dagre | 1.1 | Layout automático del grafo |
| Tailwind CSS | 3.4 | Estilos utilitarios |
| Lucide React | 0.468 | Iconografía |

---

## Estructura

```
frontend/
├── app/
│   ├── layout.tsx          # Layout global + skip link de accesibilidad
│   ├── page.tsx            # Página de inicio: input de especificación
│   ├── globals.css         # Estilos base + overrides React Flow
│   └── analysis/
│       └── page.tsx        # Dashboard de análisis con streaming SSE
├── components/
│   ├── ConfidenceMap.tsx   # React Flow: mapa visual central
│   ├── AgentStatusCard.tsx # Panel lateral de estado de agentes
│   ├── FindingDetail.tsx   # Panel de detalle al seleccionar un finding
│   └── AccessibleSummary.tsx # Resumen textual + aria-live regions
├── lib/
│   └── demo-spec.ts        # PRD de demo: sistema de notificaciones de pagos
├── types/
│   └── index.ts            # Tipos TypeScript compartidos + constantes de UI
├── next.config.ts          # Proxy /api/* → localhost:8000
└── tailwind.config.ts      # Colores de confianza: green/yellow/red
```

---

## Instalación

### Requisitos previos
- Node.js 20+
- pnpm 8+

### Instalar dependencias

```bash
cd frontend
pnpm install --registry https://registry.npmjs.org
```

> Si tu red usa un registry privado (Artifactory, etc.), el flag `--registry` apunta al registry público.

---

## Ejecución

```bash
# Desarrollo
pnpm dev

# Build de producción
pnpm build
pnpm start

# Verificar tipos
pnpm exec tsc --noEmit
```

La app queda disponible en `http://localhost:3000`.

**Requisito:** el backend debe estar corriendo en `http://localhost:8000`.

---

## Páginas

### `/` — Inicio
- Textarea para pegar PRD, BRD o user stories
- Campo opcional para arquitectura / ADRs
- Botón **"Load demo"** carga un spec de ejemplo (sistema de notificaciones de pagos)
- Vista previa de los 6 agentes disponibles
- Accesibilidad: labels semánticos, error messages con `role="alert"`, skip link

### `/analysis` — Dashboard
Layout de 3 columnas:

```
┌─────────────┬──────────────────────┬────────────────┐
│   Sidebar   │    Confidence Map    │  Finding Panel │
│   izquierdo │    (React Flow)      │    derecho     │
│             │                      │                │
│  Agentes    │  Hub → Agentes →     │  Detalle del  │
│  + estado   │  Findings (nodos     │  finding       │
│  + resumen  │  color-coded)        │  seleccionado  │
└─────────────┴──────────────────────┴────────────────┘
```

---

## Componentes clave

### `ConfidenceMap.tsx`
- Construye el grafo React Flow en tiempo real a medida que llegan eventos SSE
- Layout automático con dagre (TB: top-to-bottom)
- Tres tipos de nodos: `hub`, `agent`, `finding`
- Nodos `finding` son botones interactivos que disparan el panel de detalle
- MiniMap para orientación en grafos grandes

### `AccessibleSummary.tsx`
- `aria-live="polite"` que narra el progreso para lectores de pantalla
- Panel de texto colapsable con conteo por nivel de confianza
- Summaries narrativos de cada agente completado
- Diseño inclusivo: toda información visual existe también en texto

### `FindingDetail.tsx`
- Barra de progreso con `role="progressbar"` y `aria-valuenow`
- Secciones: descripción, evidencia (blockquote), asunciones, validaciones pendientes
- Badge del agente y categoría del finding

---

## Flujo de datos

```
Usuario ingresa spec
        │
        ▼
POST /api/analyze → {analysis_id}
        │
        ▼
Redirect a /analysis
        │
        ▼
EventSource /api/analyze/{id}/stream
        │
        ├── agent_start    → agente pasa a "running" (pulsa)
        ├── agent_complete → nodos del mapa aparecen con sus findings
        └── analysis_complete → barra de progreso llega al 100%
```

---

## Proxy al backend

`next.config.ts` re-dirige todas las llamadas `/api/*` al backend:

```ts
// next.config.ts
rewrites: [{ source: "/api/:path*", destination: "http://localhost:8000/api/:path*" }]
```

No se necesita configurar CORS en el frontend.

---

## Paleta de colores

| Token | Color | Uso |
|-------|-------|-----|
| `confidence-green` | `#22c55e` | Findings explícitamente definidos |
| `confidence-yellow` | `#eab308` | Findings inferidos |
| `confidence-red` | `#ef4444` | Findings con alta incertidumbre |
| `accent` | `#6366f1` | Nodo hub, botones primarios, agentes activos |
| `surface` | `#0d0d1a` | Fondo principal |
| `surface-card` | `#13131f` | Cards y sidebars |

---

## Accesibilidad

El frontend implementa WCAG 2.1 AA como requisito, no como feature:

- **Skip link** visible al hacer Tab en la página: "Skip to main content"
- **`aria-live="polite"`** en `AccessibleSummary` narra el progreso en tiempo real
- **`aria-busy`** en el botón de análisis mientras carga
- **`role="alert"`** para mensajes de error
- **`role="progressbar"`** con `aria-valuenow` en la barra de progreso y confidence scores
- **`role="region"`** con etiquetas en cada panel
- **`aria-current`** en el finding seleccionado en la lista
- **`prefers-reduced-motion`** respetado en CSS (animaciones desactivadas)
- Navegación por teclado completa: Tab, Enter, Space
- Contraste: todos los textos cumplen ratio 4.5:1 mínimo

---

## Variables de entorno

El frontend no requiere variables de entorno en desarrollo. En producción:

| Variable | Descripción |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | URL del backend (si no se usa el proxy de Next.js) |

---

## Build y despliegue

```bash
pnpm build
# Output estático en .next/
# Deploy en Vercel, Netlify, o cualquier servidor Node.js
```
