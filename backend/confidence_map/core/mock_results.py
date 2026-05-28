"""Pre-generated mock results for the NovaBank demo case.

Used when DEMO_MODE=true. Simulates realistic agent outputs without API calls.
Findings are based on the NovaBank international payments spec.
"""

from __future__ import annotations

from confidence_map.models.findings import (
    AgentResult,
    AgentStatus,
    ConfidenceLevel,
    ConfirmedCritical,
    ConsolidatorResult,
    Contradiction,
    Finding,
    Redundancy,
)

# Simulated agent completion times (seconds) — realistic but fast for demo
AGENT_DELAYS: dict[str, float] = {
    "spec_analyst": 2.5,
    "arch_validator": 3.2,
    "risk_intelligence": 2.8,
    "business_impact": 2.2,
    "accessibility_advocate": 2.6,
    "delivery_historian": 2.1,
}


def get_mock_results() -> dict[str, AgentResult]:
    """Return pre-generated AgentResult for each agent keyed by agent_id."""
    return {
        "spec_analyst": _spec_analyst(),
        "arch_validator": _arch_validator(),
        "risk_intelligence": _risk_intelligence(),
        "business_impact": _business_impact(),
        "accessibility_advocate": _accessibility_advocate(),
        "delivery_historian": _delivery_historian(),
    }


# ── Helpers ───────────────────────────────────────────────────────────────────


def _f(
    *,
    title: str,
    description: str,
    confidence: str,
    score: float,
    evidence: str,
    assumptions: list[str],
    needs_validation: list[str],
    recommended_action: str = "",
    category: str,
    agent_id: str,
    agent_name: str,
) -> Finding:
    return Finding(
        title=title,
        description=description,
        confidence=ConfidenceLevel(confidence),
        confidence_score=score,
        evidence=evidence,
        assumptions=assumptions,
        needs_validation=needs_validation,
        recommended_action=recommended_action,
        category=category,
        agent_id=agent_id,
        agent_name=agent_name,
    )


def _result(
    agent_id: str,
    agent_name: str,
    agent_icon: str,
    findings: list[Finding],
    summary: str,
    thinking: str = "",
) -> AgentResult:
    return AgentResult(
        agent_id=agent_id,
        agent_name=agent_name,
        agent_icon=agent_icon,
        status=AgentStatus.COMPLETED,
        findings=findings,
        summary=summary,
        thinking=thinking,
    )


# ── Agent 1: Spec Analyst ─────────────────────────────────────────────────────


def _spec_analyst() -> AgentResult:
    aid, aname = "spec_analyst", "Spec Analyst"
    findings = [
        _f(
            title="CoreBanking timeout behavior not defined",
            description=(
                "The spec does not define what happens when the CoreBanking gateway takes more than 10 seconds. "
                "Without this behavior defined, an automatic retry would generate duplicate payments — "
                "the most critical risk in a payment system."
            ),
            confidence="red",
            score=0.08,
            evidence="'The payment must complete within the regulatory SLA' — no definition of what happens if it does not.",
            assumptions=[],
            needs_validation=[
                "What is the behavior when CoreBanking exceeds the SLA?",
                "Does the system retry or cancel the transaction?",
                "How is the user notified of a transaction in an undefined state?",
            ],
            recommended_action=(
                "Schedule a refinement session with Sofia and Daniel to define "
                "timeout behavior: cancel, retry with idempotency, "
                "or mark as 'pending' for manual reconciliation?"
            ),
            category="ambiguity",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="US-003: 'What to do next' on failure not specified",
            description=(
                "The failure story says 'the system must indicate what to do next' "
                "but does not define what those actions are. Retry? Contact support? "
                "Is the retry automatic or manual? Without this, the team will implement "
                "inconsistent behaviors across failure scenarios."
            ),
            confidence="red",
            score=0.15,
            evidence="'In case of failure, the system must indicate what to do next.'",
            assumptions=["'Failure' includes anti-fraud rejection and CoreBanking timeout."],
            needs_validation=[
                "What actions are available after a failure?",
                "Can the user retry immediately or is there a waiting period?",
            ],
            recommended_action=(
                "Sofia should draft specific acceptance criteria for US-003 error states: "
                "list of available actions (retry, contact support, view status) "
                "with UX copy defined for each case."
            ),
            category="gap",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="10-second regulatory SLA absent from acceptance criteria",
            description=(
                "The 10-second value is mentioned in the business context but no "
                "user story references it explicitly as a verifiable criterion. "
                "Without this in the ACs, QA cannot build an acceptance test for the SLA."
            ),
            confidence="yellow",
            score=0.42,
            evidence=(
                "'Local regulation requires transaction confirmation in under 10 seconds.' "
                "— appears in context, not in ACs."
            ),
            assumptions=["The SLA applies to the full US-001 flow, not just the screen response."],
            needs_validation=["Does the 10s SLA apply to total time or to API response time?"],
            recommended_action=(
                "Add as an explicit acceptance criterion in US-001: "
                "'The system returns confirmation or error to the user in under 10 seconds from submission.' "
                "This turns the SLA into a QA-automatable test."
            ),
            category="gap",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="US-002: Auto-update mechanism contradicts technical notes",
            description=(
                "US-002 acceptance criteria say 'status updates automatically without refreshing the page', "
                "but technical notes specify 'polling every 3 seconds'. "
                "Polling is not automatic update; it is a simulation with up to 3s latency. "
                "The criterion and the proposed implementation are inconsistent."
            ),
            confidence="yellow",
            score=0.38,
            evidence=(
                "AC: 'Status updates automatically without refreshing the page.' "
                "Technical notes: 'React SPA with polling every 3 seconds'."
            ),
            assumptions=[],
            needs_validation=["Is 3-second maximum latency acceptable to the user?"],
            recommended_action=(
                "Align with product on whether 3s polling is acceptable for US-002. "
                "If not, enable WebSockets or SSE before the sprint starts — "
                "retrofitting the frontend afterwards is 5x more costly."
            ),
            category="contradiction",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="Transaction history: export criteria incomplete",
            description=(
                "US-004 specifies CSV export but does not define: which fields are included, "
                "whether sensitive data (full IBAN) is exported or masked, "
                "or if there is a record limit. In a PCI-DSS context, exporting account data "
                "without restrictions is a compliance risk."
            ),
            confidence="yellow",
            score=0.35,
            evidence="'CSV export' — no field specification or security restrictions.",
            assumptions=["The CSV is for internal use by the corporate client's treasury team."],
            needs_validation=[
                "Are sensitive fields (IBAN, SWIFT) exported in full or masked?",
                "Is there a record limit per export?",
            ],
            recommended_action=(
                "Define in US-004: export last 4 digits of IBAN/SWIFT masked, "
                "10,000-record limit per export, and review with Legal "
                "whether the CSV requires additional controls under PCI-DSS."
            ),
            category="gap",
            agent_id=aid,
            agent_name=aname,
        ),
    ]
    return _result(
        aid, aname, "FileSearch", findings,
        "The NovaBank spec analysis reveals five critical issues. The most urgent: "
        "the CoreBanking timeout behavior is undefined, creating direct risk of duplicate payments. "
        "Additionally, the 10-second regulatory SLA does not appear in the acceptance criteria, "
        "the payment failure story is too vague to implement, and there is a contradiction "
        "between the 'automatic update' criterion and the proposed polling. "
        "A refinement session with Sofia and Daniel is recommended before development begins.",
        thinking=(
            "I'll analyze the NovaBank international payments spec carefully, "
            "looking for explicit definitions, contradictions, and gaps.\n\n"
            "Starting with explicit definitions: the 10-second regulatory SLA appears in the "
            "business context section but is absent from all user story acceptance criteria. "
            "This means QA cannot write an automatable acceptance test for it — that's a gap.\n\n"
            "US-001 (initiate payment): the acceptance criteria list the required fields, "
            "but what happens when CoreBanking exceeds the SLA? The spec says "
            "'the payment must complete within 10 seconds' but never defines the failure path. "
            "Without this, engineers might implement automatic retry on timeout, "
            "which would generate duplicate payments — the most dangerous failure mode "
            "in a payment system. RED, high urgency.\n\n"
            "US-002 (payment status): 'updates automatically without refreshing the page' "
            "vs. technical notes saying 'polling every 3 seconds'. These are contradictory. "
            "Polling is not automatic push — it has up to 3 second latency. "
            "The product owner needs to decide: is 3s acceptable? "
            "If yes, update the AC. If not, implement WebSockets before the sprint starts.\n\n"
            "US-003 (failure handling): 'indicate what to do next' is dangerously vague. "
            "What ARE the next steps? Retry? Contact support? Cancel? "
            "This needs explicit acceptance criteria before engineering begins.\n\n"
            "US-004 (CSV export): no field specification, no mention of whether sensitive data "
            "like IBAN is exported in full or masked. In a PCI-DSS context this is a risk."
        ),
    )


# ── Agent 2: Architecture Validator ──────────────────────────────────────────


def _arch_validator() -> AgentResult:
    aid, aname = "arch_validator", "Architecture Validator"
    findings = [
        _f(
            title="Synchronous CoreBanking (2-15s) makes 10s SLA mathematically impossible",
            description=(
                "With CoreBanking latency of 2-15s and an additional 3s for anti-fraud, "
                "total time at P95 exceeds 18 seconds. "
                "The proposed architecture cannot meet the 10s regulatory SLA "
                "under normal load, guaranteeing regulatory non-compliance from day one."
            ),
            confidence="red",
            score=0.05,
            evidence=(
                "'The SWIFT CoreBanking v2.1 gateway is a synchronous system with latencies of 2-15 seconds.' "
                "'The external anti-fraud system (FraudShield) responds on average in 3 seconds.'"
            ),
            assumptions=["Latencies are additive in the current synchronous flow."],
            needs_validation=[
                "Is it possible to pre-qualify the transaction with anti-fraud asynchronously?",
                "Does CoreBanking have an undocumented async mode?",
            ],
            recommended_action=(
                "Implement async pattern: the endpoint returns 202 Accepted with a transaction ID; "
                "status is polled or pushed via WebSocket. "
                "This decouples the user SLA from CoreBanking latency."
            ),
            category="contradiction",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="Single-instance API Gateway: single point of failure in a financial system",
            description=(
                "The API Gateway is a single instance with no load balancer or redundancy. "
                "Any restart, deployment, or node failure leaves the system completely inaccessible. "
                "This directly contradicts the 99.9% availability target."
            ),
            confidence="red",
            score=0.08,
            evidence="'API Gateway: Node.js + Express, single instance'",
            assumptions=[],
            needs_validation=["Is there a redundancy plan for the API Gateway?"],
            recommended_action=(
                "Add a second API Gateway instance behind the existing load balancer "
                "before go-live. Minimal configuration cost; "
                "maximum impact on availability."
            ),
            category="risk",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="No timeout on CoreBanking calls: thread starvation risk",
            description=(
                "The Payment Service calls CoreBanking with no timeout configured, "
                "using the HTTP client default (typically infinite). "
                "If CoreBanking degrades, Payment Service threads will block "
                "indefinitely, exhausting the connection pool and bringing down the entire service."
            ),
            confidence="red",
            score=0.1,
            evidence="'No timeout configured for CoreBanking calls (uses HTTP client default)'",
            assumptions=[],
            needs_validation=["What is the maximum acceptable timeout for CoreBanking?"],
            recommended_action=(
                "Set an explicit 8-second timeout in the httpx client for CoreBanking. "
                "Return 503 to the client if it does not respond. This is a 2-line code change "
                "that must be made in the first sprint."
            ),
            category="risk",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="No idempotency: retries will generate duplicate payments",
            description=(
                "There is no idempotency key or transaction deduplication. "
                "If the client retries on timeout or the system auto-retries, "
                "the same payment will execute multiple times in CoreBanking. "
                "In international payments, this means real financial losses."
            ),
            confidence="red",
            score=0.12,
            evidence="'No idempotency mechanism implemented in transactions'",
            assumptions=["CoreBanking does not have its own deduplication."],
            needs_validation=["Can CoreBanking detect duplicate transactions on its own?"],
            recommended_action=(
                "Implement idempotency UUID: the client sends an `X-Idempotency-Key` header, "
                "Payment Service stores it in PostgreSQL with a 24h TTL "
                "and rejects duplicates with 409 Conflict. Industry standard, implementable in one sprint."
            ),
            category="gap",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="Synchronous notifications without queue: silent loss on SendGrid failure",
            description=(
                "SendGrid is called synchronously on each transaction completion, with no message queue or retry. "
                "If SendGrid fails (downtime, rate limit, network error), the transaction was already processed "
                "but the client receives no confirmation. The failure is silent — no alert, no retry."
            ),
            confidence="yellow",
            score=0.28,
            evidence="'Direct call to SendGrid from Payment Service on each transaction. No message queue. No retry on SendGrid failure.'",
            assumptions=["SendGrid has a 99.9% SLA, but the remaining 0.1% affects real transactions."],
            needs_validation=["Is it acceptable for a successful transaction to generate no confirmation email?"],
            recommended_action=(
                "Add a `pending_notifications` table in PostgreSQL. "
                "Payment Service inserts the record and an async worker sends the email "
                "with exponential retry. Decouples payment success from notification success."
            ),
            category="risk",
            agent_id=aid,
            agent_name=aname,
        ),
    ]
    return _result(
        aid, aname, "GitBranch", findings,
        "The proposed architecture has three production-blocking issues. "
        "First, the combination of CoreBanking latencies (2-15s) and anti-fraud (3s) makes it mathematically "
        "impossible to meet the 10-second regulatory SLA. Second, the absence of a timeout on CoreBanking calls "
        "and the lack of a circuit breaker create a cascading failure risk. "
        "Third, without idempotency, retries will certainly generate duplicate payments. "
        "Priority recommendations: async CoreBanking decoupling, explicit timeout, and idempotency key.",
        thinking=(
            "I need to validate the proposed architecture against the business requirements, "
            "focusing on correctness, resilience, and scalability.\n\n"
            "Critical math first: CoreBanking v2.1 has documented latency of 2-15 seconds. "
            "FraudShield adds ~3 seconds. At P95, total = 15s + 3s = 18 seconds. "
            "The regulatory SLA is 10 seconds. 18 > 10. "
            "This is mathematically impossible under the current synchronous architecture. "
            "This is my most critical finding — the team cannot ship without redesigning this flow. "
            "The fix is an async 202 Accepted pattern: the endpoint returns immediately with a "
            "transaction ID, and status is polled or pushed via WebSocket.\n\n"
            "API Gateway: single Node.js/Express instance, no load balancer, no redundancy. "
            "Any deployment or restart makes the system completely unavailable. "
            "The spec promises 99.9% availability — that's ~8.7 hours downtime per year. "
            "A single unplanned restart consumes a significant portion of that budget.\n\n"
            "Payment Service calls CoreBanking with no configured timeout. "
            "HTTP client default is typically infinite. If CoreBanking degrades, "
            "all threads block waiting for a response, connection pool exhausts, "
            "and the entire Payment Service goes down. Classic cascading failure.\n\n"
            "No idempotency key mechanism anywhere in the system. "
            "Combined with the undefined retry behavior from the spec, "
            "this guarantees duplicate payments on any retry scenario.\n\n"
            "SendGrid called synchronously per transaction with no queue. "
            "If SendGrid fails (0.1% downtime), the transaction was already processed "
            "but the client receives no email confirmation. Silent failure."
        ),
    )


# ── Agent 3: Risk Intelligence ────────────────────────────────────────────────


def _risk_intelligence() -> AgentResult:
    aid, aname = "risk_intelligence", "Risk Intelligence"
    findings = [
        _f(
            title="No circuit breaker to CoreBanking: guaranteed cascading failure",
            description=(
                "There is no circuit breaker between the Payment Service and CoreBanking. "
                "If CoreBanking degrades or goes down, all payment requests will block "
                "waiting, exhausting the Payment Service connection pool and bringing down "
                "the entire platform — not just international payments."
            ),
            confidence="red",
            score=0.07,
            evidence="'No retry logic implemented' and 'no timeout configured' imply the absence of a circuit breaker.",
            assumptions=["CoreBanking has a history of degradations as a legacy system."],
            needs_validation=["Is there a documented internal SLA for CoreBanking?"],
            recommended_action=(
                "Implement circuit breaker with Tenacity (Python): 5 consecutive failures open the circuit "
                "for 30 seconds and return immediate 503 to the client. "
                "Implementable in one day; prevents a CoreBanking failure from bringing down the entire platform."
            ),
            category="risk",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="PCI-DSS Level 1 declared but account data encryption not defined",
            description=(
                "The spec prohibits storing IBAN/SWIFT in plaintext but does not define: "
                "encryption algorithm, key management, encryption in transit between internal services, "
                "or tokenization. Without this definition, PCI-DSS compliance cannot be verified "
                "and the system will fail a security audit."
            ),
            confidence="red",
            score=0.1,
            evidence="'SWIFT/IBAN account data cannot be stored in plaintext.' — no specification of how to protect it.",
            assumptions=[],
            needs_validation=[
                "Is tokenization or symmetric encryption used for IBAN/SWIFT?",
                "Who manages the encryption keys?",
                "Is data encrypted in transit between Payment Service and CoreBanking?",
            ],
            recommended_action=(
                "Urgent meeting with the security team this week. "
                "Define: AES-256-GCM for IBAN/SWIFT at-rest encryption, keys in HashiCorp Vault. "
                "Block go-live until formal approval from the legal and security teams."
            ),
            category="risk",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="No rate limiting on the API Gateway",
            description=(
                "The API Gateway does not implement rate limiting. With projected peaks of 500 TPS "
                "and 300% growth, a malicious actor or client error could generate "
                "arbitrary load on the legacy CoreBanking, which was not designed to absorb "
                "uncontrolled traffic."
            ),
            confidence="yellow",
            score=0.32,
            evidence="'Rate limiting not yet implemented'",
            assumptions=["CoreBanking does not have its own rate limiting."],
            needs_validation=["What is the maximum TPS that CoreBanking can absorb?"],
            recommended_action=(
                "Add rate limiting in Express with `express-rate-limit`: "
                "100 req/min per JWT token. Implementable in 4 hours. "
                "Protects CoreBanking from accidental or malicious bursts."
            ),
            category="risk",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="No transactional rollback strategy",
            description=(
                "If the payment executes successfully in CoreBanking but the write "
                "to the local NovaBank database fails (or the notification fails), the system enters "
                "an inconsistent state: the money left but the system did not record it. "
                "There is no compensation mechanism or automatic reconciliation defined."
            ),
            confidence="red",
            score=0.14,
            evidence="No mention of distributed transactions, sagas, or compensation mechanisms in the entire architecture.",
            assumptions=[
                "Oracle 11g does not support distributed transactions with the Payment Service.",
            ],
            needs_validation=[
                "Is there a manual reconciliation process with CoreBanking?",
                "How is a ghost transaction detected and resolved?",
            ],
            recommended_action=(
                "Document the manual reconciliation procedure before go-live — "
                "who runs it, when, and how an inconsistent transaction is detected. "
                "For the next sprint: evaluate the Saga pattern with automatic compensations."
            ),
            category="risk",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="Audit traceability required but implementation not specified",
            description=(
                "The spec requires 'full traceability' for compliance, but does not define: "
                "which events are recorded (start, anti-fraud validation, execution, notification), "
                "audit log format, retention period, or log integrity "
                "(a log that can be modified does not meet financial regulation)."
            ),
            confidence="yellow",
            score=0.38,
            evidence="'All transactions must be audited with full traceability.'",
            assumptions=["LATAM regulation requires immutable logs with certified timestamps."],
            needs_validation=[
                "What is the minimum audit retention period per regulation?",
                "Must logs be immutable (append-only)?",
            ],
            recommended_action=(
                "Create an append-only `audit_log` table in PostgreSQL: "
                "timestamp, transaction_id, event_type, actor, payload. "
                "Review with Legal the required retention period (minimum 5 years in several LATAM markets) "
                "before go-live."
            ),
            category="gap",
            agent_id=aid,
            agent_name=aname,
        ),
    ]
    return _result(
        aid, aname, "Shield", findings,
        "The risk analysis identifies critical security and resilience vulnerabilities. "
        "The most severe risk is the absence of a circuit breaker to the legacy CoreBanking, "
        "which guarantees a cascading failure at the first legacy system degradation. "
        "Second, PCI-DSS compliance is declared but not implemented: "
        "there is no encryption definition for IBAN/SWIFT data or key management. "
        "Additionally, the lack of transactional rollback will create data inconsistencies "
        "from the first production incident.",
    )


# ── Agent 4: Business Impact ──────────────────────────────────────────────────


def _business_impact() -> AgentResult:
    aid, aname = "business_impact", "Business Impact"
    findings = [
        _f(
            title="Regulatory SLA non-compliance: quantifiable fines from day one",
            description=(
                "Since the architecture cannot meet the 10-second SLA (per Architecture Validator analysis), "
                "NovaBank will be in regulatory non-compliance from launch. "
                "In LATAM markets, fines for instant payment SLA violations range from $50K to $500K USD "
                "per quarter. The cost of redesigning the architecture now is less than the first fine."
            ),
            confidence="red",
            score=0.09,
            evidence="Regulatory SLA of 10s + architectural latencies of 5-18s = structural non-compliance.",
            assumptions=["LATAM regulators enforce fines for SLA violations in instant payments."],
            needs_validation=[
                "What is the applicable fine regime in each target market?",
                "Is there a regulatory grace period for new entrants?",
            ],
            recommended_action=(
                "Present this analysis to stakeholders before approving the MVP. "
                "The cost of the architectural redesign (2-3 sprints) is less than the first fine. "
                "Prioritize async architecture with 202 Accepted response."
            ),
            category="cost",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="300% growth with on-premise infrastructure: uncapped operational cost",
            description=(
                "The projected 300% growth in 6 months with manual on-premise deployment "
                "implies hiring and provisioning physical hardware multiple times. "
                "The marginal cost per capacity unit on-premise is 3-5x higher than cloud "
                "at this growth rate. Additionally, provisioning time (weeks) "
                "cannot follow demand peaks."
            ),
            confidence="red",
            score=0.13,
            evidence="'Current infrastructure: on-premise, no container orchestration, manual scaling.'",
            assumptions=["300% growth is the base scenario, not the optimistic one."],
            needs_validation=["Is there an approved budget for scaling infrastructure?"],
            recommended_action=(
                "Define in the post-MVP roadmap an explicit cloud migration trigger (e.g., at 100 TPS). "
                "Include a comparative TCO analysis cloud vs. on-premise "
                "before growth makes the migration urgent and costly."
            ),
            category="cost",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="User-visible latency impacts conversion against competitors",
            description=(
                "Wise and Remitly offer confirmation in under 3 seconds. "
                "With the current architecture, NovaBank will show wait times of 5-18 seconds. "
                "UX studies in payments show 40% abandonment for every 3 additional seconds of wait. "
                "This directly impacts product adoption rate."
            ),
            confidence="yellow",
            score=0.35,
            evidence="Documented latencies: CoreBanking 2-15s + FraudShield 3s vs. Wise/Remitly <3s.",
            assumptions=["Corporate users have alternatives available (Wise Business, Remitly for Business)."],
            needs_validation=["What is the acceptable abandonment rate for the product team?"],
            recommended_action=(
                "Implement immediate 202 Accepted response with a 'processing' status UI "
                "and progress bar. The user perceives speed even if the backend takes 10s. "
                "This change requires the async redesign but has the greatest UX impact."
            ),
            category="cost",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="Oracle 11g technical debt will block product evolution in 6 months",
            description=(
                "Oracle 11g (officially unsupported since 2013) does not support modern distributed transactions "
                "or native JSON. Every subsequent feature requiring new queries or schemas "
                "will involve costly workarounds or an unplanned migration. "
                "Migration cost grows exponentially with data volume."
            ),
            confidence="yellow",
            score=0.4,
            evidence="'Account database is on Oracle 11g (does not support modern distributed transactions)'",
            assumptions=["Data volume will grow with the projected 300% growth."],
            needs_validation=["Is there a migration roadmap for Oracle 11g?"],
            recommended_action=(
                "Create an abstraction layer (Repository pattern) over Oracle 11g from day one. "
                "This isolates the technical debt, facilitates the future migration, "
                "and requires no additional development time — just architectural discipline."
            ),
            category="cost",
            agent_id=aid,
            agent_name=aname,
        ),
    ]
    return _result(
        aid, aname, "TrendingUp", findings,
        "The business impact analysis identifies direct and quantifiable financial risks. "
        "The most urgent: the architecture guarantees regulatory SLA non-compliance, "
        "with potential fines exceeding the project cost from the first quarter. "
        "The projected 300% growth is incompatible with the current on-premise infrastructure, "
        "creating a scaling ceiling that will arrive before the product reaches profitability. "
        "This analysis should be presented to business stakeholders before approving the MVP.",
    )


# ── Agent 5: Accessibility Advocate ──────────────────────────────────────────


def _accessibility_advocate() -> AgentResult:
    aid, aname = "accessibility_advocate", "Accessibility Advocate"
    findings = [
        _f(
            title="Polling without aria-live: screen reader users receive no status updates",
            description=(
                "Payment status is updated via polling every 3 seconds, "
                "but without aria-live regions, status changes are invisible to screen readers. "
                "A visually impaired user will not know their payment was processed until they "
                "manually explore the page, violating WCAG 2.1 criterion 4.1.3 (Status Messages)."
            ),
            confidence="red",
            score=0.12,
            evidence="'React SPA with polling every 3 seconds to update payment status' — no mention of aria-live.",
            assumptions=[],
            needs_validation=["Does the payment status component have aria-live='polite' or aria-atomic?"],
            recommended_action=(
                "Add `aria-live='polite'` to the payment status container. "
                "When status changes, update the element's text so screen readers announce it. "
                "This is a 10-minute change that resolves a critical WCAG 4.1.3 gap."
            ),
            category="accessibility",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="Mobile-last design excludes most-used assistive technologies",
            description=(
                "The spec defines the design 'primarily for desktop' with mobile as a future improvement. "
                "In LATAM, 68% of assistive technologies are used on mobile devices. "
                "A corporate payment system inaccessible on mobile excludes users with "
                "motor disabilities using switches, low-vision users who magnify their phone screen, "
                "and TalkBack/VoiceOver users on Android/iOS."
            ),
            confidence="red",
            score=0.15,
            evidence="'Designed primarily for desktop; mobile as future improvement'",
            assumptions=["Corporate clients in LATAM frequently authorize payments from mobile."],
            needs_validation=[
                "What percentage of users access from mobile in the target B2B segment?",
            ],
            recommended_action=(
                "Include responsive design from the first MVP component. "
                "The cost of retrofitting responsive is 5-10x higher than building it from the start. "
                "Elena should review mockups before the team begins frontend development."
            ),
            category="accessibility",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="PDF receipt without document accessibility specification",
            description=(
                "The spec mentions 'confirmation email with PDF receipt' without specifying "
                "whether the PDF complies with PDF/UA (ISO 14289). An untagged PDF is unreadable by "
                "screen readers. In a financial context, an inaccessible receipt "
                "may have legal implications in markets with accessibility regulation."
            ),
            confidence="yellow",
            score=0.38,
            evidence="'Confirmation email with PDF receipt'",
            assumptions=["The PDF is generated programmatically, not a scanned document."],
            needs_validation=[
                "Does the PDF generator support semantic tagging (PDF/UA)?",
                "Do target markets have accessibility regulation for financial documents?",
            ],
            recommended_action=(
                "Use a PDF generation library with PDF/UA support: ReportLab with tagging or WeasyPrint. "
                "Add as acceptance criterion in US-003: "
                "'The confirmation PDF must be readable by screen readers (PDF/UA).'"
            ),
            category="accessibility",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="Payment error messages: visual dependency not defined",
            description=(
                "The spec mentions error notifications but does not define whether error messages "
                "use only red color to indicate failure. If so, this violates WCAG 1.4.1 (Use of Color). "
                "Error messages must include an icon or text that does not rely on color alone, "
                "and must be marked with role='alert' for screen readers."
            ),
            confidence="yellow",
            score=0.42,
            evidence="'In case of failure, the system must indicate what to do next' — no accessible design specification.",
            assumptions=["The design team does not have defined accessibility guidelines yet."],
            needs_validation=["Are there error state mockups available to review?"],
            recommended_action=(
                "Define in the design system: error messages include icon + descriptive text, not just red color. "
                "Add `role='alert'` and `aria-live='assertive'` to the error component. "
                "This combination satisfies WCAG 1.4.1 and 4.1.3 simultaneously."
            ),
            category="accessibility",
            agent_id=aid,
            agent_name=aname,
        ),
    ]
    return _result(
        aid, aname, "Eye", findings,
        "The accessibility analysis identifies four gaps against WCAG 2.1 AA. "
        "The most critical: polling status updates will not be announced to screen readers, "
        "leaving visually impaired users without information about the outcome of their payments. "
        "Additionally, the mobile-last approach excludes the majority of assistive technology users in LATAM. "
        "These issues are significantly cheaper to fix in design than in code — "
        "Elena should review the mockups before the team begins frontend development.",
    )


# ── Agent 6: Delivery Historian ───────────────────────────────────────────────


def _delivery_historian() -> AgentResult:
    aid, aname = "delivery_historian", "Delivery Historian"
    findings = [
        _f(
            title="No idempotency in payments: this pattern caused 900K duplicates in production",
            description=(
                "In 2019, a European bank processed 900,000 duplicate payments in a 4-hour incident "
                "caused by exactly this pattern: retries without idempotency keys over a "
                "synchronous payment gateway. Recovery took 3 weeks and cost €12M in reversals. "
                "The current NovaBank architecture reproduces this antipattern exactly."
            ),
            confidence="red",
            score=0.08,
            evidence="'No idempotency mechanism implemented in transactions.' 'No retry logic implemented.'",
            assumptions=[],
            needs_validation=[
                "Can CoreBanking detect duplicates on its own using some reference field?",
            ],
            recommended_action=(
                "Implement idempotency keys BEFORE the first production deploy. "
                "Pattern: UUID in `X-Idempotency-Key` header, stored in DB with 24h TTL, "
                "reject duplicates with 409 Conflict. This is not a future improvement — it is a safety requirement."
            ),
            category="pattern",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="Thread starvation from synchronous calls to legacy: cascading failure pattern",
            description=(
                "Thread starvation from synchronous calls to slow systems is one of the most "
                "documented failure patterns in microservice architectures. Amazon described this antipattern "
                "in their 2004 post-mortem as the origin of circuit breaker design in AWS. "
                "Without a timeout or circuit breaker, the first CoreBanking incident will bring down the entire platform."
            ),
            confidence="red",
            score=0.1,
            evidence="'No timeout configured for CoreBanking calls (uses HTTP client default)'",
            assumptions=["CoreBanking has a history of degradations as a legacy on-premise system."],
            needs_validation=["What is the historical availability of CoreBanking over the last 12 months?"],
            recommended_action=(
                "Implement explicit timeout and circuit breaker this week — they are independent changes "
                "that can be done in parallel in the first sprint. "
                "There is no justification for not having them from day one."
            ),
            category="pattern",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="Legacy SWIFT integration in 6 weeks: historically takes double the estimate",
            description=(
                "Integration with legacy SWIFT gateways has a consistent history of taking "
                "double the estimated time. The 'last 10%' — handling edge-case formats, "
                "undocumented errors, security certifications — typically consumes "
                "50% of total effort. Priya and Daniel must plan with this factor in mind."
            ),
            confidence="yellow",
            score=0.35,
            evidence="'The SWIFT CoreBanking v2.1 gateway is a synchronous system' — integration in 6 total weeks.",
            assumptions=["The team has no prior experience with CoreBanking v2.1."],
            needs_validation=[
                "Is complete CoreBanking technical documentation available from day one?",
                "Is there a sandbox/staging CoreBanking environment for testing?",
            ],
            recommended_action=(
                "Get access to the CoreBanking UAT environment on sprint day one. "
                "If not available in the first week, escalate immediately: "
                "this is the project's greatest timeline risk."
            ),
            category="pattern",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="Manual deployment on a critical financial system: second leading cause of production incidents",
            description=(
                "Human errors in manual deployments are the second most common cause of production incidents "
                "in financial systems (after configuration changes). "
                "A poorly executed deploy on an active payment system can leave in-flight transactions "
                "in an undefined state. Marcus must include deployment automation "
                "as a requirement, not a future improvement."
            ),
            confidence="yellow",
            score=0.38,
            evidence="'Deployment on on-premise VMs. No container orchestration. Manual scaling.'",
            assumptions=["The team will perform multiple deploys during the 6 weeks of development."],
            needs_validation=[
                "Is there a defined rollback process for the payment system in production?",
            ],
            recommended_action=(
                "Implement basic CI/CD with GitHub Actions in the first sprint: "
                "automated tests on PR + automatic deploy to staging. "
                "Production deploy can remain manual, but with a validated script and documented rollback."
            ),
            category="pattern",
            agent_id=aid,
            agent_name=aname,
        ),
    ]
    return _result(
        aid, aname, "History", findings,
        "The historical analysis identifies that NovaBank is reproducing three well-documented "
        "failure patterns from the fintech industry. The most urgent: the absence of idempotency "
        "in a system with retries is the same pattern that caused 900,000 duplicate payments "
        "at a European bank in 2019. The recommendation is clear: implementing idempotency and "
        "a circuit breaker are non-negotiable requirements before launch. "
        "Additionally, the 6-week estimate for the legacy SWIFT integration is optimistic — "
        "Marcus should plan with a 100% buffer for the CoreBanking integration.",
    )


# ── Consolidator mock ─────────────────────────────────────────────────────────


def get_mock_consolidation() -> ConsolidatorResult:
    """Pre-generated ConsolidatorResult for the NovaBank demo case."""
    return ConsolidatorResult(
        contradictions=[
            Contradiction(
                topic="CoreBanking timeout: spec gap vs. engineering gap",
                agents=["spec_analyst", "arch_validator"],
                description=(
                    "Spec Analyst flags an undefined timeout behavior as a product gap — "
                    "the spec says nothing about what happens when CoreBanking exceeds the SLA. "
                    "Arch Validator flags the same scenario as an engineering risk: "
                    "no HTTP timeout is configured on the client, causing thread starvation. "
                    "Both assign RED but assign responsibility to different layers."
                ),
                resolution=(
                    "Both findings are valid and complementary, not contradictory. "
                    "Spec Analyst's finding is the prerequisite: engineers cannot implement "
                    "the correct timeout behavior without a product decision first. "
                    "Prioritize Spec Analyst's as the blocker; Arch Validator's "
                    "8-second httpx timeout is the immediate implementation action once "
                    "the product decision is made."
                ),
            ),
        ],
        confirmed_criticals=[
            ConfirmedCritical(
                topic="No idempotency — duplicate payment risk",
                agents=["arch_validator", "delivery_historian"],
                combined_evidence=(
                    "Arch Validator: 'No idempotency mechanism implemented in transactions — "
                    "retries will generate duplicate payments in CoreBanking.' "
                    "Delivery Historian independently corroborates with a documented incident: "
                    "a 2019 European bank produced 900,000 duplicate payments from exactly this "
                    "pattern — synchronous gateway + retries + no idempotency key. "
                    "Recovery took 3 weeks and cost EUR 12M in reversals."
                ),
            ),
            ConfirmedCritical(
                topic="CoreBanking cascading failure — no timeout or circuit breaker",
                agents=["arch_validator", "risk_intelligence", "delivery_historian"],
                combined_evidence=(
                    "Three agents independently flagged this as a production blocker. "
                    "Arch Validator: no timeout configured, thread starvation will bring down Payment Service. "
                    "Risk Intelligence: no circuit breaker means any CoreBanking degradation "
                    "cascades to the entire platform. "
                    "Delivery Historian: Amazon's 2004 post-mortem on this exact pattern "
                    "led to the invention of circuit breaker design."
                ),
            ),
            ConfirmedCritical(
                topic="Regulatory SLA violation guaranteed by architecture",
                agents=["arch_validator", "business_impact"],
                combined_evidence=(
                    "Arch Validator proves mathematically: CoreBanking (2-15s) + FraudShield (3s) "
                    "= 5-18s total, exceeding the 10-second regulatory SLA at P95 under normal load. "
                    "Business Impact quantifies the exposure: $50K-$500K USD in fines per quarter "
                    "from launch day. The cost of the async redesign (2-3 sprints) is less than "
                    "the first fine."
                ),
            ),
        ],
        redundancies=[
            Redundancy(
                topic="CoreBanking thread starvation and cascading failure",
                agents=["arch_validator", "risk_intelligence", "delivery_historian"],
                kept="risk_intelligence",
            ),
            Redundancy(
                topic="No idempotency in payment processing",
                agents=["arch_validator", "delivery_historian"],
                kept="delivery_historian",
            ),
        ],
        audit_summary=(
            "The cross-agent audit confirms three production blockers independently corroborated "
            "by multiple agents. Immediate actions required before any code reaches production: "
            "(1) Implement idempotency keys with X-Idempotency-Key header and PostgreSQL "
            "deduplication — failure to do so will replicate the 900K duplicate payment incident. "
            "(2) Add an explicit 8-second timeout and circuit breaker to all CoreBanking calls — "
            "no single engineering change has higher risk-mitigation value in this system. "
            "(3) Redesign to async 202 Accepted pattern — the synchronous architecture cannot "
            "meet the regulatory SLA under any realistic load. These three changes must be treated "
            "as Sprint 0 prerequisites, not backlog items."
        ),
    )

