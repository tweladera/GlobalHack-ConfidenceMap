# Spec-to-Data Pipelines
## Architecture diagram — Confidence Map

---

## Why it was implemented

Software specifications (PRDs, user stories, architecture documents) are unstructured text.
Teams read them, interpret them, and make decisions — but that process is
invisible, untraceable, and not comparable across projects.

The **Spec-to-Data Pipelines** challenge consists of transforming that raw text into
structured, actionable, and queryable data: findings with type, confidence level, evidence,
assumptions, and recommended actions.

Without this transformation, AI can only "talk about" the specification. With it, it can
reason about it, quantify it and make it visible to the entire team.

---

## How it is applied in the project

### 1. Input: unstructured text

The user enters up to three types of text:
- **PRD / Spec**: functional requirements, user stories, acceptance criteria
- **Architecture notes**: technical decisions, chosen patterns, dependencies
- **Context**: regulatory constraints, SLAs, external integrations

### 2. Transformation: Claude tool use with Pydantic schema

Each agent receives the text and uses the `report_findings` tool with a strict JSON Schema:

```json
{
  "title":             "string (max 100 chars)",
  "description":       "string",
  "confidence":        "green | yellow | red",
  "confidence_score":  "float 0.0-1.0",
  "evidence":          "exact quote from the spec",
  "assumptions":       ["list of assumptions"],
  "needs_validation":  ["list of open questions"],
  "recommended_action":"concrete next step",
  "category":          "ambiguity | contradiction | risk | gap | accessibility | cost | pattern"
}
```

### 3. Output: structured data with full traceability

Each finding is a validated Pydantic object with:
- Semantic confidence level (green/yellow/red) + numeric score (0.0-1.0)
- Evidence: textual quote from the original specification
- Explicit assumptions the agent is making
- Open questions the team must validate
- Concrete recommended action

### 4. Distribution and global score

The orchestrator aggregates all findings and calculates:
- Distribution: how many greens, yellows, reds
- Global confidence score: weighted average of all confidence_scores
- That number appears in the central hub of the visual map

---

## Diagram

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {
  'primaryColor': '#1e293b', 'primaryTextColor': '#f1f5f9',
  'primaryBorderColor': '#3b82f6', 'lineColor': '#475569',
  'clusterBkg': '#0f172a', 'clusterBorder': '#334155',
  'fontFamily': 'Segoe UI, system-ui, sans-serif'
}}}%%
flowchart LR
  classDef input   fill:#1d3461,stroke:#3b82f6,color:#bfdbfe
  classDef agent   fill:#14532d,stroke:#22c55e,color:#86efac
  classDef tool    fill:#312e81,stroke:#818cf8,color:#c7d2fe
  classDef valid   fill:#78350f,stroke:#f59e0b,color:#fde68a
  classDef output  fill:#3b0764,stroke:#a855f7,color:#e9d5ff
  classDef consume fill:#1e293b,stroke:#475569,color:#94a3b8

  subgraph IN["  INPUT — Unstructured text  "]
    A1["PRD / User Stories"]:::input
    A2["Architecture Notes"]:::input
    A3["Context / Constraints"]:::input
  end

  subgraph PHASE1["  PHASE 1  "]
    B1["Spec Analyst\n(sequential)"]:::agent
  end

  subgraph PHASE2["  PHASE 2 — Parallel  "]
    B2["Arch Validator"]:::agent
    B3["Risk Intelligence"]:::agent
    B4["Business Impact"]:::agent
    B5["Accessibility"]:::agent
    B6["Delivery Historian"]:::agent
  end

  subgraph TOOL["  Claude Tool Use  "]
    C1["report_findings\nStrict JSON Schema"]:::tool
    C2["Pydantic v2\n+ guardrails"]:::valid
  end

  subgraph OUT["  OUTPUT  "]
    D1["Finding\nconfidence · score · evidence"]:::output
    D2["AgentResult\nfindings + summary"]:::output
    D3["Global score\n+ distribution"]:::output
  end

  subgraph CONSUME["  Frontend consumption  "]
    E1["Visual map"]:::consume
    E2["Decision Table"]:::consume
    E3["Export PDF"]:::consume
    E4["Jira Backlog"]:::consume
    E5["AI Chat"]:::consume
  end

  A1 & A2 & A3 --> B1
  B1 -->|blackboard| B2 & B3 & B4 & B5 & B6
  B1 & B2 & B3 & B4 & B5 & B6 --> C1
  C1 --> C2 --> D1 --> D2 --> D3
  D2 --> E1 & E2 & E3 & E4 & E5
```

---

## Key files in the project

| File | Role in the pipeline |
|------|---------------------|
| `backend/confidence_map/models/findings.py` | Pydantic schema for Finding and AgentResult |
| `backend/confidence_map/agents/base.py` | `REPORT_FINDINGS_TOOL` — JSON Schema for Claude tool use |
| `backend/confidence_map/agents/base.py` | `_apply_guardrails()` — post-extraction validation |
| `backend/confidence_map/core/orchestrator.py` | Findings aggregation and global score calculation |
| `frontend/types/index.ts` | TypeScript types that consume the pipeline output |
