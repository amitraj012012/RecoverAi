# RecoverAI — Architecture

## 1. ARCHITECTURE

### 1.1 Architecture Goal

RecoverAI is a modular, AI-powered revenue recovery platform for merchants.

The system receives synthetic payment events, identifies failed payments, evaluates customer/payment context, predicts recovery probability, asks the AI decision layer to select an allowed recovery strategy, executes the action through controlled tools, verifies the payment result, and updates revenue analytics.

### 1.2 High-Level Architecture

```text
                    ┌─────────────────────────────┐
                    │        Merchant UI           │
                    │ React + TypeScript + Tailwind│
                    └──────────────┬──────────────┘
                                   │ HTTPS / REST
                                   ▼
                    ┌─────────────────────────────┐
                    │        FastAPI Backend       │
                    │ Auth / API / Validation      │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
              ┌──────────┐  ┌────────────┐  ┌──────────────┐
              │ Database │  │ Risk / ML  │  │ AI Decision  │
              │Postgres  │  │ Prediction │  │    Agent     │
              └──────────┘  └────────────┘  └──────┬───────┘
                                                   │
                                            Validated Tools
                                                   │
                    ┌──────────────────────────────┼────────────────────┐
                    ▼              ▼               ▼                    ▼
              Retry Payment   Payment Link   Communication       Human Escalation
                    │              │               │
                    └──────────────┴───────────────┘
                                   │
                                   ▼
                         ┌──────────────────┐
                         │ Payment Simulator│
                         │ / Mock APIs      │
                         └────────┬─────────┘
                                  │
                                  ▼
                         Payment Verification
                                  │
                                  ▼
                         Revenue & Analytics
```

### 1.3 Main Components

#### A. Merchant Frontend

Responsibilities:
- Authentication.
- Dashboard.
- Payment monitoring.
- Recovery cases.
- Customer details.
- AI decision explanations.
- Agent activity.
- Analytics.
- Settings.

The frontend must never directly execute privileged payment or recovery operations.

#### B. FastAPI Backend

Responsibilities:
- Authentication/authorization checks.
- REST API.
- Input validation.
- Recovery workflow.
- Business calculations.
- AI orchestration.
- Tool authorization.
- Payment verification.
- Analytics aggregation.
- Audit logging.

#### C. PostgreSQL / Supabase

Stores:
- Merchant profiles.
- Customers.
- Payments.
- Recovery cases.
- Recovery actions.
- Agent decisions.
- Audit events.

#### D. Recovery Prediction Engine

Calculates:
- Recovery probability.
- Customer behavior features.
- Historical payment success rate.
- Risk/recovery signals.

Initial models:
- Logistic Regression.
- Random Forest.

#### E. AI Recovery Decision Agent

The agent:
- Reads the recovery context.
- Considers prediction results.
- Reviews previous attempts.
- Chooses an allowed strategy.
- Provides a structured reason.
- Calls only approved tools.

The AI cannot directly access arbitrary backend operations.

#### F. Action/Tool Layer

Allowed tools:

```text
retry_payment()
create_payment_link()
send_message()
apply_incentive()
get_payment_status()
escalate_case()
```

Every tool must validate input, authorization, case state, and action limits.

#### G. Payment Simulator

For the hackathon:
- Generates payment outcomes.
- Simulates success/failure.
- Simulates retries.
- Simulates payment links.
- Simulates customer response.

No real payment credentials are required.

#### H. Verification Layer

A recovery is counted only after payment status is verified.

```text
Action Executed
      ↓
Payment Status Checked
      ↓
SUCCESS?
  /        \
YES         NO
 ↓           ↓
Recovered   Next Strategy
```

---

# 2. SYSTEM FLOW

## 2.1 Failed Payment Flow

```text
Payment Attempt
      ↓
Payment Failed
      ↓
Create Recovery Case
      ↓
Load Customer + Payment History
      ↓
Calculate Features
      ↓
Recovery Prediction
      ↓
AI Decision Agent
      ↓
Select Strategy
      ↓
Validate Tool Call
      ↓
Execute Action
      ↓
Verify Payment
      ↓
 ┌────┴─────┐
SUCCESS     FAILED
   ↓           ↓
Recovered   Next Strategy
Revenue     / Escalation
Updated
```

## 2.2 Example

```text
Customer: C1024
Payment: ₹1,999
Failure: Card Declined

History:
17 successful / 18 attempts
High recent activity

Prediction:
Recovery probability = 87%

AI decision:
CREATE_PAYMENT_LINK

Reason:
Strong payment history with an isolated card failure.
A discount is unnecessary.

Action:
Payment link created.

Verification:
Payment successful.

Result:
₹1,999 recovered.
```

---

# 3. FOLDER & FILE STRUCTURE

Recommended repository:

```text
recoverai/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── layouts/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── types/
│   │   ├── utils/
│   │   └── App.tsx
│   ├── public/
│   ├── package.json
│   └── tsconfig.json
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── agents/
│   │   ├── tools/
│   │   ├── ml/
│   │   ├── database/
│   │   ├── core/
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── data/
│   ├── generators/
│   ├── seed/
│   └── sample/
│
├── docs/
│   ├── architecture.md
│   ├── product-requirements.md
│   └── demo-script.md
│
├── tests/
│
├── phases.md
├── rules.md
├── README.md
└── .gitignore
```

## 3.1 Important Backend Modules

### `api/`
REST endpoints.

### `services/`
Business logic.

### `agents/`
AI orchestration and decision logic.

### `tools/`
Safe, predefined actions available to the AI.

### `ml/`
Prediction model and feature processing.

### `models/`
Database models.

### `schemas/`
Pydantic request/response schemas.

### `database/`
Database connection and migrations/configuration.

### `core/`
Configuration, security, logging, and shared infrastructure.

---

# 4. TECH STACK

## Frontend

- React
- TypeScript
- Tailwind CSS
- React Router
- Recharts

## Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy or equivalent PostgreSQL data layer

## Database

- PostgreSQL
- Supabase

## Authentication

- Supabase Auth or equivalent trusted authentication provider.

## AI

- LLM API with structured output/function calling.

## Machine Learning

- Python
- pandas
- NumPy
- scikit-learn
- Optional XGBoost if justified by evaluation.

## Deployment

```text
Frontend → Vercel
Backend  → Render / Railway
Database → Supabase
```

---

# 5. DATABASE ARCHITECTURE

## customers

```text
id
merchant_id
demo_name
subscription_value
tenure
activity_score
created_at
```

## payments

```text
id
merchant_id
customer_id
amount
currency
payment_method
status
failure_reason
created_at
```

## recovery_cases

```text
id
merchant_id
payment_id
recovery_probability
selected_strategy
status
attempt_count
expected_revenue
recovered_amount
created_at
updated_at
```

## recovery_actions

```text
id
recovery_case_id
action_type
agent_reason
result
metadata
executed_at
```

## audit_events

```text
id
merchant_id
event_type
entity_id
actor
metadata
created_at
```

---

# 6. API ARCHITECTURE

## Authentication

```text
POST /auth/signup
POST /auth/login
POST /auth/logout
```

## Payments

```text
POST /payments/events
GET  /payments
GET  /payments/{payment_id}
```

## Recovery

```text
GET  /recovery-cases
GET  /recovery-cases/{case_id}
POST /recovery-cases/{case_id}/execute
```

## AI

```text
POST /ai/recovery-decision
POST /ai/predict-recovery
```

## Analytics

```text
GET /analytics/overview
GET /analytics/recovery
GET /analytics/strategies
```

---

# 7. AI ARCHITECTURE

## AI Decision Pipeline

```text
Recovery Case
     ↓
Customer Context
     ↓
Payment Context
     ↓
Prediction Results
     ↓
Previous Actions
     ↓
Available Tools
     ↓
AI Decision
     ↓
Structured Output
     ↓
Backend Validation
     ↓
Tool Execution
```

## Structured output

```json
{
  "strategy": "CREATE_PAYMENT_LINK",
  "confidence": 0.87,
  "reason": "Strong payment history with isolated card failure.",
  "expected_recovery": 1739,
  "next_action": "create_payment_link"
}
```

The backend must validate the output before execution.

---

# 8. AI TOOL BOUNDARY

The AI may only use:

```text
retry_payment
create_payment_link
send_message
apply_incentive
get_payment_status
escalate_case
```

The AI cannot:

- Execute arbitrary code.
- Run shell commands.
- Query arbitrary tables.
- Modify permissions.
- Change financial totals.
- Mark payments recovered without verification.
- Bypass attempt limits.
- Create new tools dynamically.

---

# 9. RECOVERY STATE ARCHITECTURE

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

Failure:

```text
ACTION_EXECUTED
      ↓
    FAILED
      ↓
NEXT_STRATEGY
      ↓
ESCALATED
```

Every state transition must be validated by backend business rules.

---

# 10. ANALYTICS ARCHITECTURE

The dashboard must calculate metrics from actual stored simulation records.

### Main metrics

```text
Revenue at Risk
Estimated Recoverable Revenue
Revenue Recovered
Recovery Rate
Recovery Cost
Recovery ROI
Average Recovery Time
Active Cases
```

### Recovery funnel

```text
Failed Payments
      ↓
Potentially Recoverable
      ↓
Recovery Started
      ↓
Customer Engaged
      ↓
Payment Recovered
```

### Strategy analytics

Compare:

```text
Retry
Payment Link
Alternate Payment
Reminder
Incentive
Escalation
```

---

# 11. BASELINE VS AI ARCHITECTURE

## Baseline

```text
Payment Failed
      ↓
Retry
      ↓
Generic Reminder
      ↓
Result
```

## RecoverAI

```text
Payment Failed
      ↓
Analyze Context
      ↓
Predict Recovery
      ↓
Choose Strategy
      ↓
Execute
      ↓
Verify
      ↓
Adapt
```

Both systems must run on the same synthetic test scenarios for a fair comparison.

---

# 12. SECURITY ARCHITECTURE

### Never store

- Card numbers
- CVV
- UPI PIN
- Bank credentials
- Payment passwords

### Protect

- API keys
- Database credentials
- Authentication tokens
- AI provider credentials

### Rules

- Secrets stay server-side.
- Use environment variables.
- Validate all API inputs.
- Enforce authentication and authorization.
- Validate every AI tool call.
- Keep an audit trail.
- Never expose internal errors to users.

---

# 13. HACKATHON DATA ARCHITECTURE

The project uses synthetic data.

Example:

```text
100,000 renewal payments
        ↓
8,000 failed payments
        ↓
₹80,00,000 revenue at risk
        ↓
AI analyzes cases
        ↓
Recovery strategies
        ↓
Simulated actions
        ↓
Simulated payment outcomes
        ↓
Recovered revenue
```

All demo results must be labelled:

> **Synthetic simulation — no private Razorpay/customer data used.**

---

# 14. PRODUCTION EXTENSION

The hackathon simulator is intentionally replaceable.

### Hackathon

```text
Synthetic Event Generator
        ↓
Mock Payment API
```

### Future authorized production version

```text
Authenticated Payment Webhooks/API
        ↓
Recovery Engine
        ↓
Merchant-authorized Actions
```

The core recovery logic should not depend directly on the simulator.

---

# 15. DEPLOYMENT ARCHITECTURE

```text
                   Internet
                       │
                       ▼
              ┌────────────────┐
              │ Vercel Frontend│
              └───────┬────────┘
                      │ HTTPS
                      ▼
              ┌────────────────┐
              │ FastAPI Backend│
              └───────┬────────┘
                      │
       ┌──────────────┼───────────────┐
       ▼              ▼               ▼
   Supabase        AI API        Mock Payment
   PostgreSQL                     Service
       │
       ▼
   Analytics
```

---

# 16. ARCHITECTURAL PRINCIPLES

1. **Modular monolith first.**
2. **Backend owns business logic.**
3. **AI makes bounded decisions, not unrestricted system changes.**
4. **Deterministic code owns financial calculations.**
5. **Every payment recovery must be verified.**
6. **Synthetic data is clearly labelled.**
7. **Every AI action is auditable.**
8. **The simulator can later be replaced by an authorized payment integration.**
9. **Build phase-by-phase according to `phases.md`.**
10. **Follow all rules in `rules.md`.**

---

# 17. DEFINITION OF ARCHITECTURE DONE

The architecture is considered ready when:

- Frontend/backend boundaries are clear.
- Database entities are defined.
- AI boundaries are defined.
- Tool permissions are defined.
- Recovery state machine is defined.
- Payment simulator is isolated from core business logic.
- API boundaries are documented.
- Security boundaries are documented.
- Folder structure is documented.
- Deployment structure is documented.
- The architecture supports the complete demo flow.

## Final system objective

```text
Failed Payment
      ↓
Understand
      ↓
Predict
      ↓
Decide
      ↓
Act
      ↓
Verify
      ↓
Recover Revenue
      ↓
Measure Impact
```

**RecoverAI is an autonomous revenue-recovery system, not a payment chatbot.**
