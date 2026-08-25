# RecoverAI

> **Autonomous AI-Powered Revenue Recovery Platform** • *A closed-loop system to predict recoverability, execute bounded recovery interventions, and continuously learn from synthetic payment outcomes.*

---

## 1. Problem

Payment failures in digital businesses and subscription services do not always mean lost customers or permanently lost revenue. However, merchants lack a closed-loop system to:
1. Identify and quantify recoverable payment failures in real-time.
2. Prioritize at-risk revenue based on explainable recovery probability.
3. Select an appropriate, low-friction recovery intervention tailored to the failure context.
4. Verify and settle outcomes safely without human micromanagement.
5. Continuously learn from historical recovery experiences to improve future strategy decisions.

---

## 2. Solution

RecoverAI transforms payment failure management into an autonomous, closed-loop recovery workflow:

$$\text{Detect} \longrightarrow \text{Predict} \longrightarrow \text{Decide} \longrightarrow \text{Act} \longrightarrow \text{Verify} \longrightarrow \text{Learn}$$

RecoverAI provides:
- **Revenue Risk Engine:** Detects and aggregates failed-payment financial exposure in integer paise.
- **ML Recovery Prediction:** Calibrated Logistic Regression model predicting recovery probability based on customer tenure, activity score, and failure taxonomy.
- **Adaptive Agent Memory:** Bounded retrieval of relevant historical experiences and empirical strategy win-rates.
- **Bounded Decision Engine:** Strictly allowlisted selection from 6 approved recovery strategies governed by deterministic safety guardrails.
- **Controlled Synthetic Simulator:** High-fidelity simulation of payment links, smart retries, rail updates, and ops escalations.
- **Continuous Learning:** Post-outcome memory persistence allowing future recovery decisions to benefit from verified experience.

---

## 3. Important Data Disclaimer

> [!IMPORTANT]
> **Hackathon Prototype Notice:**
> RecoverAI is an experimental hackathon prototype built and evaluated exclusively on **synthetic / demo data**.
> 
> RecoverAI does **NOT**:
> - Access real Razorpay merchant accounts or customer data.
> - Process real money, currency movement, or banking transactions.
> - Connect to live Razorpay payment gateway rails.
> - Connect to real banking infrastructure or card networks.
> - Collect, store, or process real customer payment credentials (card numbers, CVVs, or UPI PINs).
> 
> RecoverAI is not officially affiliated with or endorsed by Razorpay.

---

## 4. Architecture

RecoverAI is structured as a modular, full-stack enterprise operations platform:

- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, Recharts
- **Backend:** FastAPI (Python 3.10+), Pydantic v2, Uvicorn
- **Database:** SQLAlchemy ORM with PostgreSQL / SQLite (Supabase compatible)
- **Authentication:** Supabase Auth & JWT token verification with merchant tenant scoping
- **Machine Learning:** Scikit-Learn (`logistic-regression-v2`, customer-split calibrated model)
- **Bounded Agent:** Deterministic state machine and strategy evaluator
- **Adaptive Memory:** Merchant-scoped contextual memory (`recovery_memories`)
- **Simulator:** Controlled synthetic payment/recovery simulators with judge presets
- **Audit Ledger:** Append-only audit trail (`audit_events`)

---

## 5. Core Workflow

```
Failed Payment Ingested
          ↓
Revenue Risk Engine (Calculates Revenue at Risk & Baseline Recoverable)
          ↓
ML Recovery Prediction Engine (Generates Explainable Probability)
          ↓
Adaptive Agent Memory (Retrieves Context Cluster Empirical Rates)
          ↓
Bounded Decision Engine (Selects Allowlisted Strategy & Validates Guardrails)
          ↓
Controlled Synthetic Simulator (Executes Simulated Intervention)
          ↓
Outcome Settled (RECOVERED / ACTION_EXECUTED / ESCALATED)
          ↓
Audit Event Committed (Immutable Traceability)
          ↓
Adaptive Memory Updated (Adds New Experience to Memory Store)
```

---

## 6. Six Approved Recovery Strategies

The decision engine is strictly restricted to **6 approved recovery strategies**:

1. **`RETRY_PAYMENT`** — Scheduled gateway retry for transient network timeouts (`payment_retry_simulator`).
2. **`CREATE_PAYMENT_LINK`** — Self-serve digital payment link for expired cards and loyal users (`payment_link_simulator`).
3. **`ALTERNATE_PAYMENT_METHOD`** — Prompt to complete transaction via UPI or Netbanking (`payment_method_update_simulator`).
4. **`SEND_REMINDER`** — Courteous multi-channel payment reminder for temporary declines (`customer_notification_simulator`).
5. **`OFFER_INCENTIVE`** — Targeted retention discount for low-engagement churn risks (`incentive_offer_simulator`).
6. **`ESCALATE_TO_HUMAN`** — Safe routing to merchant operations when max retries or complex limits are met (`human_escalation_tool`).

---

## 7. Demo Case — C1024

The repository includes a reference demonstration scenario centered on customer **C1024**:
- **Payment ID:** `pay_c1024_fail`
- **Amount:** ₹1,999 (199,900 paise)
- **Failure Reason:** Card Declined (Insufficient Funds)
- **Customer Context:** 18 months tenure, 88% activity score, 17/17 historical successful payments
- **ML Model:** `logistic-regression-v2` $\longrightarrow$ **87.8% recovery probability**
- **Adaptive Memory:** Retrieves empirical win-rates from the `INSUFFICIENT_FUNDS_LOYAL_CUSTOMER` cluster
- **Agent Decision:** Selects `CREATE_PAYMENT_LINK`
- **Simulator Tool:** Dispatches `payment_link_simulator`
- **Outcome:** Resolves to `RECOVERED` with ₹1,999 credited
- **Audit & Learning:** Creates `AuditEvent` and persists experience to `recovery_memories`

*(Note: Customer C1024 and all associated metrics are synthetic demo records).*

---

## 8. Key Features

- **Merchant Workspace:** Secure multi-page dashboard with real-time financial exposure tracking.
- **Authoritative Integer Accounting:** All monetary values stored and computed in integer paise (₹1 = 100 paise) to prevent precision loss.
- **Explainability Drawer:** Visual feature contribution analysis for ML predictions.
- **Interactive Simulator Console:** Judge controls for scenario testing (`Auto`, `Forced Success`, `Forced Failure`, `Force Escalate`, `Batch Run`, `Reset`).
- **Adaptive Memory Inspector:** Real-time explorer for failure clusters and empirical win-rates.
- **Strict Merchant Isolation:** Complete tenant data separation across all endpoints.

---

## 9. Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, Recharts |
| **Backend** | FastAPI, Python 3.10+, SQLAlchemy, Pydantic v2, Uvicorn |
| **ML Engine** | Scikit-Learn, NumPy, Joblib |
| **Database** | SQLite (Dev) / PostgreSQL (Prod), Supabase Auth |
| **Testing** | Pytest, FastAPI TestClient, Vitest |

---

## 10. Project Structure

```
RecoverAi/
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI REST endpoints
│   │   ├── core/            # Security, config, logging
│   │   ├── database/        # SQLAlchemy session & init
│   │   ├── ml/              # Scikit-Learn model artifacts & training
│   │   ├── models/          # SQLAlchemy database models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   └── services/        # ML, Agent, Simulator, Memory, Risk Engine
│   ├── tests/               # 57 automated pytest test suites
│   ├── requirements.txt     # Python backend dependencies
│   └── .env.example         # Backend environment template
├── frontend/
│   ├── src/
│   │   ├── components/      # UI components & widgets
│   │   ├── context/         # AuthContext & session state
│   │   ├── layouts/         # Dashboard layout & navigation
│   │   ├── pages/           # Overview, Payments, RecoveryCases, Simulator, etc.
│   │   ├── services/        # API client integration
│   │   └── types/           # TypeScript interfaces
│   ├── package.json         # Frontend dependencies & scripts
│   └── vite.config.ts       # Vite bundler configuration
├── data/                    # Synthetic payment dataset definitions
├── docs/
│   └── DEMO_GUIDE.md        # Step-by-step judge presentation script
├── .gitignore               # Clean repository ignore rules
├── .env.example             # Project environment template
└── README.md                # Comprehensive project documentation
```

---

## 11. Installation & Local Setup

### Prerequisites
- Python 3.10 or higher
- Node.js 18 or higher & npm

### 1. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
python -m pip install -r requirements.txt
```

### 2. Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install
```

---

## 12. Environment Variables

Copy the provided `.env.example` templates to configure your local environment:

### Backend Configuration (`backend/.env` or root `.env`)
```env
ENVIRONMENT=development
DEBUG=true
PORT=8000
HOST=0.0.0.0
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DATABASE_URL=sqlite:///./recoverai.db
SECRET_KEY=recoverai_super_secret_development_jwt_key_32_chars
ALGORITHM=HS256
```

### Frontend Configuration (`frontend/.env`)
```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## 13. Database Initialization & Synthetic Data Seeding

Generate the deterministic 21,600+ synthetic transaction dataset:

```bash
cd backend
python -m app.services.data_generator
```

To reset simulation records back to baseline during demonstrations, use the in-app **"Reset Demo State"** button or run:
```bash
# Via API endpoint
curl -X POST http://localhost:8000/simulator/reset
```

---

## 14. Running the Application

### 1. Start the Backend Server
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```
- API Docs (Swagger UI): `http://localhost:8000/docs`
- Health Probe: `http://localhost:8000/health`

### 2. Start the Frontend Application
```bash
cd frontend
npm run dev
```
- Web Application: `http://localhost:5173`

---

## 15. Running Automated Tests

### Backend Test Suite (57/57 Passing)
```bash
cd backend
python -m pytest
```

### Frontend Production Build (Zero Errors)
```bash
cd frontend
npm run build
```

---

## 16. Demo Guide

For a 3–5 minute structured judge presentation walkthrough, refer to [`docs/DEMO_GUIDE.md`](docs/DEMO_GUIDE.md).

---

## 17. Security & Governance

- **Tenant Isolation:** All CRUD, ML, agent, and memory requests require authenticated JWT tokens with verified `merchant_id`.
- **No Stored Credentials:** Zero card numbers, CVVs, or bank credentials exist in code or database.
- **Bounded Tool Execution:** Only approved Python simulator functions in `tool_registry.py` can be executed.
- **Max Retry Ceiling:** Bounded agent automatically escalates cases with $\ge 3$ failed attempts.

---

## 18. License

This project is licensed under the MIT License.
