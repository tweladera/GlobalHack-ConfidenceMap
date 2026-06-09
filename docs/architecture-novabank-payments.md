# Technical Architecture Document
## NovaBank — Instant International Payments
### RFC-2024-47 · Revision 1.3

**Author:** Daniel Reyes, Senior Software Architect
**Reviewers:** Sofia Chen (Product), Priya Kapoor (QA Lead), Marcus Torres (Delivery Lead)
**Status:** Approved for implementation
**Date:** 2024-11-08
**Delivery target:** 6 weeks (sprint 1 starts 2024-11-11)

---

## 1. Context and objective

NovaBank needs to enable instant international payments for its corporate segment in LATAM. The system must process SWIFT/IBAN transfers with user confirmation in under 10 seconds, complying with local regulation and PCI-DSS level 1.

This document describes the proposed architecture for the MVP, the design decisions made, and the components involved.

**Non-negotiable constraints:**
- Use the existing CoreBanking v2.1 gateway (legacy system, on-premise)
- Do not migrate the accounts database (Oracle 11g)
- On-premise infrastructure without Kubernetes
- 6-week timeline for the first release

---

## 2. System overview

```
[Web Client]
     |
     | HTTPS
     v
[API Gateway]  <-- JWT Auth -->  [Auth Service (existing)]
     |
     | HTTP internal
     v
[Payment Service]
     |         |              |
     v         v              v
[CoreBanking] [FraudShield]  [PostgreSQL]
  (SWIFT v2.1) (external)    (transactions)
     |
     v
[Oracle 11g]  <- read-only
(accounts)

[Payment Service] --> [SendGrid] (email notifications)
```

**Main payment flow:**

1. Client sends `POST /api/payments` with amount, currency, destination IBAN
2. API Gateway validates JWT and routes to Payment Service
3. Payment Service queries Oracle 11g to validate source account (balance)
4. Payment Service calls FraudShield for anti-fraud validation
5. If FraudShield approves, CoreBanking gateway is called to execute the SWIFT transfer
6. CoreBanking returns confirmation (or error)
7. Payment Service persists the result in PostgreSQL
8. Payment Service calls SendGrid to send confirmation email
9. Response returned to client

---

## 3. Components and design decisions

### 3.1 Frontend — React SPA

**Technology:** React 18, TypeScript, Axios
**Hosting:** Nginx on on-premise VM

**Decisions:**
- Classic SPA, no SSR (next.js discarded for deployment simplicity)
- Payment status updates via **HTTP polling every 3 seconds** to the `GET /api/payments/{id}/status` endpoint
- WebSockets discarded for the MVP: the internal network infrastructure has no persistent connection support enabled without additional configuration changes out of scope for the platform team
- Responsive design targeting desktop; mobile version defined as post-MVP improvement in the roadmap

**Accessibility:**
- Semantic HTML will be used
- Status colors (green/red/yellow) have text labels accompanying each indicator
- No formal WCAG audit has been performed; planned for Q1 2025

### 3.2 API Gateway — Node.js + Express

**Technology:** Node.js 20 LTS, Express 4, jsonwebtoken
**Deployment:** Dedicated VM, single instance

**Decisions:**
- Express chosen for team familiarity; alternatives like Fastify or Kong discarded due to learning curve
- JWT validation with shared secret key (HS256); key rotation planned post-MVP
- The API Gateway acts as a single entry point: handles CORS, request logging, and internal routing
- **Rate limiting:** not implemented in this MVP. Assumed that initial volume (pilot with 20 corporate clients) doesn't require it. Will be reviewed before mass rollout
- No health check endpoint implemented yet (pending before go-live)
- Scaling: single instance. If needed, a second instance is added manually and the existing load balancer is configured

### 3.3 Payment Service — Python + FastAPI

**Technology:** Python 3.11, FastAPI, SQLAlchemy, httpx
**Deployment:** Dedicated VM, 2 instances (active-active manual)

**Detailed internal flow:**

```python
# Main endpoint pseudocode
async def create_payment(request):
    # 1. Validate funds in Oracle (direct read)
    balance = await oracle_client.get_balance(account_id)
    if balance < request.amount:
        raise InsufficientFundsError()

    # 2. Call FraudShield (synchronous, average 3s)
    fraud_result = await fraudshield_client.check(request)
    if fraud_result.is_fraud:
        raise FraudDetectedError()

    # 3. Execute in CoreBanking (synchronous, 2-15s)
    banking_result = await corebanking_client.execute(request)

    # 4. Persist in PostgreSQL
    await db.save_transaction(banking_result)

    # 5. Notify by email
    await sendgrid_client.send_confirmation(request.user_email, banking_result)

    return banking_result
```

**Decisions and considerations:**
- FraudShield and CoreBanking calls are **sequential and synchronous**. Parallelization was evaluated but FraudShield must run before CoreBanking per compliance policy
- **Timeouts:** default HTTP client (httpx) is used. No explicit timeouts have been configured; it is assumed that the external providers' SLAs are sufficient guarantee
- **Retry:** not implemented in this MVP. If CoreBanking fails, the error propagates directly to the client. The manual reconciliation procedure will be documented
- **Idempotency:** there is no idempotency key in transactions. If the client resends a request due to a network timeout, a duplicate payment could be generated. This risk is accepted for the MVP given the low pilot volume
- **Circuit breaker:** not implemented. If CoreBanking degrades, the Payment Service will keep making calls until FastAPI workers are exhausted

### 3.4 CoreBanking Gateway (legacy)

**System:** NovaBank-owned, on-premise, Infrastructure team
**API:** Synchronous REST over internal HTTPS
**Latency:** Variable, documented between 2 and 15 seconds per transaction
**Internal SLA:** Not formally documented. Infrastructure team indicates "high availability" without specific metrics

**Known risks:**
- It is the only path to execute SWIFT transfers; there is no alternative route
- There is no staging environment equivalent to production; integration tests will be run against the UAT environment which has synthetic data and different latencies

### 3.5 Database — PostgreSQL + Oracle 11g

**PostgreSQL 15:** stores Payment Service transactions
**Oracle 11g:** existing accounts database, read-only from the new system

**Decisions:**
- Oracle is not migrated for the MVP; reads are direct via JDBC (using the `cx_Oracle` driver)
- PostgreSQL on a dedicated VM, no read replica for the MVP
- PostgreSQL backups are the responsibility of the Infrastructure team (existing manual daily process)
- **Distributed transactions:** not implemented. If the payment is successful in CoreBanking but the write to PostgreSQL fails, the state will be inconsistent. The manual reconciliation process will cover this case

### 3.6 Notifications — SendGrid

**Technology:** SendGrid REST API (Essentials plan)
**Integration:** Direct call from Payment Service upon completing each transaction

**Decisions:**
- No intermediate message queue; the call is synchronous within the payment flow
- If SendGrid fails (outage, rate limit), the transaction has already been executed in CoreBanking but the client won't receive the confirmation email. No retry or pending email registry
- In-app notifications (mentioned in the PRD) will be implemented in the next iteration; for the MVP only email is supported

---

## 4. Infrastructure and deployment

**Environment:** On-premise, NovaBank LATAM data center
**Orchestration:** None (individual VMs, systemd for process management)

| Component       | VM          | CPU  | RAM  | Instances |
|----------------|-------------|------|------|-----------|
| API Gateway    | api-gw-01   | 4c   | 8GB  | 1         |
| Payment Service| pay-svc-01  | 8c   | 16GB | 2 (manual)|
| PostgreSQL     | db-pay-01   | 8c   | 32GB | 1         |
| Frontend       | web-01      | 2c   | 4GB  | 1         |

**Deployment strategy:**
- Manual deployment via bash scripts coordinated by Marcus
- No automated CI/CD pipeline for this project (the existing infrastructure one will be adapted)
- Rollback involves restoring the previous artifact version and restarting the service via systemd
- VMs are on the same internal VLAN; no network segmentation between components

**Capacity estimate for the pilot:**
- 20 corporate clients
- Estimated peak: 50 transactions per hour on month-end closing days
- The 10-second regulatory SLA is assumed achievable with the proposed architecture

*Note: The PRD mentions support for 500 transactions per minute. This corresponds to the mass-scale phase post-pilot and is out of scope for this architecture.*

---

## 5. Security and compliance

**Authentication:** JWT HS256 with shared key between API Gateway and internal services
**Transport:** TLS 1.2 on all external communications
**Sensitive data storage:** IBAN/SWIFT numbers are stored in PostgreSQL; encryption at rest is pending implementation by the Infrastructure team
**Audit:** All transactions are logged in PostgreSQL with timestamp and user
**PCI-DSS:** The legal team is evaluating which controls apply to the MVP. Recommendations will be implemented before go-live with the first client

---

## 6. Observability

**Logging:** Structured logs (JSON) in each service, centralized on the existing log server via rsyslog
**Metrics:** Prometheus + Grafana installed on the monitoring VM. Dashboards are under construction; the Payment Service availability dashboard will be prioritized before go-live
**Alerts:** Not configured yet. Marcus will coordinate with the operations team to define thresholds
**Distributed tracing:** Not implemented in the MVP; will be evaluated in the next iteration

---

## 7. Assumptions and accepted risks

| # | Assumption / Risk | Owner | Mitigation plan |
|---|-------------------|-------|-----------------|
| R1 | CoreBanking available >99% during the pilot | Infrastructure | Manual monitoring; immediate escalation if incident |
| R2 | FraudShield responds in ≤3s consistently | External vendor | Existing contractual SLA; no defined fallback |
| R3 | Pilot volume does not exceed current capacity | Marcus | Weekly metrics review |
| R4 | PCI-DSS: basic controls sufficient for pilot | Legal / Daniel | Evaluation in progress |
| R5 | Duplicate payments from client resend (<0.1% expected) | Daniel | Manual reconciliation |

---

## 8. Discarded decisions and justification

| Decision | Discarded | Reason |
|----------|-----------|--------|
| WebSockets for real-time status | Yes | Network support unavailable without platform changes |
| Message queue (RabbitMQ/SQS) | Yes | Operational complexity outside the 6-week timeline |
| Circuit breaker (Resilience4j/Tenacity) | Yes | Delivery speed prioritized; add post-pilot |
| Kubernetes | Yes | On-premise infrastructure without current operational capacity |
| Parallel calls to FraudShield + CoreBanking | N/A | FraudShield must precede CoreBanking per compliance |

---

## 9. Pending items before go-live

- [ ] Configure health check endpoint in API Gateway
- [ ] Define and document timeouts for CoreBanking and FraudShield calls
- [ ] Confirm PCI-DSS scope with legal team and apply minimum controls
- [ ] Configure Grafana alerts (thresholds with Marcus and operations)
- [ ] Load test against UAT (even if not equivalent to production)
- [ ] Document manual reconciliation procedure for inconsistent transactions
- [ ] Define validated rollback process and execute it in a drill

---

## 10. Next steps (post-MVP)

- Implement message queue for notifications and retries
- Add circuit breaker for CoreBanking calls
- Migrate to WebSockets or SSE for real-time status
- Evaluate Oracle 11g migration or abstraction layer
- Formal WCAG 2.1 AA accessibility review
- Automated CI/CD pipeline
- Support for scale of 500 tx/min (requires infrastructure redesign)
