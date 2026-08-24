from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from gkd_task.acceptance import SubprocessGitHubAdapter, accept_candidate, make_review
from gkd_task.canonical import canonical_bytes
from gkd_task.errors import TaskError
from gkd_task.runtime import RuntimeStore
from tests.task_core.helpers import REVIEWER_DIGEST, TaskRepo


ROOT = Path(__file__).resolve().parents[2]
ADAPTER = ROOT / "canonical" / "payload" / "bin" / "gkd-github-acceptance"


class GitHubAcceptanceAdapterContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="gkd-github-acceptance-")
        self.root = Path(self.temporary.name)
        self.scenario_path = self.root / "scenario.json"
        self.log_path = self.root / "requests.jsonl"
        self.state_path = self.root / "merged"
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.fake_gh = self.bin / "gh"
        self.fake_gh.write_text(
            """#!/usr/bin/env python3
import json
import os
from pathlib import Path
import sys

scenario = json.loads(Path(os.environ[\"FAKE_GH_SCENARIO\"]).read_text(encoding=\"utf-8\"))
arguments = sys.argv[1:]
method = arguments[arguments.index(\"--method\") + 1]
endpoint = next(argument for argument in arguments if argument.startswith(\"repos/\"))
with Path(os.environ[\"FAKE_GH_LOG\"]).open(\"a\", encoding=\"utf-8\") as stream:
    stream.write(json.dumps({\"arguments\": arguments, \"endpoint\": endpoint, \"method\": method}) + \"\\n\")
if scenario.get(\"failure\"):
    sys.stderr.write(scenario[\"failure\"])
    raise SystemExit(scenario.get(\"failureCode\", 1))
if method == \"PUT\" and scenario.get(\"indeterminate\"):
    Path(os.environ[\"FAKE_GH_STATE\"]).write_text(\"merged\\n\", encoding=\"utf-8\")
    sys.stderr.write(scenario.get(\"mergeStderr\", \"\"))
    raise SystemExit(75)
merged = Path(os.environ[\"FAKE_GH_STATE\"]).exists()
if method == \"PUT\":
    response = scenario[\"merge\"]
elif \"/pulls/\" in endpoint:
    response = scenario[\"mergedPull\"] if merged else scenario[\"pull\"]
elif \"check-runs\" in endpoint:
    response = scenario[\"checkRuns\"]
elif \"/statuses\" in endpoint:
    response = scenario[\"statuses\"]
else:
    raise SystemExit(2)
sys.stdout.write(json.dumps(response))
""",
            encoding="utf-8",
        )
        self.fake_gh.chmod(0o755)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _environment(self) -> dict[str, str]:
        return {
            "FAKE_GH_LOG": str(self.log_path),
            "FAKE_GH_SCENARIO": str(self.scenario_path),
            "FAKE_GH_STATE": str(self.state_path),
            "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
        }

    def _write_scenario(
        self,
        head: str,
        repository: str = "team/repository",
        base_branch: str = "main",
        head_branch: str = "task/task-alpha",
        **changes,
    ) -> None:
        pull = {
            "number": 7,
            "state": "open",
            "merged_at": None,
            "base": {"ref": base_branch, "repo": {"full_name": repository}},
            "head": {"ref": head_branch, "sha": head, "repo": {"full_name": repository}},
            "draft": False,
            "mergeable": True,
        }
        scenario = {
            "pull": pull,
            "mergedPull": {**pull, "state": "closed", "merged_at": "2026-01-02T03:04:05Z", "mergeable": False},
            "checkRuns": {
                "total_count": 1,
                "check_runs": [{"name": "contract", "status": "completed", "conclusion": "success", "head_sha": head}],
            },
            "statuses": [],
            "merge": {"merged": True, "sha": "f" * 40, "message": "merged"},
        }
        scenario.update(changes)
        self.scenario_path.write_text(json.dumps(scenario), encoding="utf-8")

    def _invoke(self, request: dict[str, object]) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            (sys.executable, "-B", str(ADAPTER)),
            input=canonical_bytes(request),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, **self._environment()},
            check=False,
        )

    def _requests(self) -> list[dict[str, object]]:
        if not self.log_path.exists():
            return []
        return [json.loads(line) for line in self.log_path.read_text(encoding="utf-8").splitlines()]

    def test_snapshot_maps_rest_merged_and_writes_canonical_newline(self) -> None:
        head = "a" * 40
        self._write_scenario(head)
        result = self._invoke({"operation": "snapshot", "repository": "github.com/team/repository", "prNumber": 7})
        self.assertEqual(0, result.returncode)
        self.assertEqual(b"", result.stderr)
        snapshot = json.loads(result.stdout)
        self.assertEqual(result.stdout, canonical_bytes(snapshot))
        self.assertEqual("open", snapshot["state"])
        self.assertEqual([{"name": "contract", "status": "success"}], snapshot["checks"])

        self.state_path.write_text("merged\n", encoding="utf-8")
        merged = self._invoke({"operation": "snapshot", "repository": "github.com/team/repository", "prNumber": 7})
        self.assertEqual(0, merged.returncode)
        snapshot = json.loads(merged.stdout)
        self.assertEqual("merged", snapshot["state"])
        self.assertEqual(head, snapshot["mergedHead"])
        self.assertEqual([], snapshot["checks"])

    def test_merge_uses_expected_head_and_squash(self) -> None:
        head = "b" * 40
        self._write_scenario(head)
        result = self._invoke(
            {"operation": "merge", "repository": "github.com/team/repository", "prNumber": 7, "expectedHead": head}
        )
        self.assertEqual(0, result.returncode)
        self.assertEqual({"mergedHead": head, "status": "merged"}, json.loads(result.stdout))
        request = self._requests()[-1]
        self.assertEqual("PUT", request["method"])
        self.assertEqual("repos/team/repository/pulls/7/merge", request["endpoint"])
        self.assertIn(f"sha={head}", request["arguments"])
        self.assertIn("merge_method=squash", request["arguments"])

    def test_gh_stderr_never_reaches_adapter_output(self) -> None:
        self._write_scenario("c" * 40, failure="ghp_aaaaaaaaaaaaaaaaaaaa\n", failureCode=1)
        result = self._invoke({"operation": "snapshot", "repository": "github.com/team/repository", "prNumber": 7})
        self.assertEqual(1, result.returncode)
        self.assertEqual(b"", result.stdout)
        self.assertEqual(b"", result.stderr)

    def test_head_drift_blocks_before_merge(self) -> None:
        repo = TaskRepo()
        self.addCleanup(repo.close)
        _, candidate_head = repo.delivered()
        drift_head = "d" * 40
        self._write_scenario(drift_head, base_branch=repo.base_branch, head_branch=repo.task_branch)
        review = make_review(repo.task_id, candidate_head, "acceptor", REVIEWER_DIGEST, "accepted", [])
        with patch.dict(os.environ, self._environment(), clear=False):
            adapter = SubprocessGitHubAdapter(ADAPTER)
            with self.assertRaisesRegex(TaskError, "PR_FACT_MISMATCH"):
                accept_candidate(
                    repo.main,
                    repo.candidate,
                    repo.task_path,
                    repo.identity,
                    7,
                    candidate_head,
                    ["contract"],
                    review,
                    adapter,
                    "acceptor",
                    True,
                    runtime=RuntimeStore(repo.runtime_root),
                )
        self.assertNotIn("PUT", [request["method"] for request in self._requests()])

    def test_exit_75_reconciles_without_a_second_merge(self) -> None:
        repo = TaskRepo()
        self.addCleanup(repo.close)
        _, candidate_head = repo.delivered()
        self._write_scenario(
            candidate_head,
            base_branch=repo.base_branch,
            head_branch=repo.task_branch,
            indeterminate=True,
            mergeStderr="ghp_aaaaaaaaaaaaaaaaaaaa\n",
        )
        review = make_review(repo.task_id, candidate_head, "acceptor", REVIEWER_DIGEST, "accepted", [])
        with patch.dict(os.environ, self._environment(), clear=False):
            result = accept_candidate(
                repo.main,
                repo.candidate,
                repo.task_path,
                repo.identity,
                7,
                candidate_head,
                ["contract"],
                review,
                SubprocessGitHubAdapter(ADAPTER),
                "acceptor",
                True,
                runtime=RuntimeStore(repo.runtime_root),
            )
        self.assertTrue(result["merged"])
        self.assertEqual(1, [request["method"] for request in self._requests()].count("PUT"))


if __name__ == "__main__":
    unittest.main()
