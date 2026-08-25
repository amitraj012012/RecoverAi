# RecoverAI — Judge Demonstration Guide (3–5 Minutes)

---

### Executive Pitch (30 Seconds)
> "RecoverAI is an autonomous AI revenue recovery platform designed to eliminate involuntary subscription churn. When payments fail, rather than bombarding customers with dumb dunning emails, RecoverAI evaluates ML recoverability, queries adaptive agent memory, selects bounded recovery actions, executes simulated gateway workflows, and learns from real recovery outcomes."

---

### Step-by-Step Presentation Script

#### Step 1: Merchant Workspace Overview (60 Seconds)
- **Navigate to:** `http://localhost:5173/app/overview`
- **Point out:**
  1. **Revenue at Risk:** ₹1.19 Cr detected across 1,624 failed attempts in synthetic dataset.
  2. **Estimated Recoverable Revenue:** ₹92.0L calculated via explainable Phase 4 risk engine.
  3. **Simulated Recovered Revenue:** Dynamic real-time revenue recovered by autonomous agent.
  4. **Failure Reason Breakdown:** Clear categorization (Card Declined, UPI Timeout, Card Expired).

#### Step 2: Demo Case C1024 Deep-Dive (90 Seconds)
- **Navigate to:** `/app/recovery-cases`
- **Locate:** Case `rec_c1024_fail` (Customer **C1024** • ₹1,999 • Card Declined).
- **Action 1 — Explainability:** Click the **"Explain"** button:
  - Explain the **ML Recovery Score** ($87.8\%$) produced by `logistic-regression-v2`.
  - Highlight features: 18mo tenure, 88% activity score, 17/17 historical payments.
- **Action 2 — Autonomous Execution:** Click the **"Recover"** button:
  - Watch the live lifecycle progression: `ANALYZING` $\rightarrow$ `ACTION_SELECTED` (`CREATE_PAYMENT_LINK`) $\rightarrow$ `ACTION_EXECUTED` $\rightarrow$ `RECOVERED`.
  - Show the financial update: ₹1,999 credited to recovered revenue.

#### Step 3: Simulator Sandbox & Judge Scenario Controls (60 Seconds)
- **Navigate to:** `/app/simulator`
- **Show Judge Presets:**
  - **Auto:** Probabilistic outcome based on ML probability.
  - **Forced Success:** Demonstrates successful self-serve payment link completion.
  - **Forced Failure:** Demonstrates safe failure handling and remaining risk retention.
  - **Force Escalate:** Demonstrates human-in-the-loop operational escalation.
- **Batch Simulation:** Click **"Run Autonomous Batch (25 Cases)"** to show cohort processing, state updates, and dynamic revenue recovery.

#### Step 4: Adaptive Agent Memory & Continuous Learning (45 Seconds)
- **Navigate to:** `/app/ai-decisions`
- **Inspect Adaptive Memory:**
  - Click through failure clusters (`Card Expired`, `UPI Network Timeout`, `Insufficient Funds`).
  - Show the **Empirical Win-Rate** cards learned from completed simulation outcomes.
  - Explain how memory version `agent-memory-v1` reinforces high-converting strategies in future recovery decisions.

#### Step 5: Wrap-up & Data Honesty (15 Seconds)
- Point to the **Demo / Synthetic Simulation** banner.
- Reiterate strict security boundaries: 6 allowlisted strategies, max 3 retry guardrail, integer paise accounting, zero live payment rail dependencies.

---

### Key Takeaways for Judges
1. **Full Closed Loop:** Detect $\rightarrow$ Predict $\rightarrow$ Decide $\rightarrow$ Act $\rightarrow$ Settle $\rightarrow$ Learn.
2. **Defensible ML:** Calibrated stochastic model with zero data leakage.
3. **Bounded Agent:** Governed by deterministic guardrails with full auditability.
4. **Authoritative Financials:** Integer paise math with strict invariant bounds.
