"""
CivicShield Backend — FastAPI entry point.

This file creates the FastAPI application and registers a single /health
endpoint so we can verify the server starts correctly. Features will be
added in later phases.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="CivicShield",
    description="Safety-governed agentic AI for simulated clinic incident response",
    version="0.1.0",
)

# Allow the React dev server (port 5173) to call our API without CORS errors.
# In production you'd lock this down; for local development this is fine.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Simple liveness probe. Returns 200 with a status message."""
    return {"status": "ok", "service": "civicshield-backend"}

