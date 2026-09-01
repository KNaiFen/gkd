from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from gkd_main.orchestrator import TrustedMainStageFacade
from gkd_task.errors import TaskError
from tests.runtime_bridge.helpers import BUNDLE_ROOT, init_repo, bundle_digest


class StageFacadeContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="gkd-stage-facade-")
        self.root = Path(self.temporary.name)
        self.production = self.root / "production"
        self.production.mkdir()
        self.project = self.root / "project"
        init_repo(self.project)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_default_transition_validates_without_manual_digest(self) -> None:
        TrustedMainStageFacade(BUNDLE_ROOT).transition(
            self.project, self.production, refresh=True
        )
        result = TrustedMainStageFacade(BUNDLE_ROOT).transition(
            self.project, self.production
        )
        self.assertEqual("verified", result["status"])
        self.assertEqual(bundle_digest(), result["executionBundleDigest"])

    def test_refresh_is_idempotent_and_preserves_drift(self) -> None:
        first = TrustedMainStageFacade(BUNDLE_ROOT).transition(
            self.project, self.production, refresh=True
        )
        self.assertEqual("refreshed", first["status"])
        second = TrustedMainStageFacade(BUNDLE_ROOT).transition(
            self.project, self.production, refresh=True
        )
        self.assertEqual("refreshed", second["status"])
        unknown = self.project / ".codex" / "unexpected.toml"
        unknown.write_text("unexpected = true\n", encoding="utf-8")
        before = unknown.read_bytes()
        with self.assertRaisesRegex(TaskError, "PROJECT_STAGE_DRIFT"):
            TrustedMainStageFacade(BUNDLE_ROOT).transition(
                self.project, self.production, refresh=True
            )
        self.assertEqual(before, unknown.read_bytes())


if __name__ == "__main__":
    unittest.main()
