"""Frozen protocol and versioned runtime compatibility constants for GKD-M-1B."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class RuntimeBaseline:
    """The schema digest and CLI version captured for one runtime baseline."""

    codex_version: str
    schema_digest: str


LEGACY_RUNTIME_BASELINE = RuntimeBaseline(
    codex_version="0.147.0",
    schema_digest="ea75b7760483b70be4535b2d966e1ccd92035f6c71362a79f2cb2d54d0088bcf",
)
CURRENT_RUNTIME_BASELINE = RuntimeBaseline(
    codex_version="0.152.0",
    schema_digest="398b3be7ac8f5135c7ed6f258e3ba0264c734715b0384539adb462b873745519",
)
RUNTIME_BASELINES: Mapping[str, RuntimeBaseline] = MappingProxyType(
    {
        LEGACY_RUNTIME_BASELINE.codex_version: LEGACY_RUNTIME_BASELINE,
        CURRENT_RUNTIME_BASELINE.codex_version: CURRENT_RUNTIME_BASELINE,
    }
)

# These names remain for the v0.1.5 historical watcher contract. New runtime
# checks must use RUNTIME_BASELINES so a single legacy digest cannot authorize a
# different CLI version.
EXPECTED_CODEX_VERSION = LEGACY_RUNTIME_BASELINE.codex_version
EXPECTED_SCHEMA_DIGEST = LEGACY_RUNTIME_BASELINE.schema_digest

SCHEMA_VERSION = 1
MAX_WAIT_MS = 43_200_000
MAX_HEALTH_INTERVAL_MS = 3_600_000
RPC_TIMEOUT_MS = 10_000
INTERRUPT_CONFIRM_TIMEOUT_MS = 10_000
MAX_RPC_ID = 2_147_483_647
MAX_MESSAGE_BYTES = 1_048_576

# Initialize capability facts are deliberately tri-state.  The current and
# historical captures only establish unsupported/compatibility-only values;
# no runtime is registered as watcher-capable here.
CAPABILITY_UNSUPPORTED = "unsupported"
CAPABILITY_COMPATIBILITY_ONLY = "compatibility-only"
CAPABILITY_SUPPORTED = "supported"
FEATURE_REMOVED = "removed"
STEER_FEATURE = "steer"

# A generated schema can retain a method after the CLI feature registry has
# retired it.  Keep this registry separate from schema presence so runtime
# callers cannot infer callability from generated request fields.
RUNTIME_FEATURE_REGISTRY: Mapping[str, Mapping[str, str]] = MappingProxyType(
    {
        LEGACY_RUNTIME_BASELINE.codex_version: MappingProxyType(
            {STEER_FEATURE: CAPABILITY_COMPATIBILITY_ONLY}
        ),
        CURRENT_RUNTIME_BASELINE.codex_version: MappingProxyType(
            {STEER_FEATURE: FEATURE_REMOVED}
        ),
    }
)

APPROVED_RUNTIME_DIGESTS = frozenset(
    baseline.schema_digest for baseline in RUNTIME_BASELINES.values()
)

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
