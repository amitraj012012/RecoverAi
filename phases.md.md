# RecoverAI — Phased Build Plan

## Project
**RecoverAI — AI Revenue Recovery Agent**

## Goal
Build a hackathon-ready prototype that detects failed payments, estimates recovery potential, chooses the best recovery action, executes that action through controlled tools, verifies the outcome, and measures recovered revenue.

## Critical Product Rules
- Use **synthetic/demo payment data** for the hackathon.
- Never claim to use real Razorpay customer/payment data.
- Keep the payment integration replaceable so a real, authorized webhook/API integration can be added later.
- Build **one phase at a time** and do not proceed until its acceptance criteria pass.

---

# Phase 0 — Project Foundation

### Objective
Create a clean, stable foundation.

### Requirements
- Frontend + backend structure.
- Environment variables and `.env.example`.
- Git/version control.
- README.
- Basic logging and error handling.
- API contract defined before complex UI.
- Frontend: React + TypeScript if practical.
- Backend: Python + FastAPI.
- Database: PostgreSQL/Supabase-compatible.

### Suggested structure
```text
recoverai/
├── frontend/
├── backend/
├── data/
├── docs/
├── tests/
├── .env.example
├── README.md
└── phases.md
```

### Acceptance criteria
- Frontend starts.
- Backend starts.
- Health endpoint works.
- Database configuration works.
- No secrets are committed.

---

# Phase 1 — Authentication & Merchant Workspace

### Objective
Create a secure merchant workspace.

### Requirements
- Sign up.
- Login/logout.
- Forgot password.
- Protected dashboard routes.
- Merchant profile.
- Session persistence.
- Supabase Auth or equivalent.

### Acceptance criteria
- Registration works.
- Login/logout works.
- Unauthenticated users cannot access dashboard.
- Merchant identity is available to backend requests.
- Auth errors are handled clearly.

---

# Phase 2 — Dashboard & Navigation

### Objective
Create the RecoverAI control center.

### Dashboard metrics
- Revenue at Risk
- Estimated Recoverable Revenue
- Revenue Recovered
- Recovery Rate
- Active Recovery Cases
- Successful Recovery Actions
- Recent Agent Activity

### Navigation
- Overview
- Payments
- Recovery Cases
- AI Decisions
- Customers
- Analytics
- Settings

### Requirements
- Responsive UI.
- Loading/empty/error states.
- Reusable components.
- Basic charts.
- Demo values must later be replaced by database-derived values.

### Acceptance criteria
- Dashboard loads without errors.
- Navigation works.
- Metrics have a single data source.

---

# Phase 3 — Synthetic Data & CRUD

### Objective
Create the data foundation.

## Customers
- id
- demo identifier
- subscription_value
- tenure
- activity_score
- created_at

## Payments
- id
- customer_id
- amount
- currency
- payment_method
- status
- failure_reason
- created_at

## Recovery Cases
- id
- payment_id
- recovery_probability
- selected_strategy
- status
- attempt_count
- expected_revenue
- recovered_amount
- created_at

## Recovery Actions
- id
- recovery_case_id
- action_type
- agent_reason
- result
- executed_at

### Synthetic scenarios
Generate:
- Successful payments
- Card declines
- UPI/network failures
- Bank errors
- Insufficient funds
- Repeated failures
- High-value customers
- Low-activity/churn-risk customers

### Acceptance criteria
- At least 10,000 demo payment records.
- Valid relationships.
- Search/filter/sort work.
- Dashboard metrics can be calculated from the database.

---

# Phase 4 — Payment Failure & Revenue Risk Engine

### Objective
Turn raw payment data into revenue-risk information.

### Requirements
Detect:
- Failed payments.
- Amount at risk.
- Failure reason.
- Customer history.
- Previous failures.
- Recent activity.

### Calculations
```text
Revenue at Risk = Sum of failed payment amounts
Historical Success Rate = Successful Payments / Total Attempts
```

Create an initial recoverability estimate.

### Acceptance criteria
- Failed payments can become recovery cases.
- Revenue-at-risk calculation is accurate.
- Metrics update when data changes.

---

# Phase 5 — Recovery Prediction Engine

### Objective
Estimate the probability that a failed payment can be recovered.

### Features
- Payment amount
- Failure reason
- Payment method
- Previous successful payments
- Previous failed payments
- Customer tenure
- Activity score
- Subscription value
- Previous recovery attempts

### MVP model
Start with:
- Logistic Regression, or
- Random Forest.

Do not start with deep learning.

### Requirements
- Train/test split.
- Basic evaluation.
- Model version.
- Avoid data leakage.
- Prediction between 0 and 1.

### Example
```text
Customer: C1024
Amount: ₹1,999
Recovery probability: 87%
```

### Acceptance criteria
- Model runs.
- Prediction API works.
- New cases can be scored.
- Evaluation results are documented.

---

# Phase 6 — AI Recovery Decision Agent

### Objective
Build the core AI decision layer.

### Agent inputs
- Customer profile.
- Payment information.
- Failure reason.
- Recovery probability.
- Previous recovery attempts.
- Expected financial value.
- Available actions.

### Allowed actions
```text
RETRY_PAYMENT
CREATE_PAYMENT_LINK
ALTERNATE_PAYMENT_METHOD
SEND_REMINDER
OFFER_INCENTIVE
ESCALATE_TO_HUMAN
```

### Agent responsibilities
1. Analyze the case.
2. Select an allowed strategy.
3. Explain why.
4. Call only approved tools.
5. Respect action limits.
6. Remember previous actions.
7. Avoid repeating ineffective strategies.

### Example
```text
Customer: 17 successful / 18 attempts
Failure: Card declined
Recovery probability: 87%

Decision: CREATE_PAYMENT_LINK

Reason:
Strong payment history and isolated card failure.
A discount is unnecessary.
An alternate payment path has high expected recovery value.
```

### Critical security rule
The LLM must **not** have arbitrary backend access. It may call only predefined, validated tools.

### Acceptance criteria
- Structured agent output.
- Every decision has a reason.
- Invalid actions are rejected.
- Previous actions are included in the decision context.

---

# Phase 7 — Recovery Action Simulator

### Objective
Make the agent execute actions rather than only recommend them.

### Mock APIs
```text
POST /payments/retry
POST /payments/create-link
POST /messages/send
POST /recovery/execute
GET  /payments/{id}
```

### Simulated outcomes
- Success
- Failure
- Delayed response
- Customer ignored
- Alternate-method success

### Example
```text
AI → Retry payment
Simulator → Failed

AI → Create payment link
Simulator → Customer paid

Result → ₹1,999 recovered
```

### Acceptance criteria
- At least 3 actions execute successfully.
- Action results persist.
- Payment state changes correctly.
- Recovery is counted only after verification.

---

# Phase 8 — Recovery State Machine & Memory

### Objective
Make recovery persistent and adaptive.

### States
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

### Memory
Store:
- Previous actions.
- Results.
- Attempt count.
- Agent reasoning.
- Payment status.
- Recovery status.

### Business rule
Do not repeatedly perform the same ineffective action.

### Acceptance criteria
- State survives refresh.
- Agent can continue from previous state.
- Maximum attempts are enforced.

---

# Phase 9 — Merchant Recovery Operations UI

### Objective
Give merchants visibility and control.

### Recovery Cases page
Show:
- Customer
- Amount
- Failure reason
- Recovery probability
- Selected strategy
- Status
- Attempts
- Recovered amount

### Case details
Show:
- Customer history
- Payment details
- Prediction
- AI decision
- Reasoning summary
- Action history
- Outcome

### Agent Activity Feed
```text
14:32:05  Payment failed
14:32:06  Customer history analyzed
14:32:07  Recovery probability = 87%
14:32:07  Alternate payment selected
14:32:08  Payment link created
14:34:21  Customer completed payment
14:34:22  ₹1,999 recovered
```

### Acceptance criteria
- Merchant can inspect a complete case.
- Agent actions are traceable.
- Status is understandable to a non-technical user.

---

# Phase 10 — Baseline vs AI Experiment

### Objective
Prove the AI approach provides value.

## Baseline
```text
Payment failed
↓
Retry
↓
Generic reminder
```

## RecoverAI
```text
Analyze
↓
Predict
↓
Select strategy
↓
Execute
↓
Verify
↓
Adapt
```

### Compare
- Recovery rate
- Revenue recovered
- Recovery cost
- Discount cost
- Time to recovery
- Human escalation
- Number of actions

### Important
All hackathon results are **synthetic simulation results**.

### Acceptance criteria
- Both systems use the same test scenarios.
- Results are reproducible.
- Comparison is visible in the dashboard.
- Metrics are calculated, not manually entered.

---

# Phase 11 — Analytics & Business Impact

### Objective
Translate system activity into merchant value.

### Metrics
```text
Revenue at Risk
Recoverable Revenue
Revenue Recovered
Recovery Rate
Average Recovery Time
Cost per Recovery
Recovery ROI
```

### Charts
- Recovery funnel
- Recovery by failure reason
- Recovery by payment method
- Strategy success rate
- AI vs baseline
- Revenue recovered over time

### Acceptance criteria
- Charts use database data.
- Filters work.
- Metrics reconcile with underlying records.

---

# Phase 12 — Security, Validation & Reliability

### Requirements
- No real card data.
- No CVV/card storage.
- Secrets in environment variables.
- Backend authorization.
- Input validation.
- Agent tool allowlist.
- Maximum recovery attempts.
- Audit log.
- Error logging.
- API failure handling.

### AI safety
The AI must not:
- Invent successful payments.
- Count unverified payments as recovered.
- Create arbitrary tools.
- Access unrestricted APIs.
- Execute actions outside its allowed tool set.

### Acceptance criteria
- Failed API calls do not corrupt state.
- Unverified payments are never counted as recovered.
- Unauthorized requests are rejected.
- Agent tool calls are validated.

---

# Phase 13 — Testing & QA

### Unit tests
Test:
- Revenue calculations.
- Prediction API.
- State transitions.
- Tool validation.
- Database operations.

### Integration test
```text
Payment failure
→ Recovery case
→ AI decision
→ Action
→ Payment result
→ Verification
→ Revenue recovered
```

### Edge cases
- Zero/invalid amount.
- Very large payment.
- Repeated failures.
- Missing customer.
- Unknown failure reason.
- API timeout.
- Invalid agent action.
- Success after multiple failures.

### Acceptance criteria
- Critical workflows pass.
- No broken primary user flow.
- Errors are understandable.

---

# Phase 14 — Deployment

### Recommended
- Frontend: Vercel
- Backend: Render/Railway
- Database: Supabase/PostgreSQL

### Requirements
- Production environment variables.
- CORS.
- HTTPS.
- Database migrations.
- Seed/demo dataset.
- Health check.
- Logging.

### Acceptance criteria
- Public demo works.
- Backend works from deployed frontend.
- Demo dataset loads.
- No secrets exposed.

---

# Phase 15 — Hackathon Demo

### Objective
Prove the product in about 5 minutes.

### Demo scenario
```text
100,000 renewal payments
8,000 failed
₹80 lakh revenue at risk
```

Select:
```text
Customer: C1024
Amount: ₹1,999
Failure: Card declined
History: 17/18 successful
Recovery probability: 87%
```

AI selects:
```text
Alternate payment method
```

Execute → verify → show:
```text
Payment successful
₹1,999 recovered
```

Then run a batch simulation and compare:
```text
Baseline Recovery
vs
RecoverAI Recovery
```

### Final message
> "We don't just predict payment failure. We decide what to do after failure, execute the recovery action, verify the outcome, and measure the revenue we recover."

---

# Phase 16 — Final Polish & Submission

### Checklist
- Clean UI.
- No console errors.
- README complete.
- Architecture diagram.
- Product requirements.
- Demo video.
- Clean GitHub repository.
- `.env.example`.
- Synthetic-data disclaimer.
- Setup instructions tested from a clean environment.
- Screenshots.
- Rehearsed demo.

### Repository
```text
recoverai/
├── frontend/
├── backend/
├── data/
├── docs/
│   ├── architecture.md
│   ├── product-requirements.md
│   └── demo-script.md
├── tests/
├── phases.md
├── README.md
└── .env.example
```

---

# Phase Gates

```text
Phase 0  Foundation
   ↓
Phase 1  Authentication
   ↓
Phase 2  Dashboard
   ↓
Phase 3  Data + CRUD
   ↓
Phase 4  Revenue Risk
   ↓
Phase 5  Prediction
   ↓
Phase 6  AI Agent
   ↓
Phase 7  Action Simulator
   ↓
Phase 8  Memory + State
   ↓
Phase 9  Operations UI
   ↓
Phase 10 AI vs Baseline
   ↓
Phase 11 Analytics
   ↓
Phase 12 Security
   ↓
Phase 13 Testing
   ↓
Phase 14 Deployment
   ↓
Phase 15 Demo
   ↓
Phase 16 Submission
```

## Antigravity Build Rule

Do **not** give Antigravity the entire project and ask it to build everything at once.

For every phase, give it:
1. Current phase number.
2. Objective.
3. Requirements.
4. Acceptance criteria.
5. Existing project state.
6. Explicit instruction to modify only what is needed for that phase.

After each phase:
- Run the app.
- Test acceptance criteria.
- Fix blocking errors.
- Commit the working version.
- Only then start the next phase.

This phased approach is intentionally designed to prevent an AI coding agent from generating a large, unstable codebase before the core revenue-recovery workflow is proven.
