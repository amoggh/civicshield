# CivicShield — 9-Phase Build Plan

> **Mission:** Build a safety-governed, hybrid Agentic AI prototype that investigates and recovers a *simulated* clinic appointment service. The project must be demonstrable, measurable, understandable to its developer, and achievable in two nights.
>
> **How to use this file:** Give your coding agent the **Global Rules** first. Then work through one phase at a time, pasting only that phase's prompt. Do not ask the agent to implement all nine phases at once.

## Global Rules for the Coding Agent

You are my pair programmer and tutor, not an autonomous code generator. Implement only the current phase. Before coding, briefly explain the plan and identify any assumptions. Keep changes small and show me which files changed.

### Fixed technology choices
- **Backend:** Python, FastAPI, Pydantic
- **Agent framework:** LangChain + LangGraph
- **Model:** Gemini through `langchain-google-genai`, loaded from `.env`
- **Frontend:** React + TypeScript + Vite, with Tailwind CSS
- **Charts/UI:** Use a lightweight chart library only if needed; prefer a polished, responsive dashboard over unnecessary dependencies.
- **Testing:** pytest for backend tests; frontend build/lint checks where available
- **Persistence:** Local JSON or SQLite only if genuinely needed; no cloud database
- **Development:** Windows-friendly PowerShell commands

### Safety and scope
- All incidents, users, appointments, logs, and repairs are **synthetic**.
- Never connect to or modify a real clinic, production service, real patient data, or external infrastructure.
- Do not let the LLM run shell commands, arbitrary Python, SQL, or unrestricted tools.
- The LLM may recommend a diagnosis, select from a fixed list of diagnostic tools, and propose a recovery action from a fixed allowlist.
- Python validates every proposed action against deterministic rules before execution.
- Never implement real database deletion. Unsafe proposals must be rejected and logged.
- Limit investigation/recovery loops (maximum 3 recovery attempts). If unresolved, stop and clearly escalate.
- Keep API keys in `.env`; never print or commit secrets. Add `.env` to `.gitignore`.
- Do not invent experiment results. Calculate metrics from actual runs.
- Do not silently add dependencies or rewrite working code. Explain why a new dependency is needed.
- If something fails, explain the likely cause and help me debug it before moving on.

### Learning agreement: equal work
For every phase:
1. **Coding agent:** implement the smallest working slice, add/update tests, and explain important code in plain language.
2. **Me (the student):** complete the “My work” items before accepting the phase. I should run commands, inspect code, answer the checkpoint question in my own words, and make at least one small change myself.
3. The agent must not mark a phase complete until its acceptance criteria pass and I can explain the checkpoint.
4. Prefer readable code over clever abstractions. Add comments only where they clarify a non-obvious decision.
5. At the end of a phase, report: files changed, commands to run, tests/results, key concepts learned, and the next phase's prerequisites.

### Project architecture
- **Simulation:** a local fake clinic appointment API with synthetic data and controllable failures.
- **Diagnostics:** Python tools return structured evidence about health, logs, database availability, configuration, and latency.
- **AI investigator/planner:** LangChain model calls interpret evidence and choose from a fixed set of tools/actions.
- **LangGraph workflow:** maintains state and routes between investigation, planning, safety checks, simulated repair, verification, retry, and escalation.
- **Safety governor:** deterministic Python validation; it is not delegated to the LLM.
- **Frontend:** React dashboard to inject a fault, launch an investigation, and inspect the evidence/action timeline.
- **Evaluation:** compare CivicShield against a simple restart-only baseline using repeatable synthetic scenarios.

---

## Phase 1 — Project Skeleton and Environment

**Prompt to coding agent**

Inspect my existing `civicshield` folder before changing anything. Help me set up a clean backend/frontend structure for CivicShield using FastAPI and React + TypeScript + Vite + Tailwind. Create a Python virtual environment, backend dependency file, frontend package setup, `.env.example`, and `.gitignore`. Do not build features yet. Give me Windows PowerShell commands and explain what each major folder is for. Avoid overwriting existing work without asking.

**My work**
- Run the setup commands myself.
- Open the backend and frontend folders and identify their purpose.
- Create my own `.env` from `.env.example` if a model key is available; never paste the secret into chat or source code.
- Explain what a virtual environment does and why `.env` is ignored by Git.

**Acceptance criteria**
- FastAPI can start and return a simple health response.
- React development server starts and shows a basic CivicShield page.
- Backend imports work; frontend build succeeds.
- Secrets are not tracked.

**Checkpoint question:** Which process serves the API, which serves the UI, and why do we keep them separate?

---

## Phase 2 — Build the Simulated Clinic Service

**Prompt to coding agent**

Implement a minimal FastAPI service representing a fictional clinic appointment system. Use synthetic data only. Include a health endpoint, a booking-test endpoint, and an in-memory service state. Add structured logs and clear response models. Keep the service deliberately small; do not add authentication, real patient data, or a real database. Add pytest tests for the healthy state and normal booking flow.

**My work**
- Start the API and call its endpoints using the browser, `/docs`, or PowerShell.
- Read the endpoint code and explain the request/response for one booking test.
- Change one harmless synthetic service value and rerun the test.

**Acceptance criteria**
- API starts reliably.
- Health and booking-test endpoints work in the healthy state.
- Tests pass and no real personal data is used.

**Checkpoint question:** What is an endpoint, and how does the frontend or test client call it?

---

## Phase 3 — Fault Injection and Diagnostic Tools

**Prompt to coding agent**

Add controlled, reversible fault scenarios: invalid database connection configuration, simulated database unavailability, high response latency, and a deliberately unsafe repair proposal for testing the safety governor. Build deterministic Python diagnostic tools for service health, recent logs, database status, configuration comparison, and latency. Fault injection must only change the local simulator. Return structured results, not unstructured strings where practical. Add tests proving each fault is detected and can be reset.

**My work**
- Trigger each fault manually and observe how the service changes.
- Trace one diagnostic function from input to returned evidence.
- Add one test assertion of my own.

**Acceptance criteria**
- At least three operational faults can be injected and reset.
- Each diagnostic returns useful, structured evidence.
- Fault tests are repeatable and isolated.

**Checkpoint question:** Why is diagnostic evidence better than asking an AI to guess the root cause from the symptom alone?

---

## Phase 4 — Safe Recovery Actions and Verification

**Prompt to coding agent**

Implement a small allowlist of simulated recovery actions, such as restoring the last-known-good configuration, restoring a simulated dependency's availability, and resetting simulated latency. Create a deterministic safety governor that validates action names, parameters, evidence requirements, and attempt limits before execution. Explicitly reject destructive actions such as deleting data or executing arbitrary commands. Add verification checks for service health and successful synthetic bookings. Record every proposed, rejected, executed, and verified action in an audit timeline. Add tests for both successful and rejected actions.

**My work**
- Run one safe repair and one unsafe proposal.
- Explain why the safety governor must be ordinary code rather than relying only on an LLM instruction.
- Add a test confirming an unsafe action is rejected.

**Acceptance criteria**
- Only allowlisted actions can execute.
- Unsafe actions are rejected and logged.
- A repair is not marked successful until verification passes.
- Retry count is bounded.

**Checkpoint question:** What is the difference between executing a repair and proving that it worked?

---

## Phase 5 — Add the LLM Investigator and Repair Planner

**Prompt to coding agent**

Connect Gemini through `langchain-google-genai` and LangChain, reading the API key from `.env`. Implement an investigator/planner that receives structured diagnostic evidence and selects from fixed diagnostic tools or a fixed list of recovery actions. Use typed/validated outputs (for example, Pydantic schemas). The LLM must never receive unrestricted code execution or direct control of the simulator. Handle missing API keys, timeouts, malformed output, and model errors gracefully. Include a deterministic fallback mode so the demo still works without a model call. Add a small test for output validation; don't make automated tests depend on live API calls.

**My work**
- Configure the key locally if available and run one investigation.
- Inspect the prompt and output schema; explain how free-form text becomes a validated action.
- Deliberately test missing-key or fallback mode.

**Acceptance criteria**
- The model can recommend a next diagnostic or permitted recovery action from evidence.
- Invalid model output cannot bypass validation.
- No secret is printed or committed.
- Fallback mode works without an API key.

**Checkpoint question:** What does the LLM decide, and what remains under deterministic Python control?

---

## Phase 6 — Orchestrate the Workflow with LangGraph

**Prompt to coding agent**

Build a LangGraph stateful workflow that connects incident intake, diagnostic selection/execution, hypothesis update, repair planning, safety validation, simulated recovery, verification, bounded retry, and escalation. Define a clear state schema containing the incident, evidence, hypothesis, proposed action, safety decision, verification result, attempt count, and event timeline. Use conditional edges for approval/rejection and pass/fail. Cap recovery attempts at three. Avoid unnecessary multi-agent complexity: separate logical roles are enough; use multiple model calls only where they add value. Add unit tests for success, unsafe-action rejection, and exhausted retries.

**My work**
- Draw the workflow on paper from memory.
- Run one successful and one failed scenario.
- Identify one conditional edge in the code and explain what controls its branch.

**Acceptance criteria**
- The graph completes a recovery path and an escalation path.
- Unsafe actions never execute.
- Retries are bounded and the timeline preserves key decisions.
- Tests pass without requiring a live LLM.

**Checkpoint question:** What does LangGraph add that a single straight-line Python script would not provide as cleanly?

---

## Phase 7 — Build the React Control-Room UI

**Prompt to coding agent**

Build a polished, responsive React + TypeScript dashboard using the existing Vite/Tailwind setup. Include: CivicShield title and service status; scenario selector; buttons to inject/reset a fault and run an investigation; a timeline of agent observations and decisions; evidence and hypothesis panels; proposed repair and safety-governor result; verification status; and a clear escalation state. Connect it to the FastAPI backend with a small typed API client and useful loading/error states. Use a coherent visual hierarchy and restrained animations; don't fake live results or hardcode success. If a workflow is running, show actual events returned by the backend. Add basic frontend validation and ensure the production build passes.

**My work**
- Run frontend and backend in separate terminals.
- Trigger a fault from the UI and follow the request into the backend route.
- Change one visible UI detail myself (for example, a status label, spacing, or colour token).

**Acceptance criteria**
- UI can inject/reset faults and start an investigation.
- Results shown come from backend responses.
- Loading, errors, success, rejection, and escalation are distinguishable.
- Responsive layout and production build work.

**Checkpoint question:** What happens from clicking “Run Investigation” until the UI displays the result?

---

## Phase 8 — Evaluation and Baseline Comparison

**Prompt to coding agent**

Create repeatable experiments across the available synthetic fault scenarios. Compare CivicShield with a simple restart-only or fixed-rule baseline using the same initial conditions. Calculate metrics from actual runs: recovery success rate, correct root-cause identification where ground truth is known, unsafe-action rejection rate, unnecessary recovery attempts, and number of attempts to recover. Clearly label any small sample size and limitations. Store results locally as JSON or CSV and display a compact results table/chart in the UI. Make deterministic tests independent of a live LLM; if evaluating the LLM path, record model errors and distinguish them from recovery failures. Never invent or hardcode performance numbers.

**My work**
- Run the experiment script and inspect the raw output file.
- Calculate one metric by hand from the raw counts.
- Explain one case where the baseline wins or CivicShield fails.

**Acceptance criteria**
- Experiments are repeatable.
- Metrics derive from recorded runs.
- Baseline and CivicShield use comparable scenarios.
- Results and limitations are documented.

**Checkpoint question:** Why is a baseline necessary before claiming the agentic approach is better?

---

## Phase 9 — Final Hardening, Demo, and Viva Preparation

**Prompt to coding agent**

Run the full backend test suite and frontend build; fix only issues you can explain. Add a concise README with setup/run instructions, architecture, safety boundaries, example demo flow, evaluation method, actual results, and limitations. Add a Mermaid architecture/workflow diagram. Prepare a 3-minute demo script: inject a configuration fault, run the agents, show evidence, demonstrate an unsafe action being rejected, and verify recovery or escalation. Add troubleshooting notes for missing API key, model/network failure, and port conflicts. Do not claim real-world deployment or real patient impact. Do not add features unless a required acceptance criterion is failing.

**My work**
- Start the entire project from a clean terminal using the README.
- Deliver the 3-minute demo without reading the code line by line.
- Explain the role of LangChain, LangGraph, the LLM, the safety governor, and the baseline in my own words.
- Write down three limitations and two future improvements.

**Acceptance criteria**
- A clean startup works from documented instructions.
- Core tests pass and frontend builds.
- Demo shows at least one successful recovery and one rejected unsafe action.
- README reports actual measurements and clearly states the simulator's limitations.

**Checkpoint question:** If the LLM gives a confident but wrong recommendation, why can't it directly damage the simulated service?

---

## Definition of Done

CivicShield is complete when:
- A user can inject a simulated failure from the React UI.
- The system gathers evidence and uses an LLM for investigation/planning when configured.
- A deterministic governor blocks unsafe actions.
- The workflow performs a permitted simulated repair and verifies the outcome, or stops and escalates.
- The dashboard shows the real event timeline and outcome.
- A baseline comparison reports metrics computed from actual runs.
- I can explain the system and demonstrate it without blindly relying on generated code.

## Recommended working rhythm

For each phase, use this loop:

1. Paste only that phase's prompt into your coding agent.
2. Ask it to explain the proposed changes before implementation.
3. Review the files it changes; ask questions about anything unclear.
4. Run the commands and tests yourself.
5. Complete the “My work” items and answer the checkpoint question aloud.
6. Commit the working phase to Git before moving on, if Git is configured.

**Deadline rule:** If time is running out, reduce the number of scenarios or visual flourishes. Do not remove safety checks, verification, or the working end-to-end demo.
