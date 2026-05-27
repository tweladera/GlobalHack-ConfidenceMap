// Use case: NovaBank — International Instant Payments
// Characters: Sofia (PM), Daniel (Architect), Priya (QA Lead), Marcus (Delivery Lead), Elena (Accessibility)
// Context: 6 weeks, legacy architecture, regulatory pressure

export const DEMO_SPEC = `# NovaBank — International Instant Payments
## Product Requirements Document v1.2

**Author:** Sofia Chen, Product Manager
**Reviewed by:** Daniel Reyes, Software Architect
**Status:** Under review
**Delivery target:** 6 weeks

---

## Business context

NovaBank needs to launch international instant payments for corporate clients in LATAM.
Local regulations require transaction confirmation in under 10 seconds.
The product will compete directly with Wise and Remitly in the B2B segment.
Projected growth of 300% in transaction volume in the first 6 months.

---

## MVP scope

### US-001: Initiate international payment
As a corporate client,
I want to initiate an international payment from my dashboard
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

---

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

## Out of scope

- Cryptocurrency payments
- Integration with external accounting systems (ERP)
- Multi-language support (English only for MVP)`;

export const DEMO_SPEC_AUTH = `# NovaBank — Multi-Factor Authentication (MFA) System
## Product Requirements Document v0.9

**Author:** Rodrigo Salazar, Product Manager
**Reviewed by:** Daniel Reyes, Software Architect
**Status:** Draft for technical review
**Delivery target:** 8 weeks (regulatory deadline: July 1st)

---

## Business context

NovaBank must implement mandatory multi-factor authentication for all corporate clients before the Q2 regulatory deadline. Local regulations require MFA for access to transfer features starting July 1st. The security team detected 3 unauthorized access attempts in the last 90 days.

---

## MVP scope

### US-101: Second factor registration
As a corporate client, I want to register a second authentication factor to protect my account.

**Acceptance criteria:**
- The user can register an authenticator app (TOTP)
- The user can register their phone number for SMS OTP as an alternative
- 8 recovery codes are generated when the second factor is activated
- The system validates the second factor before activating it

**Technical notes:**
- TOTP codes follow RFC 6238 standard (30-second window)
- The phone number acts as a fallback if the authenticator app is lost
- Recovery codes are single-use

### US-102: Authentication with second factor
As a client, I want to authenticate with my second factor to access my account securely.

**Acceptance criteria:**
- After login with username/password, the second factor is requested
- The user can enter a 6-digit TOTP code or SMS OTP
- A maximum of 3 incorrect attempts is allowed before temporarily blocking the session
- The MFA session has higher privileges than a non-MFA session

**Technical notes:**
- The resulting JWT includes the claim \`mfa_verified: true\`
- The SMS OTP validity window is 10 minutes

### US-103: Trusted device management
As a client, I want to mark a device as trusted to avoid repeating MFA every session.

**Acceptance criteria:**
- The user can mark the current device as trusted for 30 days
- Trusted devices are listed in account settings
- The user can revoke trusted devices individually

### US-104: Account recovery
As a client, I want to recover access if I lose my second factor.

**Acceptance criteria:**
- The user can authenticate with the recovery codes generated during registration
- After using a recovery code, a new second factor must be registered
- The corporate administrator can reset a user's MFA with security team approval

---

## Known technical constraints

- The current authentication system uses JWTs stored in browser localStorage
- The SMS service is Twilio; variable latency of 5-30 seconds has been observed in some LATAM markets
- Biometric authentication was evaluated and rejected for MVP due to integration complexity
- The auth backend is part of a Node.js monolith without service separation

## Non-functional requirements

- The MFA flow must not add more than 10 seconds to the total login time
- High availability: the authentication system requires 99.95% uptime
- All login attempts must be logged with IP, user-agent, and timestamp

## Security and compliance

- OWASP Authentication Cheat Sheet compliance
- TOTP seeds and recovery codes cannot be stored in plain text
- Rate limiting is required on login and MFA verification endpoints
- All authentication activity must be audited

## Out of scope

- Biometric authentication (planned for Q3)
- SSO/SAML for enterprise clients
- Hardware security keys (FIDO2/WebAuthn)`;

export const DEMO_ARCH_AUTH = `# Proposed Architecture — NovaBank MFA
## Author: Daniel Reyes, Software Architect

### Main components

**Frontend:**
- MFA form integrated into the existing login flow
- JWTs stored in localStorage (no change from current system)
- No session expiration on inactivity implemented
- Recovery codes displayed only once; user responsible for saving them

**Auth Service (Node.js, existing monolith):**
- Adding endpoint POST /auth/mfa/verify to verify TOTP/OTP
- TOTP seed generation with \`speakeasy\` library (no external security audit)
- TOTP seeds stored encrypted with AES-128; encryption key hardcoded in .env
- No invalidation of existing active sessions when activating or changing MFA settings
- No replay attack detection for SMS OTP

**SMS Service (Twilio):**
- OTP sent in plain text in the SMS body: "Your NovaBank code is: 123456"
- No limit on SMS OTP resends per login attempt
- Variable latency 5-30s in LATAM; no configurable timeout from Auth Service
- No fallback if Twilio is unavailable (user is locked out)

**Database:**
- PostgreSQL for MFA tokens, trusted devices, and recovery codes
- Recovery codes stored hashed with MD5
- No AES key rotation planned

**Trusted devices:**
- Device token is a UUID stored in a cookie without httpOnly flag
- No binding of the token to the device (user-agent, IP) — the same token works from any machine
- Fixed 30-day expiration with no admin configuration option`;

export const DEMO_ARCHITECTURE = `# Proposed Architecture — NovaBank International Payments
## Author: Daniel Reyes, Software Architect

### Main components

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
- Manual scaling`;
