# CivicShield
### A Safety-Governed Agentic AI System for Recovering Essential Digital Services

CivicShield is a learning prototype that demonstrates how AI agents can investigate software failures, recommend recovery actions, and safely recover a **simulated clinic appointment service**.

The goal is to help small service providers understand how routine technical incidents could be handled when a developer is not immediately available. CivicShield combines AI-driven investigation with fixed safety rules, automated verification, and human oversight when needed.

> **Project status:** Planned prototype / under development. CivicShield currently targets a local simulator. It is not a production hospital system and must not be connected to real patient data or real infrastructure.

## The problem

A clinic's appointment website may stop working because of a configuration error, an unavailable dependency, or slow responses. Someone must identify the cause, choose a fix, and check that the service works again. Smaller organisations may not have a technical person available at all hours.

CivicShield explores whether an agentic system can help with this process while keeping risky actions under control.

## How it works

1. **Detect:** The simulated clinic service reports a failure through health checks and logs.
2. **Investigate:** An AI agent reviews the available evidence and chooses from a fixed set of diagnostic tools.
3. **Plan:** The agent proposes a recovery action and explains the evidence behind it.
4. **Check safety:** A deterministic Python safety governor checks the action against an allowlist and the current policy.
5. **Recover:** If permitted, the system applies the action to the simulator—not to a real service.
6. **Verify:** Automated checks test service health and a synthetic appointment booking.
7. **Decide:** CivicShield records success, gathers more evidence, retries within a strict limit, or escalates the incident.

The language model helps interpret evidence and plan. Python remains responsible for safety checks, executing permitted actions, and deciding whether verification passed.

## Risk-based autonomy and Human-in-the-Loop

CivicShield is designed around three operating modes:

| Mode | Behaviour |
|---|---|
| **Shadow Mode** | Investigates and recommends actions but does not execute repairs. Useful for evaluating decisions safely. |
| **Supervised Mode** | Pauses for a human to approve or reject a proposed repair before it runs. |
| **Autonomous Mode** | Executes only predefined, low-risk, reversible actions that pass the safety rules. It escalates uncertain or risky cases. |

Human involvement is risk-based, not required for every action. If no operator is available, CivicShield may perform an approved routine recovery in Autonomous Mode. It must not perform a prohibited action just because a person is unavailable—or because a person approves it.

## Example demonstration

A simulated clinic appointment service begins failing after a configuration change.

- CivicShield detects the rise in failed bookings.
- The investigator checks recent logs, service health, and configuration.
- The planner proposes restoring the last-known-good configuration.
- The safety governor checks that the action is permitted.
- In Autonomous Mode, the simulator applies the approved repair.
- CivicShield reruns health checks and a synthetic booking test.
- The dashboard shows the evidence, decision, action, and actual verification result.

A second scenario can make the planner propose a destructive action, such as deleting the database. The safety governor must reject it and record the rejection.

## Technology stack

- **Python** — simulation, diagnostic tools, safety rules, recovery actions, and evaluation
- **FastAPI** — local API for the simulated clinic service
- **LangChain** — language-model integration and tool calling
- **LangGraph** — workflow state, decision branches, pauses, retries, and escalation
- **Gemini API** — optional LLM for evidence interpretation and planning
- **React + TypeScript + Vite** — interactive control-room interface
- **Tailwind CSS** — UI styling
- **pytest** — backend tests
- **Pandas / Plotly** — optional evaluation summaries and charts

The project should retain a deterministic fallback so basic simulation and safety tests can run without a live model API call.

## Safety boundaries

- Uses synthetic clinic data only.
- Runs locally against a simulated service.
- Does not connect to real hospital infrastructure or patient records.
- The LLM cannot run arbitrary shell commands, Python, or SQL.
- Recovery actions come from a fixed allowlist and are validated by Python.
- Destructive actions are always blocked.
- Recovery attempts are bounded; unresolved incidents are escalated.
- A repair is not considered successful until verification checks pass.
- API keys belong in `.env`, never in source code or Git.

These controls are part of the prototype's design. They do not establish that the system is safe for real-world clinical deployment.

## Evaluation plan

CivicShield will be compared with a simple baseline, such as a restart-only or fixed-rule recovery policy, using the same simulated scenarios.

Planned metrics include:

- **Recovery success rate:** proportion of incidents that pass verification.
- **Root-cause accuracy:** whether the identified cause matches the scenario's known cause.
- **Unsafe-action rejection rate:** proportion of prohibited proposals correctly blocked.
- **Recovery attempts:** number of attempts used before success or escalation.
- **Escalation rate:** proportion of incidents that require human attention.
- **Recovery time:** elapsed time within the simulation or test run, where measured consistently.

Results must be calculated from actual runs. Small sample sizes and simulator limitations should be reported clearly; no performance claims should be made before experiments are run.

## Getting started

The repository is being built in phases. Once the initial setup phase is complete, the intended local setup is:

1. Install Python and Node.js.
2. Create and activate a Python virtual environment.
3. Install the backend dependencies from `requirements.txt`.
4. Install the frontend dependencies with `npm install`.
5. Copy `.env.example` to `.env` and add a Gemini API key if using the hosted model.
6. Start the FastAPI backend and React frontend in separate terminals.

Exact commands and available scripts will be documented as the implementation is completed. Do not assume the application is runnable until the corresponding files and scripts exist.

## Planned project structure

```text
civicshield/
├── backend/
│   ├── simulation/     # Synthetic clinic service and fault scenarios
│   ├── agents/         # Investigation and repair planning
│   ├── tools/          # Diagnostics, safe repairs, verification
│   ├── workflow/       # LangGraph state and safety decisions
│   └── evaluation/     # Baselines, experiments, and metrics
├── frontend/           # React + TypeScript control-room UI
├── tests/              # Automated tests
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

The actual folder layout may evolve during Phase 1; keep this section aligned with the repository as it is implemented.

## Current scope and limitations

CivicShield is a course project and a proof of concept. It uses controlled, synthetic incidents rather than real hospital operations. Its simulated results cannot establish real-world uptime, clinical safety, financial savings, or suitability for production.

A future version could be tested against a non-critical service with the service owner's permission, documented recovery procedures, monitoring, access controls, and human oversight.

## Learning objectives

By building CivicShield, the developer will practise:

- Designing an agentic workflow rather than a single chatbot.
- Connecting an LLM to constrained tools using LangChain.
- Orchestrating stateful decisions and retries with LangGraph.
- Separating AI recommendations from deterministic safety enforcement.
- Implementing Human-in-the-Loop approval and risk-based autonomy.
- Testing recovery behaviour against a baseline and reporting measured results.

## License

Choose a license before publishing the repository. Do not claim a license until one has been selected and added.
