"""
CivicShield Backend — FastAPI entry point.

Creates the FastAPI application, registers CORS middleware, and includes
routers for each feature area. The /health endpoint is the top-level
liveness probe; the clinic service lives under /clinic/*.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.router import router as agent_router
from app.clinic.router import router as clinic_router
from app.diagnostics.router import router as diagnostics_router
from app.evaluation.router import router as evaluation_router
from app.recovery.router import router as recovery_router
from app.simulator.router import router as simulator_router
from app.workflow.router import router as workflow_router

# Configure structured logging for the whole app
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-28s | %(levelname)-5s | %(message)s",
    datefmt="%H:%M:%S",
)

app = FastAPI(
    title="CivicShield",
    description="Safety-governed agentic AI for simulated clinic incident response",
    version="0.7.0",
)

# Allow the React dev server (port 5173) to call our API without CORS errors.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(clinic_router)
app.include_router(simulator_router)
app.include_router(diagnostics_router)
app.include_router(recovery_router)
app.include_router(agent_router)
app.include_router(workflow_router)
app.include_router(evaluation_router)


@app.get("/health")
def health_check():
    """Top-level liveness probe. Returns 200 with a status message."""
    return {"status": "ok", "service": "civicshield-backend"}

