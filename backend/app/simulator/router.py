"""
API endpoints for simulator fault control and safety validation.
"""

from fastapi import APIRouter

from .faults import fault_manager
from .models import (
    FaultInjectionRequest,
    FaultStatusResponse,
    ProposedAction,
    SafetyValidationResult,
    validate_proposed_action,
)

router = APIRouter(prefix="/simulator", tags=["Simulator"])


@router.get("/faults", response_model=FaultStatusResponse)
def get_fault_status():
    """Retrieve currently active fault injections."""
    return fault_manager.get_status()


@router.post("/faults/inject", response_model=FaultStatusResponse)
def inject_fault(req: FaultInjectionRequest):
    """Inject a simulated operational fault."""
    fault_manager.inject(req.fault_type, req.params)
    return fault_manager.get_status()


@router.post("/faults/reset", response_model=FaultStatusResponse)
def reset_faults():
    """Reset all active faults and restore baseline configuration."""
    fault_manager.reset()
    return fault_manager.get_status()


@router.post("/safety/validate", response_model=SafetyValidationResult)
def validate_action(proposal: ProposedAction):
    """
    Test proposed repair action against deterministic safety rules.
    Used for verifying that unsafe proposals (e.g. drop_database) are blocked.
    """
    return validate_proposed_action(proposal)

