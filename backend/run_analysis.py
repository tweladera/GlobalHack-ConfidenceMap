"""Live analysis runner — streams real agent output to the console.
Run from backend/: uv run python run_analysis.py
"""
import asyncio
import sys
import time

# ── Colors ────────────────────────────────────────────────────────────────────
C = {
    "reset":  "\033[0m",
    "bold":   "\033[1m",
    "dim":    "\033[2m",
    "cyan":   "\033[36m",
    "green":  "\033[32m",
    "yellow": "\033[33m",
    "red":    "\033[31m",
    "accent": "\033[35m",
}

CONF_COLOR = {"green": C["green"], "yellow": C["yellow"], "red": C["red"]}

def line(char="─", width=70):
    print(char * width)

def banner(text):
    print(f"\n{C['bold']}{C['cyan']}{text}{C['reset']}")

def agent_header(name, t):
    print(f"\n{C['bold']}[{name}]{C['reset']}  {C['dim']}{t:.1f}s{C['reset']}")

def finding(f):
    col = CONF_COLOR.get(f["confidence"], C["reset"])
    score = round(f["confidence_score"] * 100)
    level = f["confidence"].upper()
    print(f"  {col}● [{level} {score}%]{C['reset']} {f['title']}")

# ── Spec content ──────────────────────────────────────────────────────────────

SPEC = """\
# NovaBank — International Instant Payments
## Product Requirements Document v1.2

**Author:** Sofia Chen, Product Manager
**Reviewed by:** Daniel Reyes, Software Architect
**Status:** Under review
**Delivery target:** 6 weeks

## Business context

NovaBank needs to launch international instant payments for corporate clients in LATAM.
Local regulations require transaction confirmation in under 10 seconds.
The product will compete directly with Wise and Remitly in the B2B segment.
Projected growth of 300% in transaction volume in the first 6 months.

## MVP scope

### US-001: Initiate international payment
As a corporate client, I want to initiate an international payment from my dashboard
to transfer funds to suppliers abroad.

**Acceptance criteria:**
- The user enters: amount, destination currency, beneficiary IBAN/SWIFT account
- The system validates available funds before processing
- Transaction confirmation is displayed to the user
- The payment must complete within the regulatory SLA

**Technical notes:**
- Processing goes through NovaBank's legacy SWIFT gateway (CoreBanking v2.1)
- Anti-fraud validation is mandatory before execution

### US-002: Query payment status
As a client, I want to check the status of a payment in real time
to know if it was processed correctly.

**Acceptance criteria:**
- The user can see: pending, processing, completed, failed
- Status updates automatically without refreshing the page
- Estimated crediting time to the destination account is displayed

### US-003: Result notification
As a client, I want to receive a notification when my payment is processed
to confirm that the operation was successful.

**Acceptance criteria:**
- Immediate in-app notification when status changes
- Confirmation email with PDF receipt
- In case of failure, the system must indicate what to do next

### US-004: Transaction history
As a client, I want to see the complete history of my international payments
to reconcile with my accounting.

**Acceptance criteria:**
- Paginated list of transactions
- Filters by date, status, and amount
- Export to CSV

## Known technical constraints

- The CoreBanking v2.1 SWIFT gateway is a synchronous system with latencies of 2-15 seconds
- The external anti-fraud system (FraudShield) responds on average in 3 seconds
- The accounts database is on Oracle 11g (does not support modern distributed transactions)
- Current infrastructure: on-premise, no Kubernetes, manual deployment

## Non-functional requirements

- High availability: the system must be available 99.9% of the time
- Regulatory SLA requires confirmation in under 10 seconds
- Support for peaks of up to 500 transactions per minute on accounting close days

## Security and compliance

- All transactions must be audited with full traceability
- PCI-DSS Level 1 compliance
- SWIFT/IBAN account data cannot be stored in plain text
"""

ARCHITECTURE = """\
# Proposed Architecture — NovaBank International Payments

**Frontend:**
- React SPA with polling every 3 seconds to update payment status
- No WebSockets (simplification decision for MVP)
- Designed primarily for desktop; mobile as a future enhancement

**API Gateway:**
- Node.js + Express, single instance
- Handles JWT authentication and routing
- No rate limiting implemented yet

**Payment Service:**
- Python + FastAPI
- Calls CoreBanking gateway synchronously on each transaction
- Calls FraudShield synchronously before authorizing
- No timeout configured for CoreBanking calls (uses HTTP client default)
- No retry logic implemented

**CoreBanking Gateway (legacy):**
- Proprietary SWIFT system, on-premise
- Synchronous REST API with variable latency (2-15 seconds)
- No internal SLA documented
- Single point of integration for all payments

**Database:**
- PostgreSQL for Payment Service data
- Oracle 11g for account data (read-only from the new system)
- No idempotency mechanism implemented for transactions

**Notifications:**
- Direct call to SendGrid from the Payment Service on each transaction completion
- No message queue
- No retry on SendGrid failure

**Infrastructure:**
- Deployed on on-premise VMs
- No container orchestration
- Manual scaling
"""

# ── Main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    from confidence_map.models.analysis import AnalysisRequest
    from confidence_map.models.events import SSEEventType
    from confidence_map.core.orchestrator import stream_analysis

    request = AnalysisRequest(spec=SPEC, architecture=ARCHITECTURE, context="")

    print(f"\n{C['bold']}{'═'*70}")
    print("  CONFIDENCE MAP — Real-mode analysis")
    print(f"  NovaBank International Instant Payments")
    print(f"{'═'*70}{C['reset']}")
    print(f"{C['dim']}  6 specialist agents + Consolidator  ·  claude-sonnet-4-6{C['reset']}\n")

    t0 = time.monotonic()
    agent_times: dict[str, float] = {}
    dist = {"green": 0, "yellow": 0, "red": 0}
    all_findings: list[dict] = []

    async for event in stream_analysis(request):
        elapsed = time.monotonic() - t0

        if event.type == SSEEventType.AGENT_START:
            agent_times[event.agent_id or ""] = elapsed
            print(f"  {C['cyan']}▶ {event.agent_name}{C['reset']}  {C['dim']}starting...{C['reset']}")
            sys.stdout.flush()

        elif event.type in (SSEEventType.AGENT_COMPLETE, SSEEventType.AGENT_ERROR):
            start = agent_times.get(event.agent_id or "", elapsed)
            duration = elapsed - start
            result = event.result or {}
            findings = result.get("findings", [])

            agent_header(event.agent_name or "", duration)

            if event.type == SSEEventType.AGENT_ERROR:
                print(f"  {C['red']}✗ Error: {event.error}{C['reset']}")
            else:
                for f in findings:
                    finding(f)
                    c = f.get("confidence", "")
                    if c in dist:
                        dist[c] += 1
                    all_findings.append(f)
                summary = result.get("summary", "")
                if summary:
                    print(f"\n  {C['dim']}{summary[:200]}{'...' if len(summary) > 200 else ''}{C['reset']}")
            sys.stdout.flush()

        elif event.type == SSEEventType.CONSOLIDATION_START:
            print(f"\n{C['accent']}{'─'*70}")
            print(f"  ◉ Consolidator  {C['dim']}cross-examining all findings...{C['reset']}")
            sys.stdout.flush()

        elif event.type == SSEEventType.CONSOLIDATION_COMPLETE:
            c = event.consolidation
            if c:
                print(f"\n{C['bold']}  CONFIRMED CRITICALS ({len(c.confirmed_criticals)}){C['reset']}")
                for cc in c.confirmed_criticals:
                    print(f"  {C['red']}⚑ {cc.topic}{C['reset']}")
                    print(f"    {C['dim']}Agents: {', '.join(cc.agents)}{C['reset']}")

                if c.contradictions:
                    print(f"\n{C['bold']}  CONTRADICTIONS ({len(c.contradictions)}){C['reset']}")
                    for con in c.contradictions:
                        print(f"  {C['yellow']}⚡ {con.topic}{C['reset']}")

                if c.redundancies:
                    print(f"\n{C['bold']}  REDUNDANCIES ({len(c.redundancies)}){C['reset']}")
                    for r in c.redundancies:
                        print(f"  {C['dim']}≈ {r.topic}  [keep: {r.kept}]{C['reset']}")

                print(f"\n{C['bold']}  AUDIT VERDICT{C['reset']}")
                print(f"  {C['dim']}{c.audit_summary}{C['reset']}")
            sys.stdout.flush()

        elif event.type == SSEEventType.ANALYSIS_COMPLETE:
            total_time = time.monotonic() - t0
            total = event.total_findings or 0
            score = round((event.global_confidence_score or 0) * 100)
            score_col = C["green"] if score >= 70 else C["yellow"] if score >= 45 else C["red"]

            print(f"\n{C['bold']}{'═'*70}{C['reset']}")
            print(f"{C['bold']}  ANALYSIS COMPLETE  ·  {total_time:.0f}s{C['reset']}")
            print(f"  Global confidence: {score_col}{C['bold']}{score}%{C['reset']}")
            print(f"  Findings: {total}  "
                  f"{C['green']}●{dist['green']} green{C['reset']}  "
                  f"{C['yellow']}●{dist['yellow']} yellow{C['reset']}  "
                  f"{C['red']}●{dist['red']} red{C['reset']}")
            print(f"{C['bold']}{'═'*70}{C['reset']}\n")

        elif event.type == SSEEventType.ERROR:
            print(f"\n{C['red']}✗ Pipeline error: {event.error}{C['reset']}")
            sys.exit(1)

asyncio.run(main())
