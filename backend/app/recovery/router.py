"""
FastAPI router for recovery actions, safety evaluation, verification, and audit timeline.
"""

from fastapi import APIRouter

from .executor import execute_recovery_action
from .governor import validate_recovery_proposal
from .models import (
    ActionProposal,
    AuditStage,
    AuditTimelineEntry,
    GovernorDecision,
    RecoveryCycleOutcome,
    VerificationResult,
)
from .timeline import audit_timeline
from .verifier import verify_system_recovery

router = APIRouter(prefix="/recovery", tags=["Recovery & Safety"])


@router.post("/propose-and-execute", response_model=RecoveryCycleOutcome)
def propose_and_execute_recovery(proposal: ActionProposal):
    """
    Complete governed recovery pipeline:
    1. Log proposed action to audit timeline.
    2. Evaluate proposal against deterministic Safety Governor.
    3. If approved, execute action on simulator.
    4. Run post-repair verification checks.
    5. Log all outcomes and return consolidated result.
    """
    # 1. Log Proposal
    audit_timeline.record(
        stage=AuditStage.PROPOSED,
        action_type=proposal.action_type,
        attempt_number=proposal.attempt_number,
        details={
            "rationale": proposal.rationale,
            "parameters": proposal.parameters,
            "supporting_evidence": proposal.supporting_evidence,
        },
        success=True,
    )

    # 2. Safety Governor Evaluation
    decision: GovernorDecision = validate_recovery_proposal(proposal)
    audit_timeline.record(
        stage=AuditStage.SAFETY_CHECK,
        action_type=proposal.action_type,
        attempt_number=proposal.attempt_number,
        details={
            "approved": decision.approved,
            "reason": decision.reason,
            "requires_human_escalation": decision.requires_human_escalation,
        },
        success=decision.approved,
    )

    # Rejection Branch
    if not decision.approved:
        audit_timeline.record(
            stage=AuditStage.REJECTED,
            action_type=proposal.action_type,
            attempt_number=proposal.attempt_number,
            details={"rejection_reason": decision.reason},
            success=False,
        )

        status = "REJECTED"
        if decision.requires_human_escalation:
            audit_timeline.record(
                stage=AuditStage.ESCALATED,
                action_type=proposal.action_type,
                attempt_number=proposal.attempt_number,
                details={
                    "reason": decision.reason,
                    "attempt_number": proposal.attempt_number,
                },
                success=False,
            )
            status = "ESCALATED"

        return RecoveryCycleOutcome(
            proposal=proposal,
            governor_decision=decision,
            execution_result=None,
            verification_result=None,
            overall_status=status,
        )

    # 3. Execution Branch
    exec_result = execute_recovery_action(decision, proposal)
    audit_timeline.record(
        stage=AuditStage.EXECUTED,
        action_type=proposal.action_type,
        attempt_number=proposal.attempt_number,
        details={"message": exec_result.message},
        success=exec_result.executed,
    )

    # 4. Verification Branch
    verif_result = verify_system_recovery()
    audit_timeline.record(
        stage=AuditStage.VERIFIED,
        action_type=proposal.action_type,
        attempt_number=proposal.attempt_number,
        details={
            "verified": verif_result.verified,
            "health_ok": verif_result.health_ok,
            "database_ok": verif_result.database_ok,
            "latency_ok": verif_result.latency_ok,
            "booking_test_ok": verif_result.booking_test_ok,
            "details": verif_result.details,
        },
        success=verif_result.verified,
    )

    overall_status = "SUCCESS" if verif_result.verified else "VERIFICATION_FAILED"

    return RecoveryCycleOutcome(
        proposal=proposal,
        governor_decision=decision,
        execution_result=exec_result,
        verification_result=verif_result,
        overall_status=overall_status,
    )


@router.post("/verify", response_model=VerificationResult)
def manual_verify():
    """Run verification checks on demand to inspect system health and functionality."""
    return verify_system_recovery()


@router.get("/timeline", response_model=list[AuditTimelineEntry])
def get_audit_timeline():
    """Retrieve the full chronological incident response audit timeline."""
    return audit_timeline.get_entries()


@router.post("/timeline/reset")
def reset_audit_timeline():
    """Reset the audit timeline."""
    audit_timeline.clear()
    return {"message": "Audit timeline reset successfully"}

