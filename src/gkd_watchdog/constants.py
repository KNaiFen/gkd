"""Frozen protocol and runtime constants for GKD-M-1B."""

SCHEMA_VERSION = 1
EXPECTED_CODEX_VERSION = "0.147.0"
EXPECTED_SCHEMA_DIGEST = (
    "ea75b7760483b70be4535b2d966e1ccd92035f6c71362a79f2cb2d54d0088bcf"
)
MAX_WAIT_MS = 43_200_000
MAX_HEALTH_INTERVAL_MS = 3_600_000
RPC_TIMEOUT_MS = 10_000
INTERRUPT_CONFIRM_TIMEOUT_MS = 10_000
MAX_RPC_ID = 2_147_483_647
MAX_MESSAGE_BYTES = 1_048_576

RELEVANT_SCHEMA_FILES = (
    "codex_app_server_protocol.v2.schemas.json",
    "v2/ThreadListParams.json",
    "v2/ThreadReadParams.json",
    "v2/ThreadReadResponse.json",
    "v2/ThreadStatusChangedNotification.json",
    "v2/TurnCompletedNotification.json",
    "v2/TurnInterruptParams.json",
    "v2/TurnSteerParams.json",
)
