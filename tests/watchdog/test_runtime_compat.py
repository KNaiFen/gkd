from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import unittest

from gkd_watchdog.constants import (
    CURRENT_RUNTIME_BASELINE,
    EXPECTED_CODEX_VERSION,
    EXPECTED_SCHEMA_DIGEST,
    LEGACY_RUNTIME_BASELINE,
    RELEVANT_SCHEMA_FILES,
    RuntimeBaseline,
    RUNTIME_BASELINES,
)
from gkd_watchdog.runtime import (
    AppServerFactory,
    RuntimeVerificationError,
    SubprocessRuntimeVerifier,
)

from tests.watchdog.helpers import parsed_request


BASELINE_RECORD = (
    Path(__file__).resolve().parents[2]
    / "evidence"
    / "m-1-native-d2"
    / "compatibility-baselines.json"
)


class FakeRunner:
    def __init__(self, version: str) -> None:
        self.version = version
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, args, **kwargs):
        self.calls.append(tuple(args))
        if args[-1] == "--version":
            return subprocess.CompletedProcess(
                args, 0, stdout=f"codex-cli {self.version}\n".encode(), stderr=b""
            )
        output = Path(args[args.index("--out") + 1])
        for relative in RELEVANT_SCHEMA_FILES:
            path = output / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(relative.encode("utf-8"))
        return subprocess.CompletedProcess(args, 0, stdout=b"", stderr=b"")


class FixedResolver:
    def resolve(self) -> tuple[str, ...]:
        return ("codex",)


def fake_schema_digest() -> str:
    digest = hashlib.sha256()
    for relative in RELEVANT_SCHEMA_FILES:
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(relative.encode("utf-8"))
    return digest.hexdigest()


class RuntimeCompatibilityTests(unittest.TestCase):
    def test_legacy_aliases_still_point_to_the_historical_baseline(self) -> None:
        self.assertEqual(EXPECTED_CODEX_VERSION, LEGACY_RUNTIME_BASELINE.codex_version)
        self.assertEqual(EXPECTED_SCHEMA_DIGEST, LEGACY_RUNTIME_BASELINE.schema_digest)
        self.assertIs(RUNTIME_BASELINES[EXPECTED_CODEX_VERSION], LEGACY_RUNTIME_BASELINE)
        self.assertIs(RUNTIME_BASELINES[CURRENT_RUNTIME_BASELINE.codex_version], CURRENT_RUNTIME_BASELINE)

    def test_committed_record_matches_the_registered_baselines(self) -> None:
        record = json.loads(BASELINE_RECORD.read_text(encoding="utf-8"))
        self.assertEqual(record["schemaVersion"], 1)
        self.assertEqual(record["kind"], "gkd-runtime-compatibility-baseline")
        for entry in record["baselines"]:
            baseline = RUNTIME_BASELINES[entry["codexVersion"]]
            self.assertEqual(entry["schemaDigestSha256"], baseline.schema_digest)
            self.assertIn("protocol", entry["featureSummary"])

    def test_registered_version_accepts_matching_schema_and_request_digest(self) -> None:
        runner = FakeRunner("0.152.0")
        baseline = RuntimeBaseline("0.152.0", fake_schema_digest())
        verifier = SubprocessRuntimeVerifier(
            runner=runner,
            baselines={baseline.codex_version: baseline},
        )

        verifier.verify(("codex",), expected_schema_digest=baseline.schema_digest)
        self.assertEqual(runner.calls[0][-1], "--version")

    def test_unknown_version_requires_a_new_capture(self) -> None:
        verifier = SubprocessRuntimeVerifier(
            runner=FakeRunner("0.153.0"),
            baselines={"0.152.0": RuntimeBaseline("0.152.0", fake_schema_digest())},
        )

        with self.assertRaisesRegex(
            RuntimeVerificationError, "codex_version_unsupported"
        ):
            verifier.verify(("codex",))

    def test_registered_version_schema_drift_is_distinct_from_unknown_version(self) -> None:
        verifier = SubprocessRuntimeVerifier(
            runner=FakeRunner("0.152.0"),
            baselines={"0.152.0": RuntimeBaseline("0.152.0", "0" * 64)},
        )

        with self.assertRaisesRegex(RuntimeVerificationError, "schema_digest_mismatch"):
            verifier.verify(("codex",))

    def test_factory_rejects_request_bound_to_a_different_baseline(self) -> None:
        runner = FakeRunner("0.152.0")
        baseline = RuntimeBaseline("0.152.0", fake_schema_digest())
        calls: list[tuple[str, ...]] = []

        def forbidden_transport(argv):
            calls.append(tuple(argv))
            raise AssertionError("transport must not start")

        factory = AppServerFactory(
            FixedResolver(),
            SubprocessRuntimeVerifier(
                runner=runner,
                baselines={baseline.codex_version: baseline},
            ),
            transport_factory=forbidden_transport,
        )

        with self.assertRaisesRegex(
            RuntimeVerificationError, "runtime_baseline_mismatch"
        ):
            factory(parsed_request())
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
