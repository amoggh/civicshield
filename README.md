# CivicShield: Safety-Governed Autonomous Incident Remediation

> **Disclaimer:** CivicShield is an educational, synthetic research prototype simulating a clinic appointment service. It does **not** connect to real hospital infrastructure, use real patient health data (PHI), or execute un-sandboxed operating system commands.

CivicShield is a safety-governed, hybrid Agentic AI system that investigates and resolves simulated clinic service incidents. Combining **LangChain + LangGraph** stateful orchestration with a deterministic **Safety Governor**, CivicShield guarantees that even if an underlying LLM (e.g., Google Gemini) hallucinates or recommends high-risk actions, destructive operations are mathematically blocked before execution.

---

## 1. System Architecture

```mermaid
graph TD
    UI["React + Vite Control Room UI"] -->|REST API| API["FastAPI Backend (/api/v1)"]
    
    subgraph "Core Orchestration Engine"
        API --> LG["LangGraph Stateful Workflow"]
        LG --> Node1["1. Incident Intake"]
        Node1 --> Node2["2. Diagnostic Execution"]
        Node2 --> Node3["3. LLM/Fallback Planner"]
        Node3 --> Node4["4. Deterministic Safety Governor"]
        Node4 -->|Rejected or Capped| NodeEsc["7. Human Escalation"]
        Node4 -->|Approved| Node5["5. Simulator Action Executor"]
        Node5 --> Node6["6. Verification Probe"]
        Node6 -->|Pass| Resolved["Resolved State"]
        Node6 -->|Fail & Retries < 3| Node3
        Node6 -->|Fail & Retries >= 3| NodeEsc
    end

    subgraph "Simulated Clinic Environment"
        Node2 -->|Read Status/Logs| Sim["In-Memory Clinic Service"]
        Node5 -->|Allowlisted Fixes Only| Sim
        Node6 -->|Health & Synthetic Booking| Sim
    end

    subgraph "Safety Boundary Enforcement"
        Gov["Deterministic Python Safety Governor"]
        Gov -.->|Check Allowlist| Node4
        Gov -.->|Enforce Evidence Reqs| Node4
        Gov -.->|Rate Limit (Max 3)| Node4
        Gov -.->|Deny Destructive| Node4
    end
```

### Safety Governor Enforcement Model

The LLM is strictly decoupled from the simulator environment:
1. **Typed Output Constraints:** The LLM produces a structured `PlannerRecommendation` (Pydantic), not executable code or shell commands.
2. **Deterministic Gate 1 (Allowlist):** Only 4 actions can execute: `restore_baseline_config`, `reconnect_database`, `clear_latency_delay`, and `restart_service`.
3. **Deterministic Gate 2 (Blacklist):** Any action matching patterns like `drop`, `truncate`, `delete`, `rm `, `curl`, or `eval` is immediately rejected.
4. **Deterministic Gate 3 (Evidence Pairing):** Actions must pair with corresponding diagnostic evidence (e.g., `reconnect_database` requires evidence of `db_unavailable`).
5. **Deterministic Gate 4 (Bounded Retries):** Max 3 recovery attempts per incident before mandatory human escalation.

---

## 2. Quickstart Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- *(Optional)* Gemini API Key for live LLM planning (Deterministic fallback is enabled by default if omitted)

### Installation & Startup

#### 1. Backend Setup
```bash
# From workspace root
cd backend

# Create virtual environment & install dependencies
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt

# (Optional) Set your Gemini API key in backend/.env
# GEMINI_API_KEY=your_key_here

# Run backend service
uvicorn app.main:app --reload --port 8000
```
Backend API will be accessible at: `http://localhost:8000` (Swagger docs at `/docs`).

#### 2. Frontend Setup
```bash
# In a second terminal, from workspace root
cd frontend

npm install
npm run dev
```
Frontend UI will be running at: `http://localhost:5173`.

---

## 3. Running Tests & Benchmarks

### Backend Test Suite
The backend contains 48 unit and integration tests covering the simulator, diagnostics, safety governor, LangGraph workflow, and evaluation benchmarks.
```bash
cd backend
python -m pytest tests/ -v
```

### Frontend Production Build
```bash
cd frontend
npm run build
```

### Running the Empirical Evaluation Benchmark
To run the automated comparative experiment against the baseline:
```bash
cd backend
python -m app.evaluation.runner
```
Results will be saved to `backend/app/evaluation/results.json`.

---

## 4. Empirical Evaluation Results

Comparative benchmark across 4 standardized incident scenarios (`invalid_db_config`, `db_unavailable`, `high_latency`, `unsafe_proposal_sim`):

| Evaluation Metric | CivicShield (Hybrid Agent) | Restart-Only Baseline |
| :--- | :---: | :---: |
| **Recovery Success Rate** | **100.0%** (3/3 recoverable) | **33.3%** (1/3 recoverable) |
| **Root Cause Accuracy** | **100.0%** (4/4 diagnosed) | **0.0%** (No diagnostics) |
| **Unsafe Action Block Rate**| **100.0%** (1/1 rejected) | **0.0%** (Unchecked/Blind) |
| **Futile / Unneeded Attempts**| **0 attempts** | **3 failed attempts** |
| **Mean Attempts to Recover**| **1.0 attempt** | **1.0 attempt** |

*Note: Results derived from empirical automated testing in `app.evaluation.runner` without mocked metrics.*

---

## 5. Three-Minute Live Demo Script

Follow this script for live presentations or viva defense:

### Step 1: Baseline & Normal Operation (0:00 - 0:45)
1. Open the UI at `http://localhost:5173`.
2. Observe the green **"Healthy"** badge, with the 5 diagnostic indicators reading normal (latency < 20ms, DB reachable, config matching baseline).
3. Explain: *"CivicShield monitors a simulated clinic appointment booking service where patient scheduling requires a responsive API and active database."*

### Step 2: Inject Fault & Autonomous Remediation (0:45 - 1:45)
1. In the **Scenario Selector**, select **`invalid_db_config`** (or click **Inject Database Config Drift**).
2. Point out the live diagnostic ribbon updating: Service Status shifts to **DEGRADED**, config check shows `port: 9999 (drifted)`.
3. Click **"Run CivicShield Remediation"**.
4. Observe the LangGraph execution flow in the timeline:
   - Intake captures incident.
   - Diagnostics isolate the drifted port.
   - Planner proposes `restore_baseline_config`.
   - Safety Governor approves the allowlisted action matching the evidence.
   - Simulator applies the restore.
   - Synthetic booking probe verifies end-to-end appointment creation.
   - System state returns to **HEALTHY**.

### Step 3: Demonstrating Safety Boundaries (1:45 - 2:30)
1. Select the **`unsafe_proposal_sim`** scenario.
2. Click **"Run CivicShield Remediation"**.
3. Highlight the Safety Governor card in the UI:
   - The proposed action (`drop_table_appointments` or shell execution) is flagged with **Gate Violation: Destructive command detected**.
   - The execution is halted immediately.
   - The workflow escalates to **HUMAN INTERVENTION REQUIRED**.
4. Emphasize: *"No LLM decision can execute without passing the deterministic Python safety governor."*

### Step 4: Empirical Benchmark Review (2:30 - 3:00)
1. Scroll down to the **Automated Evaluation Benchmark** card in the dashboard.
2. Explain the comparative metrics: *"Restarting services blindly recovers high latency by clearing in-memory queues, but fails 100% of configuration drift and connection errors. CivicShield achieves 100% recovery and 0 futile attempts."*

---

## 6. Troubleshooting

- **Missing `GEMINI_API_KEY`:** 
  - CivicShield automatically falls back to the deterministic heuristic planner if no API key is provided or if network calls to Google AI fail. You will see an alert noting fallback mode, but all functionality remains operable.
- **Port Conflicts:**
  - If port `8000` is occupied: `uvicorn app.main:app --port 8005 --reload` (Update `vite.config.ts` target proxy if changed).
  - If port `5173` is occupied: Vite will automatically suggest `5174`.
- **Stale State in In-Memory Simulator:**
  - Click **"Reset Simulator to Baseline"** in the UI header to restore default seed data, config, and latency.
