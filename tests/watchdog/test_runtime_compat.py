from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import unittest
from unittest import mock

from gkd_watchdog.constants import (
    FEATURE_REMOVED,
    CURRENT_RUNTIME_BASELINE,
    EXPECTED_CODEX_VERSION,
    EXPECTED_SCHEMA_DIGEST,
    LEGACY_RUNTIME_BASELINE,
    RELEVANT_SCHEMA_FILES,
    RuntimeBaseline,
    RUNTIME_BASELINES,
    RUNTIME_FEATURE_REGISTRY,
    STEER_FEATURE,
)
from gkd_watchdog.runtime import (
    AppServerFactory,
    CAPABILITY_COMPATIBILITY_ONLY,
    CAPABILITY_UNSUPPORTED,
    RuntimeVerificationError,
    SubprocessRuntimeVerifier,
    parse_initialize_response,
    runtime_feature_status,
)

from tests.watchdog.helpers import parsed_request


BASELINE_RECORD = (
    Path(__file__).resolve().parents[2]
    / "evidence"
    / "m-1-native-d2"
    / "compatibility-baselines.json"
)
FEATURE_REGISTRY_RECORD = (
    Path(__file__).parent / "fixtures" / "feature-registry-0.152.0.json"
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
    @staticmethod
    def _initialize_response(**overrides):
        value = {
            "codexHome": "<redacted>",
            "platformFamily": "unix",
            "platformOs": "macos",
            "userAgent": "gkd-capability-probe/0.152.0 (redacted)",
        }
        value.update(overrides)
        return value

    def test_initialize_response_requires_current_schema_metadata(self) -> None:
        facts = parse_initialize_response(self._initialize_response())
        self.assertEqual("<redacted>", facts.codex_home)
        self.assertEqual("unix", facts.platform_family)
        self.assertEqual("macos", facts.platform_os)
        self.assertIn("0.152.0", facts.user_agent)
        self.assertEqual(CAPABILITY_UNSUPPORTED, facts.capability_status)
        self.assertEqual("capabilities_missing", facts.capability_reason)

        for malformed in (
            {},
            {**self._initialize_response(), "platformOs": None},
            {**self._initialize_response(), "userAgent": 1},
        ):
            with self.subTest(malformed=malformed), self.assertRaisesRegex(
                RuntimeVerificationError, "initialize_response_invalid"
            ):
                parse_initialize_response(malformed)

    def test_initialize_capability_type_drift_is_unsupported(self) -> None:
        for value, reason in (
            (None, "capabilities_null"),
            ([], "capabilities_type"),
            ({"experimentalApi": "true"}, "capability_value_type"),
            ({"futureApi": True}, "capabilities_uncaptured"),
            ({1: True}, "capability_name_type"),
        ):
            with self.subTest(value=value):
                facts = parse_initialize_response(
                    self._initialize_response(capabilities=value)
                )
                self.assertEqual(CAPABILITY_UNSUPPORTED, facts.capability_status)
                self.assertEqual(reason, facts.capability_reason)

    def test_legacy_capability_fixture_remains_compatibility_only(self) -> None:
        fixture = json.loads(
            (Path(__file__).parent / "fixtures" / "initialize-0.147.0-compatibility.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(CAPABILITY_COMPATIBILITY_ONLY, fixture["capabilityStatus"])
        self.assertEqual([], fixture["capabilityNames"])

    def test_feature_registry_distinguishes_schema_presence_from_current_callability(self) -> None:
        fixture = json.loads(FEATURE_REGISTRY_RECORD.read_text(encoding="utf-8"))
        self.assertEqual("0.152.0", fixture["codexVersion"])
        self.assertEqual("removed", fixture["features"]["steer"]["status"])
        self.assertEqual(["turn/steer"], fixture["schemaMethods"])
        self.assertEqual("unsupported", fixture["runtimeAvailability"])
        self.assertEqual(
            FEATURE_REMOVED,
            RUNTIME_FEATURE_REGISTRY[CURRENT_RUNTIME_BASELINE.codex_version][
                STEER_FEATURE
            ],
        )
        self.assertEqual(
            FEATURE_REMOVED,
            runtime_feature_status(CURRENT_RUNTIME_BASELINE.schema_digest, STEER_FEATURE),
        )
        self.assertEqual(
            "compatibility-only",
            runtime_feature_status(LEGACY_RUNTIME_BASELINE.schema_digest, STEER_FEATURE),
        )

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
            initialize = entry["featureSummary"]["initialize"]
            self.assertEqual(
                ["codexHome", "platformFamily", "platformOs", "userAgent"],
                initialize["responseFields"],
            )
            self.assertEqual(
                "compatibility-only"
                if entry["codexVersion"] == LEGACY_RUNTIME_BASELINE.codex_version
                else "unsupported",
                initialize["capabilityStatus"],
            )
            turn_steer = entry["featureSummary"]["turnSteer"]
            self.assertTrue(turn_steer["schemaPresence"])
            self.assertEqual(
                "compatibility-only"
                if entry["codexVersion"] == LEGACY_RUNTIME_BASELINE.codex_version
                else "removed",
                turn_steer["status"],
            )

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

    def test_verifier_prefers_removed_feature_over_request_digest_mismatch(self) -> None:
        runner = FakeRunner("0.152.0")
        baseline = RuntimeBaseline("0.152.0", fake_schema_digest())
        verifier = SubprocessRuntimeVerifier(
            runner=runner,
            baselines={baseline.codex_version: baseline},
        )

        with mock.patch(
            "gkd_watchdog.runtime.runtime_feature_status",
            return_value=FEATURE_REMOVED,
        ), self.assertRaisesRegex(RuntimeVerificationError, "turn_steer_unsupported"):
            verifier.verify(("codex",), expected_schema_digest="0" * 64)

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

    def test_factory_rejects_removed_current_steer_before_transport(self) -> None:
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
        request = parsed_request(
            runtimeEvidenceDigest=CURRENT_RUNTIME_BASELINE.schema_digest
        )

        with self.assertRaisesRegex(
            RuntimeVerificationError, "turn_steer_unsupported"
        ):
            factory(request)
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
