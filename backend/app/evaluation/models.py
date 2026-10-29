"""
Pydantic models for evaluation metrics, scenario runs, and baseline comparisons.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class EvaluationScenario(str, Enum):
    """The four benchmark evaluation scenarios."""
    INVALID_DB_CONFIG = "invalid_db_config"
    DB_UNAVAILABLE = "db_unavailable"
    HIGH_LATENCY = "high_latency"
    ADVERSARIAL_UNSAFE = "adversarial_unsafe"


class RunResult(BaseModel):
    """Record of a single scenario execution by either CivicShield or the Baseline."""
    scenario: EvaluationScenario
    system: str  # "CivicShield" or "RestartBaseline"
    recovered: bool
    root_cause_correct: bool
    unsafe_rejected: bool
    attempts_used: int
    unnecessary_attempts: int
    execution_time_ms: float
    details: str


class SystemBenchmarkMetrics(BaseModel):
    """Aggregated quantitative performance metrics for a system."""
    system_name: str
    total_scenarios: int
    recovery_success_rate: float = Field(description="Percentage of incidents successfully resolved (0-100%)")
    root_cause_accuracy: float = Field(description="Percentage of incidents with correct root-cause isolated (0-100%)")
    unsafe_action_rejection_rate: float = Field(description="Percentage of unsafe actions blocked (0-100%)")
    total_unnecessary_attempts: int = Field(description="Count of futile or misdirected repair actions")
    avg_attempts_to_recover: float = Field(description="Average attempts used on successful recoveries")


class EvaluationReport(BaseModel):
    """Consolidated benchmark evaluation report comparing CivicShield vs Baseline."""
    generated_at: datetime
    sample_size: int
    limitations: str
    civicshield_metrics: SystemBenchmarkMetrics
    baseline_metrics: SystemBenchmarkMetrics
    scenario_runs: list[RunResult]

