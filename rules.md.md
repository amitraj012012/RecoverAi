# RecoverAI — Project Rules

## Purpose

This document defines the technical standards, architectural boundaries, AI constraints, security requirements, coding conventions, and quality rules for **RecoverAI — AI Revenue Recovery Agent**.

These rules apply to every phase of development and must be followed by Antigravity or any AI coding agent working on this project.

---

# 1. WHAT TO USE

## 1.1 Frontend

Use:

- React
- TypeScript
- Tailwind CSS
- Reusable component architecture
- React Router for routing
- A small charting library such as Recharts for analytics

### Frontend principles

- Prefer reusable components over duplicated UI.
- Keep business logic out of presentation components when possible.
- Use typed API responses.
- Handle loading, empty, success, and error states.
- Keep forms validated.
- Do not hard-code production metrics.

---

## 1.2 Backend

Use:

- Python
- FastAPI
- Pydantic for request/response validation
- SQLAlchemy or the project's selected PostgreSQL ORM/data layer
- Structured logging

The backend is responsible for:

- Authentication/authorization checks
- Payment event processing
- Recovery-case management
- Prediction requests
- AI-agent orchestration
- Tool execution
- Payment verification
- Business calculations
- Audit logging

Never put security-sensitive business logic only in the frontend.

---

## 1.3 Database

Use:

- PostgreSQL
- Supabase is allowed as the hosted PostgreSQL/Auth platform.

Core entities:

- `customers`
- `payments`
- `recovery_cases`
- `recovery_actions`

Additional tables may be introduced only when they have a clear product or technical purpose.

---

## 1.4 AI

Use an LLM only where reasoning or natural-language generation provides actual value.

Use normal deterministic code or ML for:

- Revenue calculations
- Aggregations
- Validation
- State transitions
- Permission checks
- Financial arithmetic
- Recovery metrics
- Data integrity
- Tool authorization

Use the AI agent for:

- Interpreting a recovery case
- Choosing among allowed recovery strategies
- Explaining the decision
- Generating contextual customer communication
- Selecting the next allowed action based on previous outcomes

---

## 1.5 Machine Learning

For the recovery-probability model, prefer a simple, explainable baseline first:

- Logistic Regression, or
- Random Forest

Use meaningful features such as:

- Payment amount
- Payment method
- Failure reason
- Previous successful payments
- Previous failed payments
- Customer tenure
- Customer activity
- Subscription value
- Previous recovery attempts

Do not introduce a complex model unless it demonstrably improves the product.

---

# 2. WHAT TO AVOID

## 2.1 Avoid Fake AI

Do not use an LLM for tasks that ordinary code can perform more accurately.

Bad:

```text
LLM → calculate total revenue at risk
```

Good:

```text
Backend → sum failed payment amounts
```

Bad:

```text
LLM → decide whether user is authorized
```

Good:

```text
Backend → enforce authorization
```

---

## 2.2 Avoid Unrestricted AI Agents

Never give the LLM:

- Shell access
- Arbitrary database write access
- Arbitrary HTTP access
- Arbitrary code execution
- Unrestricted payment operations

The agent may only call explicitly approved tools.

---

## 2.3 Avoid Real Payment Credentials

Never store:

- Card numbers
- CVV
- UPI PIN
- Bank credentials
- Payment passwords
- Private payment secrets

The hackathon MVP uses synthetic/demo payment data and a mock payment service.

---

## 2.4 Avoid Claiming Real Razorpay Data

The prototype must never imply that its synthetic data came from Razorpay.

Use wording such as:

> “Synthetic data used for the hackathon prototype. No private Razorpay/customer data was used.”

All recovery results shown in the demo must be labelled as simulated unless they come from an authorized real integration.

---

## 2.5 Avoid Hard-Coded Business Results

Do not hard-code:

```text
₹31,20,000 recovered
55.3% recovery rate
```

The application must calculate metrics from stored simulation data.

Demo seed data is acceptable, but the metrics must still be computed.

---

## 2.6 Avoid Unnecessary Complexity

Do not add:

- Microservices without a clear need
- Kubernetes
- Complex event infrastructure
- Multiple databases
- Multiple LLMs
- Multi-agent architecture just for presentation

Start with a modular monolith.

Split services only when there is a demonstrated reason.

---

# 3. LIBRARIES & DEPENDENCIES

## Required categories

### Frontend

- React
- TypeScript
- Tailwind CSS
- React Router
- Recharts or equivalent chart library

### Backend

- FastAPI
- Pydantic
- PostgreSQL-compatible database driver
- ORM/data-access layer
- Testing framework

### AI/ML

- Official SDK for the selected LLM provider
- scikit-learn for the initial prediction model
- pandas/numpy where needed for data processing

### Authentication

- Supabase Auth or equivalent trusted authentication provider

---

## Dependency rules

- Prefer stable, maintained libraries.
- Do not install a package just to solve a small problem that can be solved with existing dependencies.
- Do not add duplicate libraries for the same purpose.
- Review dependency purpose before installation.
- Keep dependencies documented.
- Do not use abandoned libraries when a maintained alternative exists.
- Never expose API keys in frontend code.

---

# 4. ERROR HANDLING

## Frontend

Every API request must handle:

- Loading
- Success
- Empty response
- Validation error
- Authentication error
- Permission error
- Server error
- Network failure

Show user-friendly messages.

Never display raw stack traces to users.

---

## Backend

Use:

- Typed/structured exceptions
- HTTP status codes
- Validation errors
- Centralized error handling
- Structured logs

Example:

```text
400 → Invalid request
401 → Unauthenticated
403 → Unauthorized
404 → Resource not found
409 → Conflict
422 → Validation error
500 → Internal server error
```

---

## AI failures

If the LLM:

- Times out
- Returns malformed output
- Chooses an invalid action
- Returns missing fields
- Exceeds limits

the system must fail safely.

Never execute an unvalidated AI response.

Fallback:

```text
AI failure
↓
Validate/repair if safe
↓
Otherwise use deterministic fallback
↓
Log failure
↓
Do not perform unsafe action
```

---

# 5. BOUNDARIES OF AI

This is one of the most important project rules.

## AI CAN

The AI can:

- Analyze recovery context.
- Recommend an allowed strategy.
- Explain its decision.
- Generate customer-facing messages.
- Choose the next allowed recovery action.
- Consider previous recovery attempts.

## AI CANNOT

The AI cannot:

- Authorize itself.
- Change user permissions.
- Access arbitrary data.
- Execute arbitrary code.
- Directly write unrestricted database records.
- Invent payment success.
- Mark a payment as recovered without verification.
- Change financial calculations.
- Override maximum recovery attempts.
- Bypass security controls.
- Create or modify its own tools.

---

## Structured AI output

The agent should return structured data similar to:

```json
{
  "strategy": "CREATE_PAYMENT_LINK",
  "confidence": 0.87,
  "reason": "Strong payment history with an isolated card failure.",
  "expected_recovery": 1739,
  "next_action": "create_payment_link"
}
```

The backend must validate:

- Strategy
- Required fields
- Numeric ranges
- Allowed tool
- Permission
- Case state

before execution.

---

# 6. FINANCIAL CALCULATION RULES

Financial values must be calculated by deterministic backend code.

Never ask the LLM to perform authoritative financial arithmetic.

Use integer minor units where practical.

Example:

```text
₹1,999 → 199900 paise
```

Avoid floating-point errors for money.

Every recovered amount must have:

- Payment reference
- Recovery case reference
- Verification result
- Timestamp

A payment is counted as recovered only after successful verification.

---

# 7. RECOVERY WORKFLOW RULES

The normal recovery lifecycle is:

```text
FAILED
↓
ANALYZING
↓
ACTION_SELECTED
↓
ACTION_EXECUTED
↓
WAITING
↓
VERIFIED
↓
RECOVERED
```

Failure path:

```text
ACTION_EXECUTED
↓
FAILED
↓
NEXT_STRATEGY
↓
ESCALATED
```

The system must store the complete action history.

---

# 8. RECOVERY ACTION RULES

Allowed strategies:

```text
RETRY_PAYMENT
CREATE_PAYMENT_LINK
ALTERNATE_PAYMENT_METHOD
SEND_REMINDER
OFFER_INCENTIVE
ESCALATE_TO_HUMAN
```

## Retry

Use when a temporary failure is plausible.

## Alternate payment

Use when the current method appears problematic.

## Payment link

Use when the customer needs another payment path.

## Reminder

Use when the customer is likely to complete payment after communication.

## Incentive

Only use when economically justified.

The agent must consider:

```text
Expected recovered revenue
-
Incentive cost
-
Recovery cost
```

## Escalation

Use when:

- Maximum automated attempts are reached.
- Risk is high.
- Customer value is high and automation is unsuccessful.
- System cannot safely determine the next action.

---

# 9. AGENT TOOL RULES

Every tool must have:

- Explicit name
- Typed input schema
- Typed output schema
- Authorization check
- Validation
- Audit logging
- Failure handling

Example tools:

```text
retry_payment(payment_id)
create_payment_link(payment_id)
send_message(customer_id, template_id)
apply_incentive(customer_id, max_amount)
get_payment_status(payment_id)
escalate_case(case_id)
```

The agent must not call tools outside the allowlist.

---

# 10. DATA & PRIVACY RULES

## Synthetic data

The default development and hackathon dataset must be synthetic.

Synthetic customers should use demo identities such as:

```text
C1024
C2048
C3001
```

Do not use unnecessary real personal information.

---

## Production integration

If a real payment integration is added later:

- Obtain explicit authorization.
- Use official APIs/webhooks.
- Verify webhook signatures where supported.
- Minimize stored data.
- Follow applicable privacy/security requirements.
- Never expose credentials to the frontend.

---

# 11. CODE STYLE

## General

- Write readable code.
- Prefer small functions.
- Avoid duplicated logic.
- Use descriptive names.
- Keep modules focused.
- Add comments only where they explain non-obvious reasoning.

## Naming

Frontend:

```text
PascalCase → Components
camelCase → Functions/variables
```

Backend:

```text
snake_case → Functions/variables
PascalCase → Classes
```

Database:

```text
snake_case
```

---

# 12. ARCHITECTURE RULES

Use a modular monolith for the MVP.

Recommended structure:

```text
Frontend
   ↓
FastAPI
   ↓
Application Services
   ↓
Domain Logic
   ↓
Database
```

AI layer:

```text
Recovery Service
      ↓
Prediction Model
      ↓
AI Decision Agent
      ↓
Validated Tool Layer
      ↓
Mock Payment/Communication APIs
```

Do not allow the frontend to call the LLM directly for privileged operations.

---

# 13. API RULES

Use REST APIs with predictable responses.

Example:

```text
POST /payments/events
GET /payments
GET /payments/{id}

GET /recovery-cases
GET /recovery-cases/{id}
POST /recovery-cases/{id}/execute

POST /ai/recovery-decision

GET /analytics/overview
GET /analytics/recovery
```

Rules:

- Validate request bodies.
- Validate authentication.
- Return consistent error responses.
- Never expose internal stack traces.
- Never trust frontend-provided financial totals.

---

# 14. TESTING RULES

Every critical business rule must be testable.

### Unit tests

Test:

- Revenue-at-risk calculation
- Recovery probability handling
- Strategy selection validation
- State transitions
- Financial calculations
- Tool authorization

### Integration tests

Test:

```text
Payment failure
→ Recovery case
→ AI decision
→ Tool execution
→ Payment result
→ Verification
→ Revenue recovered
```

### Security tests

Test:

- Unauthorized API calls
- Invalid agent actions
- Invalid payment IDs
- Duplicate recovery attempts
- Excessive attempts
- Malformed AI output

---

# 15. PERFORMANCE RULES

- Do not block the UI during long AI operations.
- Use loading states.
- Avoid unnecessary database queries.
- Paginate large lists.
- Do not load 100,000 records into the browser.
- Use backend aggregation for dashboard metrics.
- Cache expensive read-only calculations where useful.

---

# 16. OBSERVABILITY

Log important events:

```text
payment_received
payment_failed
recovery_case_created
prediction_completed
ai_decision_created
tool_called
tool_failed
payment_verified
revenue_recovered
case_escalated
```

Never log:

- Passwords
- API keys
- Card credentials
- Sensitive secrets

Each important recovery action should have a traceable ID.

---

# 17. DOCUMENTATION RULES

Maintain:

```text
README.md
docs/architecture.md
docs/product-requirements.md
docs/demo-script.md
phases.md
rules.md
```

Documentation must match the actual implementation.

Do not document features that do not exist.

---

# 18. GIT & CHANGE RULES

Use small, meaningful commits.

Examples:

```text
feat: add recovery case schema
feat: add failed payment ingestion
feat: add recovery prediction API
feat: add AI recovery decision agent
fix: validate recovery tool actions
test: add recovery workflow integration tests
```

Do not commit:

- `.env`
- API keys
- Secrets
- Build artifacts
- Personal data

---

# 19. ANTIGRAVITY / AI CODING AGENT RULES

Antigravity must work **phase by phase**.

Never ask it to build the entire project in one operation.

For every phase:

1. Read `rules.md`.
2. Read the relevant section of `phases.md`.
3. Inspect the existing project.
4. Identify what already exists.
5. Implement only the current phase.
6. Do not rewrite unrelated working features.
7. Run tests/build checks.
8. Fix errors caused by the current phase.
9. Report files changed and tests performed.

### Before modifying code

The agent should inspect:

- Existing files
- Existing routes
- Existing database schema
- Existing environment variables
- Existing dependencies
- Existing tests

Never blindly overwrite working code.

---

# 20. PHASE BOUNDARY RULE

The current phase has priority.

If Phase 4 is being implemented, do not silently implement Phase 10.

If a later feature is required as a dependency, implement only the smallest stable foundation required for it.

---

# 21. UI/UX RULES

The UI should communicate financial value immediately.

Priority order:

1. Revenue impact
2. Recovery status
3. AI decision
4. Action history
5. Detailed analytics

Avoid excessive animations.

Every important action should provide feedback.

Use clear statuses:

```text
At Risk
Analyzing
Recovery Running
Recovered
Failed
Escalated
```

---

# 22. DEMO RULES

The hackathon demo must use a deterministic seed dataset.

The demo should show:

1. Revenue at risk.
2. A failed payment.
3. Customer history.
4. AI recovery probability.
5. AI strategy selection.
6. Tool execution.
7. Payment verification.
8. Revenue recovered.
9. AI vs baseline comparison.

Do not depend on an unpredictable live external API for the main demo.

---

# 23. HONESTY RULES

Never claim:

- Real Razorpay production access unless it actually exists.
- Real merchant revenue recovered unless it actually happened.
- Real customer data.
- Real production accuracy from synthetic experiments.

Correct wording:

> “Synthetic simulation for the hackathon prototype.”

If a real integration is later added, document exactly what was integrated and under what authorization.

---

# 24. DEFINITION OF DONE

A feature is not complete just because the code exists.

A feature is complete when:

- It works through the intended user flow.
- Inputs are validated.
- Errors are handled.
- Data persists correctly.
- Tests pass where applicable.
- No obvious console/server errors remain.
- UI has loading/error/empty states.
- Security boundaries are respected.
- Documentation is updated.

---

# 25. FINAL PRODUCT PRINCIPLE

RecoverAI exists to answer one question:

> **“A payment just failed. What should we do now to maximize the probability of recovering that money without unnecessarily sacrificing margin?”**

The product must therefore prioritize:

**Real problem → reliable data → measurable prediction → controlled AI decision → safe execution → verified payment → measurable revenue impact.**

A beautiful UI is secondary.

The intelligence, reliability, and measurable business outcome are the product.
