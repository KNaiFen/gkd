"""Trusted command resolution and version-bound app-server startup."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any, Callable, Mapping, Protocol, Sequence

from .constants import (
    FEATURE_REMOVED,
    CAPABILITY_COMPATIBILITY_ONLY,
    CAPABILITY_UNSUPPORTED,
    RELEVANT_SCHEMA_FILES,
    RUNTIME_BASELINES,
    RUNTIME_FEATURE_REGISTRY,
    RPC_TIMEOUT_MS,
    STEER_FEATURE,
    RuntimeBaseline,
)
from .jsonrpc import AppServerStartError, JsonRpcClient, SubprocessTransport


class RuntimeVerificationError(RuntimeError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def runtime_feature_status(schema_digest: str, feature: str) -> str:
    """Return the registered runtime status for a feature and schema digest."""

    for codex_version, baseline in RUNTIME_BASELINES.items():
        if baseline.schema_digest == schema_digest:
            return RUNTIME_FEATURE_REGISTRY[codex_version].get(
                feature, CAPABILITY_UNSUPPORTED
            )
    return CAPABILITY_UNSUPPORTED


INITIALIZE_REQUIRED_FIELDS = frozenset(
    {"codexHome", "platformFamily", "platformOs", "userAgent"}
)


@dataclass(frozen=True)
class InitializeFacts:
    """Safe facts extracted from one app-server initialize response.

    The current and historical captures do not contain a server capability
    advertisement.  A capability name is therefore never treated as
    supported merely because it is present in a response-shaped mapping.
    """

    codex_home: str
    platform_family: str
    platform_os: str
    user_agent: str
    capability_status: str
    capability_reason: str
    capability_names: tuple[str, ...]

    @property
    def capabilities_status(self) -> str:
        """Compatibility alias for callers using the plural field name."""

        return self.capability_status

    @property
    def capabilities(self) -> tuple[str, ...]:
        return self.capability_names


def parse_initialize_response(value: Any) -> InitializeFacts:
    """Validate the versioned initialize response without inventing support.

    ``InitializeResponse`` in the captured 0.152.0 schema has four required
    server metadata fields and no ``capabilities`` property.  Capability
    mappings from another runtime are retained only as names and classified
    unsupported until a reviewed capture registers them.
    """

    if not isinstance(value, Mapping):
        raise RuntimeVerificationError("initialize_response_invalid")
    if any(field not in value for field in INITIALIZE_REQUIRED_FIELDS):
        raise RuntimeVerificationError("initialize_response_invalid")
    metadata: dict[str, str] = {}
    for field in INITIALIZE_REQUIRED_FIELDS:
        item = value[field]
        if not isinstance(item, str) or not item:
            raise RuntimeVerificationError("initialize_response_invalid")
        metadata[field] = item

    missing = object()
    raw_capabilities = value.get("capabilities", missing)
    capability_names: tuple[str, ...] = ()
    if raw_capabilities is missing:
        capability_reason = "capabilities_missing"
    elif raw_capabilities is None:
        capability_reason = "capabilities_null"
    elif not isinstance(raw_capabilities, Mapping):
        capability_reason = "capabilities_type"
    else:
        raw_names = tuple(raw_capabilities)
        if any(not isinstance(name, str) for name in raw_names):
            capability_reason = "capability_name_type"
        else:
            names = tuple(sorted(raw_names))
            capability_names = names
            if any(not isinstance(raw_capabilities[name], bool) for name in names):
                capability_reason = "capability_value_type"
            else:
                capability_reason = "capabilities_uncaptured"

    return InitializeFacts(
        codex_home=metadata["codexHome"],
        platform_family=metadata["platformFamily"],
        platform_os=metadata["platformOs"],
        user_agent=metadata["userAgent"],
        capability_status=CAPABILITY_UNSUPPORTED,
        capability_reason=capability_reason,
        capability_names=capability_names,
    )


class CommandResolver(Protocol):
    def resolve(self) -> tuple[str, ...]: ...


class RuntimeVerifier(Protocol):
    def verify(
        self,
        command: Sequence[str],
        *,
        expected_schema_digest: str | None = None,
    ) -> None: ...


class CloseRegistrar(Protocol):
    def register_close(self, callback: Callable[[], None]) -> None: ...

    def unregister_close(self, callback: Callable[[], None]) -> None: ...


class DefaultCommandResolver:
    """Resolve one executable from trusted installation configuration."""

    def __init__(self, executable: str | None = None) -> None:
        self._configured = executable

    def resolve(self) -> tuple[str, ...]:
        configured = self._configured or os.environ.get("GKD_CODEX_EXECUTABLE")
        executable = configured or shutil.which("codex")
        if (
            not isinstance(executable, str)
            or not executable
            or "\0" in executable
            or "\n" in executable
        ):
            raise AppServerStartError()
        return (executable,)


@dataclass(frozen=True)
class RuntimeFacts:
    codex_version: str
    schema_digest: str


class SubprocessRuntimeVerifier:
    def __init__(
        self,
        *,
        runner: Callable[..., subprocess.CompletedProcess[bytes]] = subprocess.run,
        baselines: Mapping[str, RuntimeBaseline] = RUNTIME_BASELINES,
    ) -> None:
        self._runner = runner
        self._baselines = baselines

    def capture(self, command: Sequence[str]) -> RuntimeFacts:
        if not command:
            raise RuntimeVerificationError("codex_command_missing")
        try:
            version = self._runner(
                (*command, "--version"),
                shell=False,
                check=False,
                capture_output=True,
                timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RuntimeVerificationError("codex_version_unavailable") from exc
        stdout = version.stdout.decode("utf-8", errors="replace")
        match = re.fullmatch(r"codex-cli\s+([0-9.]+)\s*", stdout)
        if version.returncode != 0 or match is None:
            raise RuntimeVerificationError("codex_version_unavailable")

        with tempfile.TemporaryDirectory(prefix="gkd-watchdog-schema-") as root:
            try:
                generated = self._runner(
                    (
                        *command,
                        "app-server",
                        "generate-json-schema",
                        "--experimental",
                        "--out",
                        root,
                    ),
                    shell=False,
                    check=False,
                    capture_output=True,
                    timeout=15,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise RuntimeVerificationError("schema_generation_failed") from exc
            if generated.returncode != 0:
                raise RuntimeVerificationError("schema_generation_failed")
            digest = hashlib.sha256()
            try:
                for relative in RELEVANT_SCHEMA_FILES:
                    raw = (Path(root) / relative).read_bytes()
                    digest.update(relative.encode("utf-8"))
                    digest.update(b"\0")
                    digest.update(raw)
            except OSError as exc:
                raise RuntimeVerificationError("schema_generation_failed") from exc
        return RuntimeFacts(match.group(1), digest.hexdigest())

    def verify(
        self,
        command: Sequence[str],
        *,
        expected_schema_digest: str | None = None,
    ) -> None:
        facts = self.capture(command)
        baseline = self._baselines.get(facts.codex_version)
        if baseline is None:
            raise RuntimeVerificationError("codex_version_unsupported")
        if facts.schema_digest != baseline.schema_digest:
            raise RuntimeVerificationError("schema_digest_mismatch")
        if runtime_feature_status(facts.schema_digest, STEER_FEATURE) == FEATURE_REMOVED:
            raise RuntimeVerificationError("turn_steer_unsupported")
        if (
            expected_schema_digest is not None
            and expected_schema_digest != baseline.schema_digest
        ):
            raise RuntimeVerificationError("runtime_baseline_mismatch")


class StaticRuntimeVerifier:
    """Injectable verifier for hermetic tests; production never selects it."""

    def __init__(self, reason: str | None = None) -> None:
        self.reason = reason
        self.calls = 0

    def verify(
        self,
        command: Sequence[str],
        *,
        expected_schema_digest: str | None = None,
    ) -> None:
        self.calls += 1
        if self.reason is not None:
            raise RuntimeVerificationError(self.reason)


class AppServerFactory:
    def __init__(
        self,
        resolver: CommandResolver,
        verifier: RuntimeVerifier,
        *,
        transport_factory: Callable[[Sequence[str]], SubprocessTransport] = SubprocessTransport,
    ) -> None:
        self._resolver = resolver
        self._verifier = verifier
        self._transport_factory = transport_factory

    def __call__(
        self, _request, cancellation: CloseRegistrar | None = None
    ) -> JsonRpcClient:
        expected_schema_digest = getattr(_request, "runtime_evidence_digest", None)
        if runtime_feature_status(expected_schema_digest, STEER_FEATURE) == FEATURE_REMOVED:
            raise RuntimeVerificationError("turn_steer_unsupported")
        command = self._resolver.resolve()
        self._verifier.verify(
            command,
            expected_schema_digest=expected_schema_digest,
        )
        transport = self._transport_factory((*command, "app-server"))
        client = JsonRpcClient(transport)
        close_callback = client.close
        if cancellation is not None:
            cancellation.register_close(close_callback)
        try:
            result = client.request(
                "initialize",
                {
                    "clientInfo": {
                        "name": "gkd-watchdog",
                        "title": "GKD Watchdog",
                        "version": "1",
                    },
                    "capabilities": {},
                },
                timeout_ms=RPC_TIMEOUT_MS,
            )
            initialize_facts = parse_initialize_response(result)
            # Keep the response-derived facts attached to the session for
            # diagnostic consumers without exposing the raw initialize body.
            client.initialize_facts = initialize_facts
        except Exception:
            if cancellation is not None:
                cancellation.unregister_close(close_callback)
            client.close()
            raise
        return client


def default_app_server_factory() -> AppServerFactory:
    return AppServerFactory(DefaultCommandResolver(), SubprocessRuntimeVerifier())
