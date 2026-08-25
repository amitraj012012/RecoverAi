# RecoverAI — Project Memory

## 1. PROJECT IDENTITY

**Project:** RecoverAI  
**Product type:** AI-powered FinTech / Revenue Recovery platform  
**Primary purpose:** Recover revenue from failed or at-risk payments using bounded AI decision-making and controlled automated actions.

### Core product statement

> RecoverAI does not simply send payment reminders. It analyzes why a payment failed, evaluates the customer and payment context, selects the most economically appropriate recovery strategy, executes the action, verifies the result, and measures recovered revenue.

---

# 2. PROBLEM WE ARE SOLVING

Merchants lose revenue when payments fail.

A failed payment does not always mean the customer has abandoned the business.

Potential causes include:

- Temporary bank/network failures.
- Card declines.
- UPI/payment-method failures.
- Insufficient funds.
- Expired payment methods.
- Customer inactivity.
- Repeated payment failures.
- Churn behavior.

A basic system often does:

```text
Payment failed
↓
Retry
↓
Generic reminder
```

RecoverAI instead performs:

```text
Payment failed
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
Recover
↓
Measure
```

---

# 3. TARGET USER

Primary:

**Merchant / business**

Examples:

- SaaS businesses.
- Subscription businesses.
- Online education.
- Marketplaces.
- Digital services.
- Businesses with recurring payments.

Secondary:

- Finance teams.
- Revenue operations.
- Payment operations teams.

---

# 4. CORE VALUE PROPOSITION

RecoverAI helps merchants answer:

> “A payment just failed. What should we do now to maximize the probability of recovering that money without unnecessarily sacrificing margin?”

The system optimizes for:

- Revenue recovered.
- Recovery rate.
- Recovery cost.
- Recovery ROI.
- Customer experience.
- Automation rate.

---

# 5. DATA STRATEGY

## Hackathon

Use **synthetic data only**.

The project does not have access to private Razorpay merchant/customer data.

Never imply otherwise.

Demo wording:

> “Synthetic simulation — no private Razorpay/customer data used.”

## Future

The mock payment/event layer can be replaced by an authorized payment webhook/API integration.

---

# 6. CORE WORKFLOW

```text
Payment Attempt
      ↓
Failed
      ↓
Recovery Case
      ↓
Customer + Payment Analysis
      ↓
Recovery Probability
      ↓
AI Strategy Decision
      ↓
Validated Tool
      ↓
Action
      ↓
Payment Verification
      ↓
Recovered / Next Strategy / Escalation
```

---

# 7. AI MEMORY

The project memory must preserve important implementation context.

## Current architecture

- React + TypeScript frontend.
- FastAPI backend.
- PostgreSQL/Supabase database.
- ML prediction layer.
- LLM-based bounded decision agent.
- Controlled action/tool layer.
- Mock payment simulator.
- Analytics dashboard.

## Current core entities

```text
customers
payments
recovery_cases
recovery_actions
audit_events
```

## Core recovery states

```text
FAILED
ANALYZING
ACTION_SELECTED
ACTION_EXECUTED
WAITING
VERIFIED
RECOVERED
ESCALATED
```

---

# 8. AI DECISION MEMORY

For every case, remember:

- Customer ID.
- Payment ID.
- Payment amount.
- Failure reason.
- Payment method.
- Previous successful payments.
- Previous failed payments.
- Customer tenure.
- Activity score.
- Recovery probability.
- Previous recovery actions.
- Previous action results.
- Selected strategy.
- Expected recovery.
- Final result.

The agent must use previous actions to avoid repeatedly choosing an ineffective strategy.

---

# 9. ALLOWED RECOVERY STRATEGIES

```text
RETRY_PAYMENT
CREATE_PAYMENT_LINK
ALTERNATE_PAYMENT_METHOD
SEND_REMINDER
OFFER_INCENTIVE
ESCALATE_TO_HUMAN
```

The agent cannot create new arbitrary actions.

---

# 10. AI BOUNDARIES

AI can:

- Analyze context.
- Select an allowed recovery strategy.
- Explain the decision.
- Generate customer communication.
- Choose the next allowed action.

AI cannot:

- Execute arbitrary code.
- Access unrestricted databases.
- Change permissions.
- Modify financial calculations.
- Mark a payment recovered without verification.
- Bypass security.
- Create arbitrary tools.
- Override attempt limits.

Financial calculations belong to deterministic backend code.

---

# 11. IMPORTANT PRODUCT METRICS

The dashboard must eventually show:

```text
Revenue at Risk
Estimated Recoverable Revenue
Revenue Recovered
Recovery Rate
Recovery Cost
Recovery ROI
Average Recovery Time
Active Recovery Cases
```

---

# 12. BASELINE COMPARISON

The project must compare RecoverAI against a simple baseline.

### Baseline

```text
Failed payment
↓
Retry
↓
Generic reminder
```

### RecoverAI

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

Compare:

- Recovery rate.
- Revenue recovered.
- Recovery cost.
- Time to recovery.
- Escalation rate.

All hackathon results are synthetic experiment results.

---

# 13. CURRENT BUILD STRATEGY

Build phase by phase.

Do not ask Antigravity to build the entire application in one prompt.

Current phase order:

```text
0  Foundation
1  Authentication
2  Dashboard
3  Synthetic Data + CRUD
4  Revenue Risk
5  Recovery Prediction
6  AI Decision Agent
7  Action Simulator
8  Memory + State
9  Operations UI
10 AI vs Baseline
11 Analytics
12 Security
13 Testing
14 Deployment
15 Demo
16 Submission
```

---

# 14. FILES THAT CONTROL THE PROJECT

## `rules.md`

Defines:

- What technologies to use.
- What to avoid.
- AI boundaries.
- Security.
- Error handling.
- Coding standards.
- Testing.
- Antigravity rules.

## `phases.md`

Defines:

- What to build.
- Phase order.
- Requirements.
- Acceptance criteria.
- Phase gates.

## `architecture.md`

Defines:

- System architecture.
- Components.
- Folder structure.
- Tech stack.
- Database.
- APIs.
- AI layer.
- Deployment.

## `design.md`

Defines:

- UI/UX.
- Color system.
- Typography.
- Layout.
- Dashboard hierarchy.
- Responsive behavior.
- Judge-facing presentation.

## `memory.md`

Defines:

- Current project context.
- Important decisions.
- Product purpose.
- Architecture state.
- AI constraints.
- Development strategy.

---

# 15. ANTIGRAVITY MEMORY RULE

Before making changes, Antigravity should read:

```text
rules.md
architecture.md
design.md
phases.md
memory.md
```

Then it should:

1. Inspect the existing project.
2. Identify the current phase.
3. Identify what already works.
4. Modify only the current phase.
5. Follow architecture and design rules.
6. Test the changes.
7. Update project memory when a meaningful architectural/product decision changes.

---

# 16. WHAT TO REMEMBER BETWEEN PHASES

After every meaningful phase, record:

- What was completed.
- What files were changed.
- What decisions were made.
- What APIs were added.
- What database changes were made.
- What tests passed.
- What issues remain.
- What the next phase requires.

Do not store irrelevant implementation noise.

---

# 17. DEMO MEMORY

The primary demo scenario:

```text
Customer: C1024
Payment: ₹1,999
Failure: Card declined
History: 17/18 successful
Activity: High
Recovery probability: 87%

AI:
Create payment link

Result:
Payment successful

Recovered:
₹1,999
```

The batch demo then shows:

```text
Revenue at Risk
↓
AI analyzes failed payments
↓
Different strategies selected
↓
Actions executed
↓
Payments verified
↓
Recovered revenue
↓
AI vs baseline comparison
```

---

# 18. DESIGN MEMORY

Visual identity:

```text
Deep Navy     #0B1220
Electric Blue #2563EB
Emerald       #10B981
Amber         #F59E0B
Red           #EF4444
Background    #F8FAFC
Text          #0F172A
Muted         #64748B
Border        #E2E8F0
```

Primary visual feeling:

**Trustworthy + intelligent + financial + modern**

Do not make the product look like a generic AI chatbot.

---

# 19. CURRENT PRODUCT PRINCIPLES

1. Solve a real revenue problem.
2. Make AI useful, not decorative.
3. Keep AI bounded.
4. Verify financial outcomes.
5. Never fake real-world data.
6. Measure business impact.
7. Prefer simple reliable architecture.
8. Build a working core before adding advanced features.
9. Keep the demo deterministic.
10. Optimize for judge comprehension.

---

# 20. LONG-TERM PRODUCT DIRECTION

The hackathon MVP should prove the core loop:

```text
Failed Payment
→ AI Decision
→ Controlled Action
→ Verification
→ Revenue Recovered
```

Future possibilities:

- Real payment-provider webhooks.
- Merchant-specific optimization.
- More sophisticated recovery models.
- A/B testing.
- Continuous learning.
- WhatsApp/voice recovery.
- Advanced revenue forecasting.
- Multi-agent orchestration only if justified.

Do not build future features before the core recovery loop is stable.

---

# 21. MEMORY UPDATE RULE

When project decisions change, update this file.

Examples of meaningful changes:

- Tech stack change.
- Database schema change.
- AI architecture change.
- Recovery strategy change.
- New security rule.
- New product requirement.
- Major UI direction change.
- Deployment architecture change.

Do not update memory for every small CSS or variable change.

---

# 22. FINAL PROJECT NORTH STAR

RecoverAI should make the following story obvious:

> **A payment failed. Instead of blindly retrying or sending a generic reminder, RecoverAI understands the situation, chooses the best recovery action, safely executes it, verifies the payment, and proves how much revenue was recovered.**
