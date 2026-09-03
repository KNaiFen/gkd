import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "gkd-github-watch"


class GithubWatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.tmp = Path(self.temp.name)
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        self.log = self.tmp / "gh.log"
        self.git = self.bin / "git"
        self.git.write_text(
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            "if sys.argv[1:] == ['remote', 'get-url', 'origin']:\n"
            "    if os.environ.get('FAKE_NO_ORIGIN'):\n"
            "        raise SystemExit(2)\n"
            "    print(os.environ.get('FAKE_ORIGIN', 'https://github.com/owner/repo.git'))\n"
            "    raise SystemExit(0)\n"
            "raise SystemExit(1)\n",
            encoding="utf-8",
        )
        self.git.chmod(self.git.stat().st_mode | stat.S_IXUSR)
        self.gh = self.bin / "gh"
        self.gh.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, sys, time\n"
            "log = os.environ['GH_LOG']\n"
            "with open(log, 'a', encoding='utf-8') as stream:\n"
            "    stream.write(json.dumps(sys.argv[1:]) + '\\n')\n"
            "if sys.argv[1:2] != ['api']:\n"
            "    print('write operation rejected', file=sys.stderr)\n"
            "    raise SystemExit(9)\n"
            "responses = json.loads(os.environ['GH_RESPONSES'])\n"
            "index = sum(1 for _ in open(log, encoding='utf-8')) - 1\n"
            "response = responses[min(index, len(responses) - 1)]\n"
            "if response.get('sleep'):\n"
            "    time.sleep(response['sleep'])\n"
            "if response.get('exit'):\n"
            "    print(response.get('stderr', ''), file=sys.stderr)\n"
            "    raise SystemExit(response['exit'])\n"
            "print(json.dumps(response.get('json', {})))\n",
            encoding="utf-8",
        )
        self.gh.chmod(self.gh.stat().st_mode | stat.S_IXUSR)

    def tearDown(self):
        self.temp.cleanup()

    def run_watch(self, *args, responses, origin="https://github.com/owner/repo.git", timeout=2):
        env = os.environ.copy()
        env["PATH"] = str(self.bin) + os.pathsep + env.get("PATH", "")
        env["GH_LOG"] = str(self.log)
        env["GH_RESPONSES"] = json.dumps(responses)
        if origin is None:
            env["FAKE_NO_ORIGIN"] = "1"
            env.pop("FAKE_ORIGIN", None)
        else:
            env["FAKE_ORIGIN"] = origin
            env.pop("FAKE_NO_ORIGIN", None)
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=self.tmp,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def test_all_target_endpoints_are_read_only(self):
        cases = [
            (["--pr", "7", "--repo", "owner/repo"], "/repos/owner/repo/pulls/7"),
            (["--run", "8", "--repo", "owner/repo"], "/repos/owner/repo/actions/runs/8"),
            (["--commit", "abc", "--repo", "owner/repo"], "/repos/owner/repo/commits/abc/status"),
            (["--release", "v1.0", "--repo", "owner/repo"], "/repos/owner/repo/releases/tags/v1.0"),
        ]
        payloads = [
            {"state": "closed", "merged": True},
            {"status": "completed", "conclusion": "success"},
            {"state": "success"},
            {"tag_name": "v1.0", "published_at": "2026-09-03T00:00:00Z"},
        ]
        for args, endpoint in cases:
            result = self.run_watch(*args, "--interval", "0", responses=[{"json": payloads[cases.index((args, endpoint))]}])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            call = json.loads(self.log.read_text(encoding="utf-8").splitlines()[-1])
            self.assertEqual(call, ["api", endpoint])
            self.log.unlink()

    def test_running_then_success(self):
        result = self.run_watch(
            "--run", "42", "--interval", "0", "--timeout", "1",
            responses=[
                {"json": {"status": "in_progress", "html_url": "https://example/run"}},
                {"json": {"status": "completed", "conclusion": "success", "html_url": "https://example/run"}},
            ],
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("status: success", result.stdout)
        self.assertEqual(len(self.log.read_text(encoding="utf-8").splitlines()), 2)

    def test_ssh_origin_is_normalized(self):
        result = self.run_watch(
            "--run", "43", "--interval", "0",
            origin="git@github.com:owner/repo.git",
            responses=[{"json": {"status": "completed", "conclusion": "success"}}],
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("repository: owner/repo", result.stdout)

    def test_unknown_response_structure_is_error(self):
        result = self.run_watch(
            "--run", "44", "--interval", "0",
            responses=[{"json": {"status": "mysterious"}}],
        )
        self.assertEqual(result.returncode, 3)
        self.assertIn("状态未知", result.stdout)

    def test_failure_and_failed_check_summary(self):
        result = self.run_watch(
            "--commit", "deadbeef", "--interval", "0",
            responses=[{"json": {"state": "failure", "statuses": [{"context": "lint", "state": "failure"}]}}],
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("status: failure", result.stdout)
        self.assertIn("lint: failure", result.stdout)

    def test_authentication_and_not_found_errors(self):
        for response, expected in (
            ({"exit": 1, "stderr": "HTTP 401: Bad credentials"}, "认证失败"),
            ({"exit": 1, "stderr": "HTTP 404: Not Found"}, "目标不存在"),
        ):
            result = self.run_watch("--run", "9", responses=[response])
            self.assertEqual(result.returncode, 3)
            self.assertIn(expected, result.stdout)

    def test_repo_mismatch_is_call_error(self):
        result = self.run_watch("--run", "9", "--repo", "other/repo", responses=[{"json": {}}])
        self.assertEqual(result.returncode, 3)
        self.assertIn("origin 不一致", result.stdout)
        self.assertFalse(self.log.exists())

    def test_explicit_repo_works_without_origin(self):
        result = self.run_watch(
            "--run", "11", "--repo", "owner/repo", "--interval", "0",
            origin=None,
            responses=[{"json": {"status": "completed", "conclusion": "success"}}],
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("repository: owner/repo", result.stdout)

    def test_gh_call_is_bounded_by_global_timeout(self):
        result = self.run_watch(
            "--run", "12", "--interval", "0", "--timeout", "0.5",
            responses=[{"sleep": 1, "json": {"status": "queued"}}],
        )
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("status: timeout", result.stdout)
        self.assertEqual(len(self.log.read_text(encoding="utf-8").splitlines()), 1)

    def test_timeout_keeps_last_state_and_writes_no_cwd_files(self):
        before = sorted(path.name for path in self.tmp.iterdir())
        result = self.run_watch(
            "--run", "10", "--interval", "0.05", "--timeout", "0.5",
            responses=[{"json": {"status": "queued", "html_url": "https://example/queued"}}],
        )
        after = sorted(path.name for path in self.tmp.iterdir() if path.name != "gh.log")
        self.assertEqual(result.returncode, 2)
        self.assertIn("status: timeout", result.stdout)
        self.assertIn("https://example/queued", result.stdout)
        self.assertEqual(before, after)

    def test_help_and_argument_errors(self):
        help_result = subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0)
        invalid = subprocess.run([sys.executable, str(SCRIPT), "--run", "1", "--pr", "2"], capture_output=True, text=True)
        self.assertEqual(invalid.returncode, 2)

        for option in (("--interval", "nan"), ("--interval", "inf"), ("--timeout=-inf",), ("--timeout=-1",)):
            invalid = self.run_watch("--run", "1", *option, responses=[])
            self.assertEqual(invalid.returncode, 2, invalid.stdout + invalid.stderr)
            self.assertIn("有限的非负数", invalid.stderr)


if __name__ == "__main__":
    unittest.main()
