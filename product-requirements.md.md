# RecoverAI — Product Requirements Document

## 1. Product Overview

**Product:** RecoverAI  
**Type:** AI-powered FinTech / Revenue Recovery platform  
**Primary track:** AI Revenue Recovery

RecoverAI helps merchants recover revenue from failed or at-risk payments. It analyzes payment and customer context, predicts recovery probability, selects an economically sensible recovery strategy, executes the action through controlled tools, verifies the payment result, and measures recovered revenue.

---

## 2. Problem

Businesses lose revenue when payments fail because of temporary bank/network issues, card declines, UPI/payment-method failures, insufficient funds, expired payment methods, inactivity, or churn.

A basic workflow is:

```text
Payment failed → Retry → Generic reminder
```

This treats every customer the same, wastes recovery attempts, may give unnecessary discounts, and provides poor visibility into lost revenue.

RecoverAI changes this to:

```text
Failed Payment
→ Understand
→ Predict
→ Decide
→ Act
→ Verify
→ Recover
→ Measure
```

---

## 3. Product Goal

Answer:

> “A payment just failed. What should we do now to maximize the probability of recovering that money without unnecessarily sacrificing margin?”

---

## 4. Target Users

### Primary
Merchants and businesses with recurring or high-volume payments:
- SaaS
- Subscription businesses
- Online education
- Marketplaces
- Digital services
- Membership businesses

### Secondary
- Finance teams
- Revenue operations
- Payment operations teams

---

## 5. Core Value Proposition

- **Intelligent recovery:** Different failed payments receive different strategies.
- **Automated action:** The system can execute approved actions, not just recommend them.
- **Financial optimization:** Recovery decisions consider expected value and cost.
- **Verification:** Revenue is counted only after payment status is verified.
- **Measurable impact:** AI is compared against a rule-based baseline.

---

## 6. Core User Journey

```text
Payment Attempt
      ↓
Payment Failed
      ↓
Create Recovery Case
      ↓
Analyze Customer + Payment
      ↓
Predict Recovery Probability
      ↓
AI Selects Strategy
      ↓
Execute Approved Action
      ↓
Verify Payment
      ↓
Recovered / Next Strategy / Escalation
```

---

## 7. Functional Requirements

### FR-01 — Payment Event Ingestion
Accept payment events containing:
- payment_id
- customer_id
- amount
- currency
- payment_method
- status
- failure_reason

The hackathon uses synthetic data and a mock payment API.

### FR-02 — Customer Profile
Maintain:
- Customer ID
- Subscription value
- Payment history
- Successful/failed attempts
- Payment methods
- Tenure
- Recent activity
- Previous recovery behavior

### FR-03 — Revenue Risk Engine
Calculate:
- Revenue at Risk = sum of failed payment amounts
- Estimated Recoverable Revenue

Values must be calculated from stored data, not hard-coded.

### FR-04 — Recovery Prediction
Estimate recovery probability using:
- Amount
- Failure reason
- Payment method
- Historical success rate
- Previous failures
- Customer tenure
- Activity
- Subscription value
- Previous recovery attempts

Start with Logistic Regression or Random Forest.

### FR-05 — AI Recovery Decision
The AI receives customer/payment context, prediction results, previous actions, expected value, and available actions.

Allowed strategies:
```text
RETRY_PAYMENT
CREATE_PAYMENT_LINK
ALTERNATE_PAYMENT_METHOD
SEND_REMINDER
OFFER_INCENTIVE
ESCALATE_TO_HUMAN
```

Every decision must include a concise rationale.

---

## 8. Recovery Strategies

### Retry
For plausible temporary failures.

### Alternate Payment Method
When the current method appears problematic.

### Payment Link
Give the customer another payment path.

### Personalized Reminder
Send contextual recovery communication.

### Incentive
Only when economically justified:

```text
Expected recovered revenue
- incentive cost
- recovery cost
```

### Human Escalation
When attempts are exhausted, customer value/risk is high, or automation cannot safely decide.

---

## 9. Agent Memory

Remember:
- Previous actions
- Results
- Attempt count
- Recovery state
- Payment status
- Agent decision/rationale

The agent must avoid repeating ineffective actions.

---

## 10. Recovery State Machine

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

---

## 11. Controlled AI Tools

The AI may only call predefined tools:

```text
retry_payment(payment_id)
create_payment_link(payment_id)
send_message(customer_id, template_id)
apply_incentive(customer_id, max_amount)
get_payment_status(payment_id)
escalate_case(case_id)
```

Every tool call must be authenticated, authorized, validated, audited, and subject to business limits.

---

## 12. Payment Simulator

The hackathon prototype uses a controlled simulator supporting:
- Payment success
- Payment failure
- Retry success/failure
- Payment-link success
- Ignored messages
- Alternate payment success
- Delayed responses

A payment counts as recovered only after verification.

---

## 13. Dashboard Requirements

Show:
- Revenue at Risk
- Estimated Recoverable Revenue
- Revenue Recovered
- Recovery Rate
- Active Recovery Cases
- Successful/failed actions
- Escalated cases
- AI cases analyzed
- Strategy performance

---

## 14. Recovery Case View

Display:
- Customer
- Payment amount
- Failure reason
- Recovery probability
- AI strategy
- Current status
- Recovered amount
- Customer/payment history
- Decision rationale
- Action history
- Verification result

---

## 15. Baseline vs AI

### Baseline
```text
Payment Failed
↓
Retry
↓
Generic Reminder
```

### RecoverAI
```text
Analyze
↓
Predict
↓
Select Strategy
↓
Execute
↓
Verify
↓
Adapt
```

Run both on the same synthetic scenarios and compare:
- Recovery rate
- Revenue recovered
- Recovery cost
- Discount cost
- Time to recovery
- Escalation rate

All hackathon results must be labelled as synthetic simulation results.

---

## 16. Synthetic Data

Generate realistic:
- Successful payments
- Card declines
- UPI/network failures
- Bank errors
- Insufficient funds
- Repeated failures
- High-value customers
- Inactive/churn-risk customers

Use synthetic identities such as `C1024`. Never claim the data is from Razorpay production.

---

## 17. Database

Core tables:

```text
customers
payments
recovery_cases
recovery_actions
audit_events
```

Important fields should support merchant ownership, payment history, recovery state, AI decisions, actions, and verified recovered amount.

---

## 18. API Requirements

```text
POST /auth/signup
POST /auth/login
POST /auth/logout

POST /payments/events
GET  /payments
GET  /payments/{payment_id}

GET  /recovery-cases
GET  /recovery-cases/{case_id}
POST /recovery-cases/{case_id}/execute

POST /ai/recovery-decision
POST /ai/predict-recovery

GET /analytics/overview
GET /analytics/recovery
GET /analytics/strategies
```

---

## 19. Security

Never store:
- Card numbers
- CVV
- UPI PIN
- Bank credentials
- Payment passwords

Keep secrets server-side. Validate all agent actions. Enforce authentication and authorization. Keep an audit trail. Never count an unverified payment as recovered.

---

## 20. Non-Goals

The MVP will not:
- Access private Razorpay merchant/customer data.
- Process real customer payments without authorization.
- Store real payment credentials.
- Claim simulated results are production results.
- Build a complete payment gateway.
- Replace finance/compliance teams.
- Add complex infrastructure without a clear need.

---

## 21. Technology Requirements

### Frontend
React, TypeScript, Tailwind CSS, React Router, Recharts.

### Backend
Python, FastAPI, Pydantic, PostgreSQL data layer.

### Database
PostgreSQL / Supabase.

### Authentication
Supabase Auth or equivalent.

### AI
LLM API with structured output/function calling.

### ML
Python, pandas, NumPy, scikit-learn; XGBoost only if evaluation justifies it.

### Deployment
Vercel + Render/Railway + Supabase.

---

## 22. UI/UX Requirements

The product should feel:

```text
Trustworthy
Intelligent
Financial
Modern
Fast
Professional
```

Visual hierarchy:

```text
Revenue Impact
↓
Recovery Performance
↓
AI Decisions
↓
Active Cases
↓
Analytics
```

Emphasize recovered revenue, revenue at risk, recovery rate, AI decision, and verified outcome.

Do not make the interface look like a generic chatbot or overly futuristic AI demo.

---

## 23. Hackathon Demo

Use a deterministic synthetic dataset.

Example:

```text
100,000 renewal payments
8,000 failed
₹80 lakh revenue at risk
```

Demo case:

```text
Customer: C1024
Amount: ₹1,999
Failure: Card declined
History: 17/18 successful
Activity: High
Recovery probability: 87%
```

AI selects an allowed recovery action, the simulator executes it, verification confirms success, and the dashboard shows recovered revenue.

Then compare the batch result against the rule-based baseline.

---

## 24. Success Metrics

### Business
- Revenue recovered
- Recovery rate
- Recovery ROI
- Cost per recovered payment

### AI
- Recovery prediction performance
- Decision quality
- Tool execution success
- Valid/safe decisions

### Product
- Automation rate
- Escalation rate
- Average recovery time
- Clarity of AI decisions

---

## 25. MVP Scope

Must include:
- Synthetic dataset
- Payment-event simulator
- Failed-payment detection
- Revenue-risk calculation
- Recovery probability
- AI decision engine
- At least 3 recovery strategies
- Mock action APIs
- Agent memory/state
- Payment outcome simulator
- Merchant dashboard
- Recovery case view
- Agent activity feed
- Rule-based baseline
- AI vs baseline comparison
- Live demo scenario

---

## 26. Stretch Features

Only after the MVP is stable:
- Multi-agent orchestration
- WhatsApp simulation
- Voice recovery
- Merchant-specific optimization
- A/B testing
- Continuous learning
- Advanced incentive optimization
- Authorized payment-provider integration

---

## 27. Product Differentiator

RecoverAI is not:

> “An AI chatbot that sends payment reminders.”

It is:

> **“An autonomous revenue recovery engine that determines the economically appropriate action for each failed payment, executes the action through controlled tools, verifies the outcome, and measures the revenue recovered.”**

---

## 28. Definition of Done

The product is ready when:
- The complete recovery workflow works.
- Synthetic data is generated and persisted.
- Failed payments create recovery cases.
- Recovery probability can be calculated.
- AI selects an allowed strategy.
- Tool calls are validated.
- Actions execute through the simulator.
- Payment results are verified.
- Recovered revenue is calculated from verified results.
- Dashboard metrics are database-driven.
- Agent memory works.
- Baseline comparison works.
- Security rules are enforced.
- Critical tests pass.
- Public demo works.
- Documentation matches implementation.

---

## 29. North Star

> **A payment failed. RecoverAI understands the situation, predicts the likelihood of recovery, chooses the best action, safely executes it, verifies the payment, and proves how much revenue was recovered.**
