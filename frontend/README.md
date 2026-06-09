# Confidence Map — Frontend

Web interface that visualizes multi-agent analysis in real time through an interactive confidence map built with React Flow.

---

## Technologies

| Tool | Version | Role |
|------|---------|------|
| Next.js | 15 (App Router) | React framework |
| TypeScript | 5 strict | Static typing |
| React Flow | 11 | Map visualization |
| dagre | 1.1 | Automatic graph layout |
| Tailwind CSS | 3.4 | Utility styles |
| Lucide React | 0.468 | Icons |

---

## Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Global layout + accessibility skip link
│   ├── page.tsx            # Home page: spec input
│   ├── globals.css         # Base styles + React Flow overrides
│   └── analysis/
│       └── page.tsx        # Analysis dashboard with SSE streaming
│       api/analyze/[id]/
│           stream/route.ts # SSE Route Handler (bypasses Next.js buffering)
├── components/
│   ├── ConfidenceMap.tsx   # React Flow: central visual map
│   ├── AgentStatusCard.tsx # Left sidebar: agent status timeline
│   ├── FindingDetail.tsx   # Detail panel for selected finding
│   ├── DecisionTable.tsx   # Filterable findings table (Alt+2)
│   ├── HeatMap.tsx         # 5×5 risk matrix (Alt+4)
│   ├── BacklogModal.tsx    # JIRA-ready ticket generator
│   ├── ChatPanel.tsx       # Inline AI chat sidebar
│   └── AccessibleSummary.tsx # Text summary + aria-live regions
├── lib/
│   ├── demo-spec.ts        # Demo specs: NovaBank Payments + Auth MFA
│   ├── export.ts           # Markdown download + PDF report
│   ├── history.ts          # localStorage analysis history
│   └── config.ts           # User config (default view, etc.)
├── types/
│   └── index.ts            # Shared TypeScript types + UI constants
├── next.config.ts          # Proxy /api/* → localhost:8000
└── tailwind.config.ts      # Confidence color tokens: green/yellow/red
```

---

## Installation

### Prerequisites
- Node.js 22+
- pnpm 10+

### Install dependencies

```bash
cd frontend
pnpm install --registry https://registry.npmjs.org
```

> If your network uses a private registry (Artifactory, etc.), the `--registry` flag points to the public registry.

---

## Running

```bash
# Development
pnpm dev

# Production build
pnpm build
pnpm start

# Type check
pnpm exec tsc --noEmit
```

App available at `http://localhost:3000`.

**Requirement:** backend must be running at `http://localhost:8000`.

---

## Pages

### `/` — Home
- Textarea for pasting PRD, BRD, or user stories
- Optional field for architecture / ADRs
- **"NovaBank · Payments"** and **"NovaBank · Auth MFA"** preset buttons
- Preview of the 6 available agents
- Accessibility: semantic labels, error messages with `role="alert"`, skip link

### `/analysis` — Dashboard
3-column layout:

```
┌─────────────┬──────────────────────┬────────────────┐
│  Left       │    Confidence Map    │  Finding Panel │
│  Sidebar    │    (React Flow)      │  (right)       │
│             │                      │                │
│  Agents     │  Hub → Agents →      │  Selected      │
│  + status   │  Findings (color-    │  finding       │
│  + summary  │  coded nodes)        │  detail        │
└─────────────┴──────────────────────┴────────────────┘
```

Header (post-analysis): **Export ▾** · **Backlog** · **Ask AI**

---

## Key Components

### `ConfidenceMap.tsx`
- Builds the React Flow graph in real time as SSE events arrive
- Automatic layout with dagre (TB: top-to-bottom)
- Three node types: `hub`, `agent`, `finding`
- `finding` nodes are interactive buttons that open the detail panel
- MiniMap for orientation in large graphs

### `AgentStatusCard.tsx`
- Timeline with status dot per agent (pending / running / completed / error)
- Elapsed seconds counter next to the spinner for running agents
- Mini confidence distribution badges (green/yellow/red) when completed
- "Show reasoning" toggle when `ENABLE_THINKING=true`

### `AccessibleSummary.tsx`
- `aria-live="polite"` narrates progress for screen readers
- Collapsible text panel with count per confidence level
- Narrative summaries from each completed agent
- Inclusive design: all visual information also available as text

### `FindingDetail.tsx`
- Progress bar with `role="progressbar"` and `aria-valuenow`
- Sections: description, evidence (blockquote), assumptions, pending validations
- Agent badge and finding category

---

## Data Flow

```
User submits spec
        │
        ▼
POST /api/analyze → {analysis_id}
        │
        ▼
Redirect to /analysis
        │
        ▼
EventSource /api/analyze/{id}/stream  ← Route Handler (no buffering)
        │
        ├── agent_start    → agent transitions to "running" (pulsing dot)
        ├── agent_complete → map nodes appear with their findings
        └── analysis_complete → progress bar reaches 100%
```

### SSE Streaming Architecture
`next.config.ts` rewrites buffer SSE responses. The Route Handler at
`app/api/analyze/[id]/stream/route.ts` bypasses this by piping the upstream
`ReadableStream` directly to the client with `no-cache, no-transform` headers.

---

## Backend Proxy

`next.config.ts` redirects all `/api/*` calls to the backend:

```ts
// next.config.ts
rewrites: [{ source: "/api/:path*", destination: "http://localhost:8000/api/:path*" }]
```

SSE stream uses the Route Handler directly — no CORS configuration needed in the frontend.

---

## Color Palette

| Token | Color | Usage |
|-------|-------|-------|
| `confidence-green` | `#22c55e` | Explicitly defined findings |
| `confidence-yellow` | `#eab308` | Inferred findings |
| `confidence-red` | `#ef4444` | High-uncertainty findings |
| `accent` | `#6366f1` | Hub node, primary buttons, active agents |
| `surface` | `#0d0d1a` | Main background |
| `surface-card` | `#13131f` | Cards and sidebars |

---

## Accessibility

The frontend implements WCAG 2.1 AA as a requirement, not a feature:

- **Skip link** visible on Tab: "Skip to main content"
- **`aria-live="polite"`** in `AccessibleSummary` narrates progress in real time
- **`aria-busy`** on the analysis button while loading
- **`role="alert"`** for error messages
- **`role="progressbar"`** with `aria-valuenow` on progress bars and confidence scores
- **`role="region"`** with labels on each panel
- **`aria-current`** on the selected finding in the list
- **`prefers-reduced-motion`** respected in CSS (animations disabled)
- Full keyboard navigation: Tab, Enter, Space
- Contrast: all text meets minimum 4.5:1 ratio

---

## Environment Variables

The frontend requires no environment variables in development. In production:

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend URL (if not using the Next.js proxy) |

---

## Build and Deploy

```bash
pnpm build
# Static output in .next/
# Deploy on Vercel, Netlify, or any Node.js server
```
