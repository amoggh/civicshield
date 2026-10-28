"""
Simulated clinic configuration state.

Defines the golden baseline configuration and tracks runtime active
configuration so diagnostics can detect configuration drift or corruption.
"""

from pydantic import BaseModel, Field


class ClinicConfig(BaseModel):
    """Configuration parameters for the clinic service and its database."""
    db_host: str = Field(default="127.0.0.1", description="Database host address")
    db_port: int = Field(default=5432, description="Database port")
    db_name: str = Field(default="clinic_records", description="Database name")
    db_pool_size: int = Field(default=10, description="Connection pool size")
    timeout_ms: int = Field(default=200, description="Max acceptable latency in ms")
    read_only_mode: bool = Field(default=False, description="Maintenance read-only flag")


# Golden baseline reference — known good state
BASELINE_CONFIG = ClinicConfig(
    db_host="127.0.0.1",
    db_port=5432,
    db_name="clinic_records",
    db_pool_size=10,
    timeout_ms=200,
    read_only_mode=False,
)

# Active runtime configuration (in-memory, modifiable by fault injection)
active_config: ClinicConfig = BASELINE_CONFIG.model_copy()


def reset_active_config() -> ClinicConfig:
    """Reset active configuration to golden baseline in-place."""
    for key, val in BASELINE_CONFIG.model_dump().items():
        setattr(active_config, key, val)
    return active_config
