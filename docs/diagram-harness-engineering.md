# Harness Engineering
## Architecture diagram — Confidence Map

---

## Why it was implemented

AI agents fail in predictable ways: they exceed API usage, generate malformed output,
produce inconsistent results under rate limit pressure, or simply "hallucinate" with vague
evidence. Without a harness, these failures propagate silently to the user.

The **harness** is the architectural scaffolding that surrounds the agents and ensures that:
- Errors are captured and isolated without breaking the full flow
- Each agent's output is validated before being consumed
- API resources are distributed fairly among parallel agents
- Transient failures (rate limits, 5xx errors) are automatically recovered
- The user receives real-time feedback while the agents work

Reference: [Anthropic Engineering — Harness Design for Long-Running Apps](https://www.anthropic.com/engineering/harness-design-long-running-apps)

---

## How it is applied in the project

### Harness components

#### 1. Phase-based orchestration

```
Phase 1: Spec Analyst        (sequential — its output informs subsequent phases)
         v blackboard
Phase 2: 5 agents            (parallel — asyncio.gather with semaphore)
         v all results
Phase 3: Consolidator        (sequential — cross-examines all findings)
         v sentinel
Phase 4: Global score        (aggregation — weighted average of confidence_scores)
```

#### 2. Concurrency semaphore

`asyncio.Semaphore(3)` — maximum 3 agents calling Claude simultaneously.
Prevents saturating rate limits when 5 agents attempt to run in parallel.
The fourth and fifth agents wait in queue until a slot is freed.

#### 3. Retry policy with exponential backoff

```python
MAX_RETRIES = 2
BASE_DELAY  = 2.0s
# Delays: 2s -> 4s -> definitive failure
```
Covers: `RateLimitError`, `APIStatusError` (5xx).
Does not retry 4xx errors (those are client errors, not server errors).

#### 4. Output quality guardrails

After each Claude call, `_apply_guardrails()` validates:
- **Score-level alignment**: the confidence_score must fall within its level's range
  - green: 0.60-1.00 | yellow: 0.30-0.75 | red: 0.00-0.45
  - If not: clamped to the correct range + warning in logs
- **Empty evidence**: if the agent omits the citation, a placeholder is substituted
- **All-green distribution**: if all findings are green in a multi-finding result, a warning of possible shallow analysis is logged

#### 5. Error isolation

`call_agent()` always returns `AgentResult`, never raises an exception.
Errors are stored in `result.error` and `result.status = ERROR`.
The orchestrator continues with the remaining agents even if one fails.

#### 6. SSE streaming (real-time feedback)

The harness emits SSE events as each agent completes:
- `AGENT_START`: the agent started
- `AGENT_COMPLETE` / `AGENT_ERROR`: the agent finished with a result or error
- `CONSOLIDATION_START` / `CONSOLIDATION_COMPLETE`: the meta-judge acted
- `ANALYSIS_COMPLETE`: global score + final distribution
- Timeout: if an event does not arrive within 130s, the harness emits an error

#### 7. Shared Blackboard pattern

The Spec Analyst findings (Phase 1) are formatted as XML and passed to the 5 Phase 2 agents.
This prevents each agent from rediscovering the same problems and directs them to reason
from their specific domain.

#### 8. DEMO_MODE (Test harness)

With `DEMO_MODE=true`, the harness uses pre-generated results with simulated delays.
The SSE flow is identical to real mode — without consuming API credits.
Allows validating the full architecture at $0 cost.

---

## Diagram

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {
  'primaryColor': '#1e293b', 'primaryTextColor': '#f1f5f9',
  'primaryBorderColor': '#f97316', 'lineColor': '#475569',
  'clusterBkg': '#0f172a', 'clusterBorder': '#334155',
  'fontFamily': 'Segoe UI, system-ui, sans-serif'
}}}%%
flowchart TD
  classDef req     fill:#1d3461,stroke:#3b82f6,color:#bfdbfe
  classDef phase1  fill:#1d3461,stroke:#60a5fa,color:#bfdbfe
  classDef phase2  fill:#3b0764,stroke:#a78bfa,color:#e9d5ff
  classDef phase3  fill:#14532d,stroke:#4ade80,color:#86efac
  classDef harness fill:#451a03,stroke:#f97316,color:#fed7aa
  classDef sse     fill:#1e293b,stroke:#06b6d4,color:#67e8f9
  classDef guard   fill:#422006,stroke:#eab308,color:#fde68a
  classDef err     fill:#450a0a,stroke:#ef4444,color:#fca5a5

  REQ["AnalysisRequest\nspec · architecture · context"]:::req

  subgraph HARNESS["HARNESS — orchestrator.py"]
    subgraph P1["PHASE 1 — Sequential"]
      SA["Spec Analyst\ncall_agent()"]:::phase1
      BB["Shared Blackboard\nformat_spec_findings() -> XML"]:::harness
    end
    subgraph SEM["Semaphore(3) — max 3 concurrent"]
      subgraph P2["PHASE 2 — asyncio.gather"]
        A1["Arch Validator"]:::phase2
        A2["Risk Intelligence"]:::phase2
        A3["Business Impact"]:::phase2
        A4["Accessibility"]:::phase2
        A5["Delivery Historian"]:::phase2
      end
    end
    subgraph P3["PHASE 3 — Sequential"]
      CON["Consolidator\nMeta-judge · cross-examines findings"]:::phase3
    end
    SCORE["Global score\navg(confidence_scores) · distribution"]:::harness
  end

  subgraph BASE["BASE AGENT — base.py"]
    API["Claude Sonnet 4.6\nreport_findings tool"]:::phase1
    RETRY["Retry + backoff\n2s -> 4s · MAX 2 retries"]:::harness
    GUARD["_apply_guardrails()\nscore · evidence · all-green"]:::guard
    ISO["Error isolation\nalways returns AgentResult"]:::err
  end

  subgraph SSE["SSE STREAMING"]
    E1["AGENT_START"]:::sse
    E2["AGENT_COMPLETE / ERROR"]:::sse
    E3["CONSOLIDATION_COMPLETE"]:::sse
    E4["ANALYSIS_COMPLETE + score"]:::sse
    TO["Timeout 130s -> ERROR"]:::err
  end

  REQ --> SA
  SA --> BB
  BB --> A1 & A2 & A3 & A4 & A5
  A1 & A2 & A3 & A4 & A5 --> CON
  SA --> CON
  CON --> SCORE
  SA & A1 & A2 & A3 & A4 & A5 --> API
  API --> RETRY --> GUARD --> ISO
  ISO --> E1 & E2
  CON --> E3
  SCORE --> E4
```

---

## Comparison with the Anthropic pattern

| Anthropic pattern (long-running) | Implementation in Confidence Map |
|----------------------------------|----------------------------------|
| Multi-agent specialization | 6 agents + consolidator with separate domains |
| External evaluation (Evaluator) | Consolidator: separate agent that judges all agents' output |
| Structured artifacts | XML Blackboard passed between phases |
| Output quality guardrails | `_apply_guardrails()`: score, evidence, distribution |
| Rate limiting | `asyncio.Semaphore(3)` |
| Retry + backoff | `_make_api_call()` with exponential backoff |
| Error isolation | `call_agent()` never raises — always returns result |
| Environmental continuity | SSE streaming: the user sees progress in real time |
| Test harness | `DEMO_MODE=true` with mock results identical in structure |
| Context reset | Not applicable: each agent is a single call (not multi-turn) |
| Feature registry | Not applicable: atomic analysis, not multi-session |

---

## Key files in the project

| File | Harness component |
|------|------------------|
| `backend/confidence_map/core/orchestrator.py` | Phase orchestration, semaphore, SSE queue, timeout, global score |
| `backend/confidence_map/agents/base.py` | `_make_api_call()` retry, `_apply_guardrails()`, `call_agent()` error isolation |
| `backend/confidence_map/agents/base.py` | `format_spec_findings()` shared blackboard |
| `backend/confidence_map/core/mock_results.py` | DEMO_MODE test harness |
| `backend/confidence_map/core/settings.py` | `DEMO_MODE`, `MODEL`, `ENABLE_THINKING`, `THINKING_BUDGET_TOKENS` |
| `backend/confidence_map/api/analysis.py` | SSE endpoint — consumes events from the harness |
