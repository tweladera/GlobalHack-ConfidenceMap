# Accessibility — Confidence Map

Confidence Map was built with accessibility as a first-class requirement, not an afterthought.
This guide documents what exists, where it lives, and how it works.

---

## 1. Keyboard navigation

### View shortcuts (Alt + number)

| Shortcut | Action |
|----------|--------|
| `Alt+1` | Map view (React Flow — ConfidenceMap) |
| `Alt+2` | Table view (DecisionTable — filterable) |
| `Alt+3` | Text mode (full accessible document) |
| `Alt+4` | Risk Heat Map (5x5 probability x impact matrix) |

**Implementation:** `frontend/app/analysis/page.tsx:82–93`

```ts
window.addEventListener("keydown", (e) => {
  if (!e.altKey) return;
  if (e.key === "1") { /* map    */ }
  if (e.key === "2") { /* table  */ }
  if (e.key === "3") { /* text   */ }
  if (e.key === "4") { /* heatmap*/ }
});
```

Header buttons have `aria-pressed` and `title="Alt+N"` so the screen reader
and mouse tooltip communicate the available shortcut.

All interactive controls (buttons, inputs, links) are reachable with `Tab` via
standard semantic HTML — no manual `tabIndex` needed.

---

## 2. Screen reader support

There are two independent mechanisms that work in parallel:

### 2a. `announce()` — real-time narration

**File:** `frontend/app/analysis/page.tsx:62–71`

Function that updates an `aria-live="assertive"` + `sr-only` region with each
analysis event:

| SSE event | Announcement |
|-----------|-------------|
| `agent_start` | `"${agentName} has started analysis."` |
| `agent_complete` | `"${agentName} has completed analysis. Found N findings."` |
| `consolidation_start` | `"Cross-agent audit in progress."` |
| `consolidation_complete` | `"Cross-agent audit complete."` |
| `analysis_complete` | `"Analysis complete. N findings found."` |

**Technique:** clear → re-set with a 60ms delay to force re-announcement even
when the previous text is similar. This ensures the screen reader fires the
event even for repeated messages.

### 2b. `AccessibleSummary` — continuous passive narration

**File:** `frontend/components/AccessibleSummary.tsx`

Component with two parts:

**Invisible region (always active):**
```tsx
<div aria-live="polite" aria-atomic="false" className="sr-only" role="status">
  {statusText}  {/* updates automatically as each agent completes */}
</div>
```

**Visible panel (manual toggle):**
- Floating button bottom-left: `aria-expanded`, `aria-controls`, `aria-label`
- Panel with `role="region"`, `aria-label="Accessible text summary of confidence map"`
- Counts by level with `role="group"` and individual `aria-label`
- Top 3 critical findings in `<ul aria-label="High uncertainty findings">`
- Narrative summary per agent in natural language

### 2c. ARIA across the interface

Key instrumented elements:

| Element | ARIA attributes |
|---------|----------------|
| Progress bar | `role="progressbar"` · `aria-valuenow/min/max` · `aria-label` |
| View toggle | `role="group"` · `aria-pressed` · `aria-label` with shortcuts |
| Findings list | `role="list"` · `aria-label` with count · `aria-current` on selected |
| Collapsible panels | `aria-expanded` · `aria-controls` |
| Loading states | `aria-busy="true"` · `role="status"` · `aria-live="polite"` |
| Errors | `role="alert"` · `aria-live="assertive"` |
| Decorative icons | `aria-hidden="true"` on all |
| Global score | `aria-label="Global confidence: 78%"` |

---

## 3. Text mode (Alt+3)

Full view of all findings as a structured text document.

**Activation:** `Alt+3` or click on the "Text" toggle in the header.

**Implementation:** `frontend/app/analysis/page.tsx:494–600`

```tsx
<div role="document" aria-label="Text view — all findings">
  {/* heading per agent -> findings list -> "view detail" button with aria-label */}
</div>
```

Features:
- `role="document"` — declares the region as a navigable document
- `<h2>` / `<h3>` headings for semantic structure
- Each finding with confidence level in text (`[RED]`, `[YELLOW]`, `[GREEN]`)
- "View detail" button with `aria-label={f.title}` — unique for the screen reader
- "Copy executive summary" button with explicit `aria-label`

---

## 4. Accessibility agent — Accessibility Advocate

In addition to the platform's own accessibility, there is the **Accessibility Advocate** agent
that evaluates the **analyzed product** against WCAG 2.1 AA.

**File:** `backend/confidence_map/agents/accessibility_advocate.py`

Detects in specifications:
- Exclusive reliance on visual signals (without auditory or textual alternative)
- Lack of screen reader support in critical flows
- Navigation without keyboard support
- Insufficient contrast declared in the spec
- Language barriers or cognitive complexity

---

## 5. Known limitations

| Limitation | Context |
|------------|---------|
| React Flow canvas is not navigable node-by-node with keyboard | Library limit, not the project's. Text Mode (Alt+3) covers this case. |
| AccessibleSummary (button) overlaps visually with the right sidebar on small screens | Cosmetic issue, not functional. |

---

## 6. Key files

| File | What it implements |
|------|--------------------|
| `frontend/app/analysis/page.tsx` | Alt+1/2/3/4 shortcuts · announce() · aria in header and views |
| `frontend/components/AccessibleSummary.tsx` | Passive narration · accessible summary panel |
| `frontend/components/ConfidenceMap.tsx` | role/aria-label on visual map nodes |
| `frontend/components/DecisionTable.tsx` | Table with correct HTML semantics |
| `backend/confidence_map/agents/accessibility_advocate.py` | WCAG 2.1 AA evaluator agent |
