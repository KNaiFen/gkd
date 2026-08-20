from __future__ import annotations

import json
from pathlib import Path
import subprocess

from gkd_role.bridge import TrustedMainRuntimeBridge
from gkd_role.roles import role_catalog
from gkd_role.routing import decide_route
from gkd_task.canonical import FixedClock, FixedNonce
from gkd_task.runtime import RuntimeStore
from tests.task_core.helpers import FIXED_TIME, FUTURE_TIME, TaskRepo


BUNDLE_ROOT = Path("canonical/payload")
SOURCE_ROOT = Path("canonical")


def run(*args: str, cwd: Path) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


def init_repo(root: Path) -> None:
    root.mkdir()
    run("git", "init", "--initial-branch=main", cwd=root)
    run("git", "config", "user.name", "Fixture", cwd=root)
    run("git", "config", "user.email", "fixture@example.test", cwd=root)
    (root / "README.md").write_text("fixture\n", encoding="utf-8")
    run("git", "add", "README.md", cwd=root)
    run("git", "commit", "-m", "base", cwd=root)


def bundle_digest() -> str:
    return json.loads((SOURCE_ROOT / "manifest.lock.json").read_text(encoding="utf-8"))["contentDigest"]


def automatic_decision(digest: str | None = None) -> dict[str, object]:
    return decide_route(
        {
            "schemaVersion": 1,
            "requestedRoute": "automatic",
            "bundleDigest": digest or bundle_digest(),
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
    bridge = TrustedMainRuntimeBridge(
        repo.candidate,
        repo.task_path,
        RuntimeStore(repo.runtime_root),
        bundle_root,
        digest,
        FixedClock(FIXED_TIME),
        FixedNonce(["c" * 48, *[f"bridge-nonce-{index}" for index in range(20)]]),
    )
    prepared = bridge.prepare(*repo.cas(), automatic_decision(digest), FUTURE_TIME)
    return bridge, prepared


def spawn_result(prepared: dict[str, object], **overrides: object) -> dict[str, object]:
    catalog = role_catalog(BUNDLE_ROOT, str(prepared["executionBundleDigest"]))
    role = next(item for item in catalog["roles"] if item["name"] == "gkd_executor")
    value: dict[str, object] = {
        "schemaVersion": 1,
        "status": "spawned",
        "spawnCount": 1,
        "taskName": prepared["spawnRequest"]["taskName"],
        "agentType": "gkd_executor",
        "forkTurns": "none",
        "agentId": "agent-runtime-one",
        "threadDigest": "a" * 64,
        "roleName": "gkd_executor",
        "roleDigest": role["roleDigest"],
        "configDigest": role["configDigest"],
        "executionBundleDigest": prepared["executionBundleDigest"],
        "routeDecisionDigest": prepared["routeDecisionDigest"],
        "model": role["model"],
        "reasoningEffort": role["modelReasoningEffort"],
        "sandbox": role["sandboxMode"],
        "runtimeSeconds": role["runtimeSeconds"],
        "activatedAt": FIXED_TIME,
        "fallbackAttempted": False,
    }
    value.update(overrides)
    return value
