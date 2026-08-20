from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
LIBRARY = ROOT / "canonical" / "payload" / "lib"
if str(LIBRARY) not in sys.path:
    sys.path.insert(0, str(LIBRARY))

from gkd_task.canonical import canonical_bytes  # noqa: E402


SYNTHETIC_REPOSITORY = "github.com/acme/widgets"
SYNTHETIC_CHECK = "Fixture Verify"
EXPECTED_HEAD = "a" * 40


def run(*arguments: str, cwd: Path) -> str:
    result = subprocess.run(
        arguments,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


def policy_value(
    repository: str = SYNTHETIC_REPOSITORY,
    base_branch: str = "main",
    checks: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "baseBranch": base_branch,
        "provider": "github",
        "repository": repository,
        "requiredChecks": checks or [SYNTHETIC_CHECK],
        "schemaVersion": 1,
    }


def write_policy(checkout: Path, value: dict[str, Any] | None = None) -> Path:
    path = checkout / ".gkd" / "policy.json"
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(canonical_bytes(value or policy_value()))
    return path


def init_checkout(
    root: Path,
    remote_url: str = "https://github.com/acme/widgets.git",
    base_branch: str = "main",
    repository: str = SYNTHETIC_REPOSITORY,
) -> Path:
    checkout = root / "checkout"
    checkout.mkdir(parents=True)
    run("git", "init", f"--initial-branch={base_branch}", cwd=checkout)
    run("git", "config", "user.name", "Fixture", cwd=checkout)
    run("git", "config", "user.email", "fixture@example.test", cwd=checkout)
    (checkout / "README.md").write_text("fixture\n", encoding="utf-8")
    run("git", "add", "README.md", cwd=checkout)
    run("git", "commit", "-m", "base", cwd=checkout)
    run("git", "remote", "add", "origin", remote_url, cwd=checkout)
    run("git", "update-ref", f"refs/remotes/origin/{base_branch}", "HEAD", cwd=checkout)
    run(
        "git",
        "symbolic-ref",
        "refs/remotes/origin/HEAD",
        f"refs/remotes/origin/{base_branch}",
        cwd=checkout,
    )
    write_policy(checkout, policy_value(repository=repository, base_branch=base_branch))
    return checkout


def tree_digest(root: Path) -> str:
    records: list[bytes] = []
    for path in sorted(root.rglob("*")):
        if ".git" in path.relative_to(root).parts or not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        records.append(relative.encode("utf-8") + b"\0" + hashlib.sha256(path.read_bytes()).digest())
    return hashlib.sha256(b"".join(records)).hexdigest()


def pull_request(
    *,
    number: int = 8,
    repository: str = "acme/widgets",
    state: str = "open",
    base: str = "main",
    head: str = EXPECTED_HEAD,
    head_branch: str = "task/change",
) -> dict[str, Any]:
    return {
        "base": {"ref": base, "repo": {"full_name": repository}},
        "head": {
            "ref": head_branch,
            "repo": {"full_name": repository},
            "sha": head,
        },
        "number": number,
        "state": state,
    }


def check_run(
    name: str = SYNTHETIC_CHECK,
    *,
    status: str = "completed",
    conclusion: str | None = "success",
    head: str = EXPECTED_HEAD,
) -> dict[str, Any]:
    return {
        "conclusion": conclusion,
        "head_sha": head,
        "name": name,
        "status": status,
    }


def status_context(
    context: str = SYNTHETIC_CHECK,
    *,
    state: str = "success",
    head: str = EXPECTED_HEAD,
) -> dict[str, Any]:
    return {"context": context, "sha": head, "state": state}


def write_scenario(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def fake_github_environment(root: Path, scenario: Path) -> dict[str, str]:
    bin_dir = root / "bin"
    bin_dir.mkdir()
    executable = bin_dir / "gh"
    executable.symlink_to(ROOT / "tests" / "ci_policy" / "fake_github.py")
    environment = dict(os.environ)
    environment["PATH"] = f"{bin_dir}{os.pathsep}{environment['PATH']}"
    environment["GKD_FAKE_GITHUB_SCENARIO"] = os.fspath(scenario)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment
