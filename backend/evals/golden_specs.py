"""Golden spec definitions for regression evals.

Each GoldenSpec is a synthetic product spec with deliberately planted issues.
DetectionCriteria describes what a good agent MUST catch, specified as:
  - keywords: at least one must appear (case-insensitive) in any finding
    title or description produced by the named agent_id
  - agent_id: which agent is expected to detect this (None = any agent)
  - confidence: expected confidence level (informational only)

The recall threshold (min_recall) is the minimum fraction of criteria that
must be detected for the spec to PASS. Failing to meet it exits non-zero.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DetectionCriteria:
    """A single expected detection for a golden spec."""

    label: str
    keywords: list[str]
    agent_id: str | None = None  # None = accept match from any agent
    confidence: str = "red"


@dataclass
class GoldenSpec:
    """A curated spec with known issues and the agents needed to find them."""

    name: str
    description: str
    spec: str
    architecture: str
    criteria: list[DetectionCriteria]
    # Agents to run (only these are called during the eval)
    agents_to_run: list[str] = field(default_factory=lambda: ["spec_analyst"])
    min_recall: float = 0.60


# ── Golden Spec 1: SimpleBank Wire Transfer ───────────────────────────────────

_SIMPLEBANK_SPEC = """\
# SimpleBank Wire Transfer API — Product Spec v1.0

## Overview
SimpleBank provides a B2B wire transfer service enabling corporate clients to
send international payments via SWIFT.

## User Stories

### US-001: Initiate Wire Transfer
As a corporate treasurer, I want to initiate international wire transfers
so that I can pay overseas vendors and suppliers.

Acceptance Criteria:
- User enters: amount, currency, beneficiary IBAN, BIC/SWIFT code, and
  reference note
- System validates all fields before submission
- Transfer must complete in under 5 seconds
- On success, show confirmation screen with transaction reference number

### US-002: Transfer Status Tracking
As a corporate treasurer, I want to see the current status of my transfers
so that I can track whether payments have been received.

Acceptance Criteria:
- Status updates automatically without page refresh
- Statuses: Pending | Processing | Completed | Failed

### US-003: Transfer Failure Handling
As a corporate treasurer, I want to be notified when a transfer fails
so that I can take corrective action.

Acceptance Criteria:
- Display an error message when the transfer fails
- Provide guidance on what to do next

## Technical Notes
- Integration with GlobalPay SWIFT gateway (synchronous calls, 3-12s latency)
- PostgreSQL for local transaction records
- SendGrid for email notifications
- Retry behaviour: not yet defined
"""

_SIMPLEBANK_ARCH = """\
- API Gateway: Node.js/Express (single instance)
- Payment Service: Python/FastAPI
- Database: PostgreSQL 14 (single instance, no replication)
- SWIFT Integration: GlobalPay SDK — synchronous, 3-12 second response time
- Anti-fraud: RiskCheck service, synchronous, ~2 second average latency
- Email: SendGrid (direct call from Payment Service, no queue)
- No timeout configured on GlobalPay SDK calls
- No idempotency key mechanism in the current implementation
- No circuit breaker or retry logic implemented
"""

_SIMPLEBANK_CRITERIA = [
    DetectionCriteria(
        label="5-second SLA is architecturally impossible (3-12s gateway + 2s anti-fraud)",
        keywords=["5 second", "5-second", "SLA", "impossible", "latency", "synchronous",
                  "3-12", "exceed", "mathematically"],
        agent_id="arch_validator",
        confidence="red",
    ),
    DetectionCriteria(
        label="Missing idempotency — retries will generate duplicate transfers",
        keywords=["idempoten", "duplicate", "dedupl"],
        agent_id=None,  # spec_analyst, arch_validator, or delivery_historian may catch this
        confidence="red",
    ),
    DetectionCriteria(
        label="US-003 failure handling vague: 'what to do next' not defined",
        keywords=["what to do", "next step", "failure", "error", "US-003", "vague",
                  "undefined", "not defined", "action"],
        agent_id="spec_analyst",
        confidence="red",
    ),
    DetectionCriteria(
        label="No timeout on GlobalPay gateway calls: thread starvation risk",
        keywords=["timeout", "time-out", "thread", "starvation", "blocking", "hung",
                  "GlobalPay", "circuit"],
        agent_id=None,
        confidence="red",
    ),
]

SIMPLEBANK = GoldenSpec(
    name="SimpleBank Wire Transfer",
    description="B2B wire transfer spec with planted SLA impossibility, missing idempotency, "
                "no timeout, and vague failure story",
    spec=_SIMPLEBANK_SPEC,
    architecture=_SIMPLEBANK_ARCH,
    criteria=_SIMPLEBANK_CRITERIA,
    agents_to_run=["spec_analyst", "arch_validator", "delivery_historian"],
    min_recall=0.60,
)


# ── Golden Spec 2: MediPay Healthcare Billing ─────────────────────────────────

_MEDIPAY_SPEC = """\
# MediPay Healthcare Billing Portal — Spec v2.1

## Overview
MediPay enables clinics and hospitals to collect patient payments online.
The system handles sensitive patient billing data and must comply with
PCI-DSS requirements.

## User Stories

### US-001: Pay Invoice
As a patient, I want to pay my clinic invoice online so that I can settle
balances without visiting in person.

Acceptance Criteria:
- Patient enters: invoice number and payment card details
- System processes payment via PayFlow gateway
- On success: display confirmation with receipt number
- On failure: display an error message and allow the patient to retry

### US-002: Export Billing History
As a clinic administrator, I want to export patient billing history as a
CSV file so that I can submit records to insurance providers and auditors.

Acceptance Criteria:
- Administrator selects a date range
- System downloads a CSV file to the administrator's computer

### US-003: Password Reset
As a patient or clinic administrator, I want to reset my password via email
so that I can regain access to my account if I forget my credentials.

Acceptance Criteria:
- User enters email address → system sends a password reset link
- Link expires after 24 hours

## Compliance
- The system is PCI-DSS compliant
- Patient data must be protected at all times

## Technical Notes
- PayFlow payment gateway (synchronous, average 1.5 second latency)
- React SPA frontend with React Router
- Python/FastAPI backend
- PostgreSQL for patient and billing records
"""

_MEDIPAY_ARCH = """\
- Frontend: React SPA, deployed on S3/CloudFront
- Backend: FastAPI (Python), single EC2 instance
- Database: PostgreSQL (patient records, billing, users)
- Payment: PayFlow SDK — synchronous integration
- No retry mechanism or idempotency key for PayFlow calls
- Email: AWS SES (direct call, no queue)
- Auth: JWT tokens, 24-hour expiry
- No rate limiting configured on any endpoint
- No field-level encryption defined for stored card or patient data
"""

_MEDIPAY_CRITERIA = [
    DetectionCriteria(
        label="CSV export has no field specification or data masking for patient data",
        keywords=["CSV", "export", "field", "mask", "patient", "sensitive", "PHI",
                  "PII", "IBAN", "account", "complian"],
        agent_id="spec_analyst",
        confidence="yellow",
    ),
    DetectionCriteria(
        label="Password reset has no rate limiting — brute-force / account enumeration risk",
        keywords=["rate limit", "rate-limit", "throttl", "brute", "enumerat", "reset",
                  "password", "attempt", "abuse"],
        agent_id="risk_intelligence",
        confidence="yellow",
    ),
    DetectionCriteria(
        label="On-failure retry without idempotency will cause duplicate payments",
        keywords=["idempoten", "duplicate", "retry", "dedupl"],
        agent_id=None,
        confidence="red",
    ),
    DetectionCriteria(
        label="PCI-DSS declared but encryption and key management not specified",
        keywords=["PCI", "encrypt", "key", "token", "plaintext", "complian",
                  "card", "implement"],
        agent_id="risk_intelligence",
        confidence="red",
    ),
]

MEDIPAY = GoldenSpec(
    name="MediPay Healthcare Billing",
    description="Healthcare billing portal with planted PCI gap, missing idempotency, "
                "no rate limiting on password reset, and incomplete CSV spec",
    spec=_MEDIPAY_SPEC,
    architecture=_MEDIPAY_ARCH,
    criteria=_MEDIPAY_CRITERIA,
    agents_to_run=["spec_analyst", "risk_intelligence", "arch_validator"],
    min_recall=0.60,
)


# ── Registry ──────────────────────────────────────────────────────────────────

GOLDEN_SPECS: list[GoldenSpec] = [SIMPLEBANK, MEDIPAY]
