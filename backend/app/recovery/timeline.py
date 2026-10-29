"""
In-memory Audit Timeline for CivicShield.

Maintains an immutable chronological record of every:
- PROPOSED action
- SAFETY_CHECK decision
- REJECTED proposal
- EXECUTED recovery step
- VERIFIED validation outcome
- ESCALATED incident event
"""

from datetime import datetime, timezone
import logging
from typing import Any
import uuid

from .models import AuditStage, AuditTimelineEntry

logger = logging.getLogger("civicshield.recovery.timeline")


class AuditTimeline:
    """Stores the chronological history of all recovery events for audit and dashboard display."""

    def __init__(self) -> None:
        self.entries: list[AuditTimelineEntry] = []

    def record(
        self,
        stage: AuditStage,
        action_type: str,
        attempt_number: int,
        details: dict[str, Any],
        success: bool,
    ) -> AuditTimelineEntry:
        """Append an entry to the audit timeline."""
        entry = AuditTimelineEntry(
            id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(timezone.utc),
            stage=stage,
            action_type=action_type,
            attempt_number=attempt_number,
            details=details,
            success=success,
        )
        self.entries.append(entry)
        logger.info(
            "AUDIT [%s] action=%s attempt=%d success=%s | %s",
            stage.value,
            action_type,
            attempt_number,
            success,
            details.get("reason") or details.get("message") or details.get("details", ""),
        )
        return entry

    def get_entries(self) -> list[AuditTimelineEntry]:
        """Return all timeline entries in chronological order."""
        return list(self.entries)

    def clear(self) -> None:
        """Clear timeline entries (used for resetting tests)."""
        self.entries.clear()
        logger.info("Audit timeline cleared.")


# Global singleton instance
audit_timeline = AuditTimeline()

