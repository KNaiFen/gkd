from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest

from gkd_task.acceptance import MergeIndeterminate, SubprocessGitHubAdapter
from gkd_task.canonical import canonical_bytes


ROOT = Path(__file__).resolve().parents[2]
ADAPTER = ROOT / "canonical" / "payload" / "bin" / "gkd-github-accept"
REPOSITORY = "github.com/acme/widgets"
HEAD = "a" * 40


class GitHubAcceptanceAdapterContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="gkd-accept-adapter-")
        self.root = Path(self.temporary.name)
        self.scenario = self.root / "scenario.json"
        self.calls = self.root / "calls.json"
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        python = bin_dir / "python3"
        python.symlink_to(Path(sys.executable))
        gh = bin_dir / "gh"
        gh.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, sys\n"
            "from pathlib import Path\n"
            "scenario = json.loads(Path(os.environ['GKD_ACCEPT_SCENARIO']).read_text(encoding='utf-8'))\n"
            "calls_path = Path(os.environ['GKD_ACCEPT_CALLS'])\n"
            "calls = json.loads(calls_path.read_text(encoding='utf-8')) if calls_path.exists() else []\n"
            "calls.append(sys.argv[1:])\n"
            "calls_path.write_text(json.dumps(calls), encoding='utf-8')\n"
            "if len(sys.argv) < 7 or sys.argv[1:6] != ['api', '--method', sys.argv[3], '-H', 'Accept: application/vnd.github+json']:\n"
            "    raise SystemExit(3)\n"
            "method, endpoint = sys.argv[3], sys.argv[6]\n"
            "if scenario.get('transportFailure'):\n"
            "    sys.stderr.write('Bearer fixture-secret /private/error\\n')\n"
            "    raise SystemExit(1)\n"
            "if method == 'GET' and '/commits/' in endpoint and '/check-runs?' in endpoint:\n"
            "    value = scenario['checks']\n"
            "elif method == 'GET' and '/pulls/' in endpoint:\n"
            "    value = scenario['pull']\n"
            "elif method == 'PUT' and endpoint.endswith('/merge'):\n"
            "    if scenario.get('mergeExit'):\n"
            "        sys.stderr.write('Bearer fixture-secret /private/error\\n')\n"
            "        raise SystemExit(scenario['mergeExit'])\n"
            "    value = scenario['merge']\n"
            "else:\n"
            "    raise SystemExit(4)\n"
            "sys.stdout.write(json.dumps(value, sort_keys=True))\n",
            encoding="utf-8",
        )
        gh.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        self.environment = dict(os.environ)
        self.environment.update(
            {
                "GKD_ACCEPT_SCENARIO": os.fspath(self.scenario),
                "GKD_ACCEPT_CALLS": os.fspath(self.calls),
                "PATH": f"{bin_dir}{os.pathsep}{self.environment['PATH']}",
                "PYTHONDONTWRITEBYTECODE": "1",
            }
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _pull(self, *, state: str = "open", merged: bool = False) -> dict[str, object]:
        return {
            "base": {"ref": "main", "repo": {"full_name": "acme/widgets"}},
            "draft": False,
            "head": {"ref": "task/adapter", "repo": {"full_name": "acme/widgets"}, "sha": HEAD},
            "mergeable": True,
            "merged": merged,
            "number": 7,
            "state": state,
        }

    def _write_scenario(self, **overrides: object) -> None:
        value: dict[str, object] = {
            "pull": self._pull(),
            "checks": {
                "check_runs": [
                    {"conclusion": "success", "head_sha": HEAD, "name": "GKD Verify", "status": "completed"}
                ],
                "total_count": 1,
            },
            "merge": {"merged": True, "sha": "b" * 40},
        }
        value.update(overrides)
        self.scenario.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")

    def _adapter(self) -> SubprocessGitHubAdapter:
        before = dict(os.environ)
        os.environ.clear()
        os.environ.update(self.environment)
        self.addCleanup(lambda: (os.environ.clear(), os.environ.update(before)))
        return SubprocessGitHubAdapter(ADAPTER)

    def test_snapshot_is_canonical_and_uses_rest_pull_and_checks(self) -> None:
        self._write_scenario()
        snapshot = self._adapter().snapshot(REPOSITORY, 7)
        self.assertEqual(
            {
                "repository": REPOSITORY,
                "prNumber": 7,
                "baseBranch": "main",
                "headBranch": "task/adapter",
                "headSha": HEAD,
                "state": "open",
                "draft": False,
                "mergeable": True,
                "checks": [{"name": "GKD Verify", "status": "success"}],
                "mergedHead": None,
            },
            snapshot,
        )
        self.assertEqual(
            [
                ["api", "--method", "GET", "-H", "Accept: application/vnd.github+json", "repos/acme/widgets/pulls/7"],
                ["api", "--method", "GET", "-H", "Accept: application/vnd.github+json", f"repos/acme/widgets/commits/{HEAD}/check-runs?per_page=100&page=1"],
            ],
            json.loads(self.calls.read_text(encoding="utf-8")),
        )

    def test_merge_is_squash_and_binds_the_exact_head(self) -> None:
        self._write_scenario()
        self.assertEqual({"status": "merged", "mergedHead": HEAD}, self._adapter().merge(REPOSITORY, 7, HEAD))
        self.assertEqual(
            [["api", "--method", "PUT", "-H", "Accept: application/vnd.github+json", "repos/acme/widgets/pulls/7/merge", "-f", "merge_method=squash", "-f", f"sha={HEAD}"]],
            json.loads(self.calls.read_text(encoding="utf-8")),
        )

    def test_rest_merged_state_maps_to_the_candidate_head(self) -> None:
        self._write_scenario(pull=self._pull(state="closed", merged=True))
        snapshot = self._adapter().snapshot(REPOSITORY, 7)
        self.assertEqual("merged", snapshot["state"])
        self.assertEqual(HEAD, snapshot["mergedHead"])
        self.assertEqual([], snapshot["checks"])

    def test_exit_75_and_transport_errors_do_not_echo_credentials(self) -> None:
        self._write_scenario(mergeExit=75)
        adapter = self._adapter()
        with self.assertRaises(MergeIndeterminate):
            adapter.merge(REPOSITORY, 7, HEAD)
        result = subprocess.run(
            [sys.executable, str(ADAPTER)],
            input=canonical_bytes({"operation": "merge", "repository": REPOSITORY, "prNumber": 7, "expectedHead": HEAD}),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.environment,
            check=False,
        )
        self.assertEqual(75, result.returncode)
        self.assertEqual(b"", result.stdout)
        self.assertNotIn(b"fixture-secret", result.stderr)

        self._write_scenario(transportFailure=True)
        failed = subprocess.run(
            [sys.executable, str(ADAPTER)],
            input=canonical_bytes({"operation": "snapshot", "repository": REPOSITORY, "prNumber": 7}),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.environment,
            check=False,
        )
        self.assertEqual(2, failed.returncode)
        self.assertEqual(b"", failed.stdout)
        self.assertNotIn(b"fixture-secret", failed.stderr)


if __name__ == "__main__":
    unittest.main()
