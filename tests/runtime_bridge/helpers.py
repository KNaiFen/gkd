from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

from gkd_role.bridge import TrustedMainRuntimeBridge
from gkd_role.project import stage_project
from gkd_role.roles import role_catalog
from gkd_role.routing import decide_route
from gkd_task.canonical import FixedClock, FixedNonce, canonical_bytes
from gkd_task.runtime import RuntimeStore
from tests.task_core.helpers import FIXED_TIME, FUTURE_TIME, TaskRepo


BUNDLE_ROOT = Path("canonical/payload")
SOURCE_ROOT = Path("canonical")


def run(*args: str, cwd: Path) -> str:
    command = (sys.executable, *args) if Path(args[0]).is_file() else args
    result = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


def init_repo(root: Path) -> None:
    root.mkdir()
    run("git", "init", "--initial-branch=main", cwd=root)
    run("git", "config", "user.name", "Fixture", cwd=root)
    run("git", "config", "user.email", "fixture@example.test", cwd=root)
    (root / "README.md").write_text("fixture\n", encoding="utf-8")
    (root / ".gkd").mkdir()
    (root / ".gkd" / "policy.json").write_bytes(
        canonical_bytes(
            {
                "schemaVersion": 1,
                "provider": "github",
                "repository": "github.com/team/repository",
                "baseBranch": "main",
                "requiredChecks": ["contract"],
            }
        )
    )
    run("git", "add", "README.md", ".gkd/policy.json", cwd=root)
    run("git", "commit", "-m", "base", cwd=root)
    run("git", "remote", "add", "origin", "https://github.com/team/repository.git", cwd=root)
    run("git", "update-ref", "refs/remotes/origin/main", "HEAD", cwd=root)


def bundle_digest() -> str:
    return json.loads((SOURCE_ROOT / "manifest.lock.json").read_text(encoding="utf-8"))["contentDigest"]


def automatic_decision(digest: str, project_policy: dict[str, object]) -> dict[str, object]:
    return decide_route(
        {
            "schemaVersion": 2,
            "requestedRoute": "automatic",
            "bundleDigest": digest,
            "projectPolicy": project_policy,
            "gates": {
                "activationProviderReady": True,
                "bundleFixed": True,
                "offerClaimReady": True,
                "roleAvailable": True,
                "roleConfigFixed": True,
                "waitGateReady": True,
            },
        }
    )


def ready_bridge(repo: TaskRepo, bundle_root: Path = BUNDLE_ROOT) -> tuple[TrustedMainRuntimeBridge, dict[str, object]]:
    repo.ready_and_authorized()
    digest = bundle_digest()
    stage_project(bundle_root, digest, repo.main, repo.production)
    bridge = TrustedMainRuntimeBridge(
        repo.candidate,
        repo.task_path,
        RuntimeStore(repo.runtime_root),
        bundle_root,
        digest,
        FixedClock(FIXED_TIME),
        FixedNonce(["c" * 48, *[f"bridge-nonce-{index}" for index in range(20)]]),
    )
    prepared = bridge.prepare(
        *repo.cas(),
        automatic_decision(digest, repo.state()["repository"]["policy"]),
        FUTURE_TIME,
        repo.main,
        repo.production,
    )
    return bridge, prepared


def spawn_result(prepared: dict[str, object], **overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "schemaVersion": 2,
        "status": "spawned",
        "spawnCount": 1,
        "taskName": f"/root/{prepared['spawnRequest']['taskName']}",
        "agentType": "gkd_executor",
        "forkTurns": "none",
        "fallbackAttempted": False,
    }
    value.update(overrides)
    return value


def terminal_result(
    repo: TaskRepo,
    prepared: dict[str, object],
    claim: dict[str, object],
    **overrides: object,
) -> dict[str, object]:
    value: dict[str, object] = {
        "schemaVersion": 1,
        "status": "terminal",
        "taskId": repo.task_id,
        "repository": repo.identity,
        "taskBranch": repo.task_branch,
        "offerId": prepared["offerId"],
        "claimId": claim["claimId"],
        "taskName": prepared["spawnRequest"]["taskName"],
        "agentId": "legacy-terminal-agent",
        "sessionDigest": "a" * 64,
        "roleName": prepared["roleName"],
        "roleDigest": prepared["roleDigest"],
        "configDigest": prepared["configDigest"],
        "executionBundleDigest": prepared["executionBundleDigest"],
        "routeDecisionDigest": prepared["routeDecisionDigest"],
        "route": "automatic",
        "terminalAt": FIXED_TIME,
    }
    value.update(overrides)
    return deepcopy(value)
