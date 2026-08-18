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
from typing import Callable, Protocol, Sequence

from .constants import (
    EXPECTED_CODEX_VERSION,
    EXPECTED_SCHEMA_DIGEST,
    RELEVANT_SCHEMA_FILES,
    RPC_TIMEOUT_MS,
)
from .jsonrpc import AppServerStartError, JsonRpcClient, SubprocessTransport


class RuntimeVerificationError(RuntimeError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class CommandResolver(Protocol):
    def resolve(self) -> tuple[str, ...]: ...


class RuntimeVerifier(Protocol):
    def verify(self, command: Sequence[str]) -> None: ...


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


@dataclass(frozen=True, slots=True)
class RuntimeFacts:
    codex_version: str
    schema_digest: str


class SubprocessRuntimeVerifier:
    def __init__(
        self,
        *,
        runner: Callable[..., subprocess.CompletedProcess[bytes]] = subprocess.run,
    ) -> None:
        self._runner = runner

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

    def verify(self, command: Sequence[str]) -> None:
        facts = self.capture(command)
        if facts.codex_version != EXPECTED_CODEX_VERSION:
            raise RuntimeVerificationError("codex_version_mismatch")
        if facts.schema_digest != EXPECTED_SCHEMA_DIGEST:
            raise RuntimeVerificationError("schema_digest_mismatch")


class StaticRuntimeVerifier:
    """Injectable verifier for hermetic tests; production never selects it."""

    def __init__(self, reason: str | None = None) -> None:
        self.reason = reason
        self.calls = 0

    def verify(self, command: Sequence[str]) -> None:
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
        command = self._resolver.resolve()
        self._verifier.verify(command)
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
            if not isinstance(result, dict):
                raise RuntimeVerificationError("initialize_response_invalid")
        except Exception:
            if cancellation is not None:
                cancellation.unregister_close(close_callback)
            client.close()
            raise
        return client


def default_app_server_factory() -> AppServerFactory:
    return AppServerFactory(DefaultCommandResolver(), SubprocessRuntimeVerifier())
