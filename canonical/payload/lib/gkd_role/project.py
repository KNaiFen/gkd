"""Deterministic project-scoped staging for trusted GKD main sessions."""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import stat
import subprocess
import tomllib
from typing import Any

from gkd_bundle import BundleError, verify_bundle_root
from gkd_task.canonical import atomic_write, canonical_bytes, digest_object, read_canonical_json, require_keys, require_sha256, sha256_bytes
from gkd_task.errors import TaskError
from .roles import load_role_source, role_catalog, role_files, role_record


PROJECT_INVENTORY = Path(".gkd/runtime-project.json")
EXECUTOR_SKILLS = ("gkd-ci-monitor", "gkd-execute", "gkd-local-verify")
PARENT_SKILLS = ("gkd-main",)


def _overlap(first: Path, second: Path) -> bool:
    try:
        first.relative_to(second)
        return True
    except ValueError:
        try:
            second.relative_to(first)
            return True
        except ValueError:
            return False


def _reject_symlink_chains(project: Path, relative_paths: Any) -> None:
    for relative in relative_paths:
        current = project
        for part in Path(relative).parts:
            current /= part
            if current.is_symlink():
                raise TaskError("PROJECT_STAGE_SYMLINK")


def _root_without_symlink_ancestors(value: Path, code: str) -> Path:
    if ".." in value.parts:
        raise TaskError("PROJECT_PATH_TRAVERSAL")
    absolute = value if value.is_absolute() else Path.cwd() / value
    # macOS exposes these temporary roots as stable system aliases; inspect
    # their physical targets while retaining lexical checks for project paths.
    parts = absolute.parts
    if len(parts) > 1 and Path(parts[0], parts[1]) in {Path("/var"), Path("/tmp")}:
        system_root = Path(parts[0], parts[1]).resolve()
        absolute = system_root.joinpath(*parts[2:])
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        try:
            metadata = os.lstat(current)
        except FileNotFoundError:
            break
        except OSError:
            raise TaskError(code) from None
        if stat.S_ISLNK(metadata.st_mode):
            raise TaskError(code)
    return absolute


def _git_project(value: Path) -> Path:
    absolute = _root_without_symlink_ancestors(value, "PROJECT_ROOT_SYMLINK")
    if not absolute.is_dir():
        raise TaskError("PROJECT_NOT_GIT_ROOT")
    root = absolute.resolve()
    result = subprocess.run(
        ("git", "rev-parse", "--show-toplevel"),
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0 or Path(result.stdout.strip()).resolve() != root:
        raise TaskError("PROJECT_NOT_GIT_ROOT")
    return root


def _project_config(description: str) -> bytes:
    return (
        "[agents]\n"
        "enabled = true\n\n"
        "[agents.gkd_executor]\n"
        f"description = {json.dumps(description, ensure_ascii=True)}\n"
        'config_file = "agents/gkd_executor.toml"\n'
    ).encode("utf-8")


def _validate_project_config(data: bytes, description: str) -> None:
    try:
        value = tomllib.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        raise TaskError("INVALID_PROJECT_CONFIG") from None
    if value != {
        "agents": {
            "enabled": True,
            "gkd_executor": {
                "description": description,
                "config_file": "agents/gkd_executor.toml",
            },
        }
    }:
        raise TaskError("INVALID_PROJECT_CONFIG")


def _skill_files(bundle_root: Path, skill: str, target_root: Path) -> dict[str, tuple[bytes, int]]:
    source = bundle_root / "skills" / skill
    if source.is_symlink() or not source.is_dir():
        raise TaskError("INVALID_SKILL_INVENTORY")
    result: dict[str, tuple[bytes, int]] = {}
    for path in sorted(source.rglob("*")):
        if path.is_symlink() or (path.exists() and not path.is_file() and not path.is_dir()):
            raise TaskError("INVALID_SKILL_INVENTORY")
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        result[(target_root / skill / relative).as_posix()] = (path.read_bytes(), stat.S_IMODE(path.stat().st_mode))
    if not result or (target_root / skill / "SKILL.md").as_posix() not in result:
        raise TaskError("INVALID_SKILL_INVENTORY")
    return result


def _desired_files(bundle_root: Path, bundle_digest: str) -> tuple[dict[str, tuple[bytes, int]], dict[str, Any]]:
    root = bundle_root.resolve()
    try:
        verified = verify_bundle_root(root)
    except BundleError:
        raise TaskError("BUNDLE_CONTENT_MISMATCH") from None
    if verified["contentDigest"] != bundle_digest:
        raise TaskError("BUNDLE_DIGEST_MISMATCH")
    source, _ = load_role_source(root)
    catalog = role_catalog(root, bundle_digest)
    definition = next(item for item in source["roles"] if item["name"] == "gkd_executor")
    role = role_record(catalog, "gkd_executor")
    config = _project_config(definition["description"])
    _validate_project_config(config, definition["description"])
    role_bytes = role_files(root, bundle_digest)["gkd_executor.toml"]
    if sha256_bytes(role_bytes) != role["configDigest"]:
        raise TaskError("ROLE_CONFIG_DRIFT")
    files: dict[str, tuple[bytes, int]] = {
        ".codex/config.toml": (config, 0o644),
        ".codex/agents/gkd_executor.toml": (role_bytes, 0o644),
    }
    for skill in EXECUTOR_SKILLS:
        files.update(_skill_files(root, skill, Path(".codex/skills")))
    for skill in PARENT_SKILLS:
        files.update(_skill_files(root, skill, Path(".agents/skills")))
    expected_skills = set(EXECUTOR_SKILLS) | set(PARENT_SKILLS)
    if expected_skills != set(role["skills"]) | set(PARENT_SKILLS):
        raise TaskError("INVALID_PROJECT_SKILLS")
    facts = {
        "executionBundleDigest": bundle_digest,
        "roleName": "gkd_executor",
        "roleDigest": role["roleDigest"],
        "configDigest": role["configDigest"],
        "projectConfigDigest": sha256_bytes(config),
        "skillDigests": {name: catalog["skillDigests"][name] for name in sorted(expected_skills)},
    }
    return files, facts


def _inventory(files: dict[str, tuple[bytes, int]], facts: dict[str, Any]) -> dict[str, Any]:
    value = {
        "schemaVersion": 1,
        "kind": "gkd-project-runtime",
        **facts,
        "files": [
            {
                "path": path,
                "mode": f"{mode:04o}",
                "sha256": sha256_bytes(data),
                "preimage": None,
            }
            for path, (data, mode) in sorted(files.items())
        ],
        "launch": {"workingDirectory": ".", "skill": "gkd-main", "role": "gkd_executor"},
    }
    value["inventoryDigest"] = digest_object(value)
    return value


def _validate_inventory(value: dict[str, Any]) -> None:
    require_keys(
        value,
        {
            "schemaVersion", "kind", "executionBundleDigest", "roleName", "roleDigest",
            "configDigest", "projectConfigDigest", "skillDigests", "files", "launch", "inventoryDigest",
        },
        "INVALID_PROJECT_INVENTORY",
    )
    if value["schemaVersion"] != 1 or value["kind"] != "gkd-project-runtime" or value["roleName"] != "gkd_executor":
        raise TaskError("INVALID_PROJECT_INVENTORY")
    for field in ("executionBundleDigest", "roleDigest", "configDigest", "projectConfigDigest", "inventoryDigest"):
        require_sha256(value[field], "INVALID_PROJECT_INVENTORY")
    if value["launch"] != {"workingDirectory": ".", "skill": "gkd-main", "role": "gkd_executor"}:
        raise TaskError("INVALID_PROJECT_INVENTORY")
    if not isinstance(value["skillDigests"], dict) or tuple(sorted(value["skillDigests"])) != tuple(sorted((*EXECUTOR_SKILLS, *PARENT_SKILLS))):
        raise TaskError("INVALID_PROJECT_INVENTORY")
    for digest in value["skillDigests"].values():
        require_sha256(digest, "INVALID_PROJECT_INVENTORY")
    if not isinstance(value["files"], list) or not value["files"]:
        raise TaskError("INVALID_PROJECT_INVENTORY")
    paths = []
    for record in value["files"]:
        require_keys(record, {"path", "mode", "sha256", "preimage"}, "INVALID_PROJECT_INVENTORY")
        path = Path(record["path"])
        if path.is_absolute() or ".." in path.parts or record["mode"] != "0644" or record["preimage"] is not None:
            raise TaskError("INVALID_PROJECT_INVENTORY")
        require_sha256(record["sha256"], "INVALID_PROJECT_INVENTORY")
        paths.append(record["path"])
    if paths != sorted(set(paths)):
        raise TaskError("INVALID_PROJECT_INVENTORY")
    unsigned = deepcopy(value)
    digest = unsigned.pop("inventoryDigest")
    if digest_object(unsigned) != digest:
        raise TaskError("INVALID_PROJECT_INVENTORY")


def _validate_boundaries(bundle_root: Path, project_root: Path, production_root: Path) -> tuple[Path, Path]:
    project_path = _root_without_symlink_ancestors(project_root, "PROJECT_ROOT_SYMLINK")
    production = production_root.resolve(strict=False)
    if project_path == production or _overlap(project_path, production):
        raise TaskError("PRODUCTION_PROJECT_FORBIDDEN")
    project = _git_project(project_path)
    source_path = _root_without_symlink_ancestors(bundle_root, "PROJECT_SOURCE_SYMLINK")
    if not source_path.is_dir():
        raise TaskError("INVALID_BUNDLE_ROOT")
    source = source_path.resolve()
    if _overlap(source, project):
        raise TaskError("PROJECT_SOURCE_OVERLAP")
    _reject_symlink_chains(
        project,
        (".codex/agents", ".codex/skills", ".agents/skills/gkd-main", PROJECT_INVENTORY),
    )
    return source, project


def _managed_files(project: Path) -> set[str]:
    result: set[str] = set()
    codex = project / ".codex"
    if codex.exists():
        result.update(path.relative_to(project).as_posix() for path in codex.rglob("*") if path.is_file() or path.is_symlink())
    main_skill = project / ".agents" / "skills" / "gkd-main"
    if main_skill.exists():
        result.update(path.relative_to(project).as_posix() for path in main_skill.rglob("*") if path.is_file() or path.is_symlink())
    if (project / PROJECT_INVENTORY).exists() or (project / PROJECT_INVENTORY).is_symlink():
        result.add(PROJECT_INVENTORY.as_posix())
    return result


def _result(status: str, inventory: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": status,
        "executionBundleDigest": inventory["executionBundleDigest"],
        "roleName": inventory["roleName"],
        "roleDigest": inventory["roleDigest"],
        "configDigest": inventory["configDigest"],
        "projectConfigDigest": inventory["projectConfigDigest"],
        "skillDigests": inventory["skillDigests"],
        "inventoryDigest": inventory["inventoryDigest"],
        "launch": inventory["launch"],
    }


def verify_project(bundle_root: Path, bundle_digest: str, project_root: Path, production_root: Path) -> dict[str, Any]:
    source, project = _validate_boundaries(bundle_root, project_root, production_root)
    files, facts = _desired_files(source, bundle_digest)
    _reject_symlink_chains(project, (*files, PROJECT_INVENTORY))
    inventory = read_canonical_json(project / PROJECT_INVENTORY, "INVALID_PROJECT_INVENTORY", _validate_inventory)
    expected = _inventory(files, facts)
    if inventory != expected:
        raise TaskError("PROJECT_STAGE_DRIFT")
    expected_paths = set(files) | {PROJECT_INVENTORY.as_posix()}
    if _managed_files(project) != expected_paths:
        raise TaskError("PROJECT_STAGE_DRIFT")
    for record in inventory["files"]:
        path = project / record["path"]
        if path.is_symlink() or not path.is_file():
            raise TaskError("PROJECT_STAGE_DRIFT")
        if sha256_bytes(path.read_bytes()) != record["sha256"]:
            raise TaskError("PROJECT_STAGE_DRIFT")
        if stat.S_IMODE(path.stat().st_mode) != int(record["mode"], 8):
            raise TaskError("PROJECT_STAGE_DRIFT")
    return _result("verified", inventory)


def stage_project(
    bundle_root: Path,
    bundle_digest: str,
    project_root: Path,
    production_root: Path,
    failure_hook: Any | None = None,
) -> dict[str, Any]:
    source, project = _validate_boundaries(bundle_root, project_root, production_root)
    files, facts = _desired_files(source, bundle_digest)
    _reject_symlink_chains(project, (*files, PROJECT_INVENTORY))
    inventory_path = project / PROJECT_INVENTORY
    if inventory_path.exists() or inventory_path.is_symlink():
        result = verify_project(source, bundle_digest, project, production_root)
        result["status"] = "already_staged"
        return result
    if _managed_files(project):
        raise TaskError("PROJECT_CONFIG_CONFLICT")
    inventory = _inventory(files, facts)
    created_dirs: list[Path] = []
    written: list[Path] = []
    try:
        for index, (relative, (data, mode)) in enumerate((*sorted(files.items()), (PROJECT_INVENTORY.as_posix(), (canonical_bytes(inventory), 0o644))), start=1):
            path = project / relative
            missing = []
            parent = path.parent
            while parent != project and not parent.exists():
                missing.append(parent)
                parent = parent.parent
            for directory in reversed(missing):
                directory.mkdir()
                created_dirs.append(directory)
            atomic_write(path, data, mode=mode)
            written.append(path)
            if failure_hook is not None:
                failure_hook(index, path)
    except (OSError, TaskError):
        try:
            for path in reversed(written):
                path.unlink(missing_ok=True)
            for directory in reversed(created_dirs):
                directory.rmdir()
        except OSError:
            raise TaskError("PROJECT_STAGE_ROLLBACK_FAILED") from None
        raise TaskError("PROJECT_STAGE_FAILED") from None
    return _result("staged", inventory)


def remove_project(project_root: Path, production_root: Path) -> dict[str, Any]:
    project = _git_project(project_root)
    production = production_root.resolve(strict=False)
    if project == production or _overlap(project, production):
        raise TaskError("PRODUCTION_PROJECT_FORBIDDEN")
    _reject_symlink_chains(project, (".codex/agents", ".codex/skills", ".agents/skills/gkd-main", PROJECT_INVENTORY))
    inventory = read_canonical_json(project / PROJECT_INVENTORY, "INVALID_PROJECT_INVENTORY", _validate_inventory)
    _reject_symlink_chains(project, (record["path"] for record in inventory["files"]))
    expected_paths = {record["path"] for record in inventory["files"]} | {PROJECT_INVENTORY.as_posix()}
    if _managed_files(project) != expected_paths:
        raise TaskError("PROJECT_STAGE_DRIFT")
    for record in inventory["files"]:
        path = project / record["path"]
        if (
            path.is_symlink()
            or not path.is_file()
            or sha256_bytes(path.read_bytes()) != record["sha256"]
            or stat.S_IMODE(path.stat().st_mode) != int(record["mode"], 8)
        ):
            raise TaskError("PROJECT_STAGE_DRIFT")
    for record in reversed(inventory["files"]):
        path = project / record["path"]
        path.unlink()
    (project / PROJECT_INVENTORY).unlink()
    for relative in (
        ".codex/agents", ".codex/skills/gkd-ci-monitor/agents", ".codex/skills/gkd-ci-monitor",
        ".codex/skills/gkd-execute/agents", ".codex/skills/gkd-execute",
        ".codex/skills/gkd-local-verify/agents", ".codex/skills/gkd-local-verify", ".codex/skills",
        ".codex", ".agents/skills/gkd-main/agents", ".agents/skills/gkd-main", ".agents/skills",
        ".agents", ".gkd",
    ):
        directory = project / relative
        if directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()
    return _result("removed", inventory)
