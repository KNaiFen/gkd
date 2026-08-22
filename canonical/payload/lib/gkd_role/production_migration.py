"""Explicit, recoverable production migration for the bounded GKD surfaces."""

from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
import tomllib
from typing import Any, Callable

from gkd_bundle import BundleError, verify_bundle_root
from gkd_task.canonical import atomic_write, canonical_bytes, digest_object, require_keys, require_sha256, sha256_bytes
from gkd_task.errors import TaskError

from .migration import MANAGED_BEGIN, MANAGED_END, _copy_skill
from .roles import load_role_source, role_catalog, role_files


RECOVERY_DIRECTORY = ".codex/.gkd-production-migration"
RECOVERY_FILE = "recovery.json"
ROLE_NAMES = ("gkd_acceptor.toml", "gkd_ci_reviewer.toml", "gkd_executor.toml")


def _production_home(value: Path) -> Path:
    if value.is_symlink() or not value.is_dir():
        raise TaskError("INVALID_PRODUCTION_HOME")
    home = value.resolve()
    codex = home / ".codex"
    if codex.is_symlink() or not codex.is_dir():
        raise TaskError("INVALID_PRODUCTION_HOME")
    for name in ("agents", "skills"):
        path = codex / name
        if path.is_symlink() or not path.is_dir():
            raise TaskError("INVALID_PRODUCTION_HOME")
    return home


def _path(root: Path, relative: str) -> Path:
    path = root / PurePosixPath(relative)
    current = root
    for part in PurePosixPath(relative).parts:
        current = current / part
        if current.is_symlink():
            raise TaskError("PRODUCTION_SYMLINK_REJECTED")
    return path


def _regular(path: Path, missing_code: str, invalid_code: str) -> bytes:
    if path.is_symlink():
        raise TaskError("PRODUCTION_SYMLINK_REJECTED")
    if not path.exists():
        raise TaskError(missing_code)
    if not path.is_file():
        raise TaskError(invalid_code)
    return path.read_bytes()


def _config_bytes(home: Path) -> bytes:
    path = _path(home, ".codex/config.toml")
    if not path.exists():
        return b""
    if path.is_symlink():
        raise TaskError("PRODUCTION_SYMLINK_REJECTED")
    if not path.is_file():
        raise TaskError("INVALID_PRODUCTION_CONFIG")
    raw = path.read_bytes()
    try:
        tomllib.loads(raw.decode("utf-8") or "")
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        raise TaskError("INVALID_PRODUCTION_CONFIG") from None
    return raw


def _managed_config(home: Path, duplicates: list[str], raw: bytes) -> bytes:
    try:
        text = raw.decode("utf-8")
        tomllib.loads(text or "")
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        raise TaskError("INVALID_PRODUCTION_CONFIG") from None
    pattern = re.compile(
        re.escape(MANAGED_BEGIN) + r"\n.*?" + re.escape(MANAGED_END) + r"\n?",
        re.DOTALL,
    )
    if text.count(MANAGED_BEGIN) != text.count(MANAGED_END) or text.count(MANAGED_BEGIN) > 1:
        raise TaskError("INVALID_PRODUCTION_CONFIG")
    lines = [MANAGED_BEGIN]
    for name in duplicates:
        skill = home / ".agents" / "skills" / name / "SKILL.md"
        lines.extend(("[[skills.config]]", f"path = {json.dumps(os.fspath(skill), ensure_ascii=True)}", "enabled = false", ""))
    lines.append(MANAGED_END)
    base = pattern.sub("", text).rstrip()
    updated = ((base + "\n\n") if base else "") + "\n".join(lines) + "\n"
    try:
        parsed = tomllib.loads(updated)
    except tomllib.TOMLDecodeError:
        raise TaskError("INVALID_PRODUCTION_CONFIG") from None
    expected = {os.fspath(home / ".agents" / "skills" / name / "SKILL.md") for name in duplicates}
    entries = parsed.get("skills", {}).get("config", [])
    selected = [entry for entry in entries if isinstance(entry, dict) and entry.get("path") in expected]
    if len(selected) != len(expected) or {entry.get("path") for entry in selected} != expected or any(entry.get("enabled") is not False for entry in selected):
        raise TaskError("PRODUCTION_CONFIG_MISMATCH")
    return updated.encode("utf-8")


def _tree_digest(path: Path) -> str:
    if path.is_symlink() or not path.is_dir():
        raise TaskError("INVALID_PRODUCTION_MANAGED_TARGET")
    records = []
    for candidate in [path, *sorted(path.rglob("*"))]:
        metadata = candidate.lstat()
        relative = "." if candidate == path else candidate.relative_to(path).as_posix()
        record = {"path": relative, "mode": format(stat.S_IMODE(metadata.st_mode), "04o")}
        if stat.S_ISREG(metadata.st_mode):
            record.update(type="file", sha256=sha256_bytes(candidate.read_bytes()))
        elif stat.S_ISDIR(metadata.st_mode):
            record["type"] = "directory"
        else:
            raise TaskError("INVALID_PRODUCTION_MANAGED_TARGET")
        records.append(record)
    return sha256_bytes(b"".join(canonical_bytes(record) for record in records))


def _target_record(root: Path, relative: str) -> dict[str, str]:
    path = _path(root, relative)
    if not path.exists():
        return {"path": relative, "type": "missing"}
    metadata = path.lstat()
    if stat.S_ISREG(metadata.st_mode):
        return {
            "path": relative,
            "type": "file",
            "mode": format(stat.S_IMODE(metadata.st_mode), "04o"),
            "sha256": sha256_bytes(path.read_bytes()),
        }
    if stat.S_ISDIR(metadata.st_mode):
        return {"path": relative, "type": "directory", "treeDigest": _tree_digest(path)}
    raise TaskError("INVALID_PRODUCTION_MANAGED_TARGET")


def _records(root: Path, targets: tuple[str, ...]) -> list[dict[str, str]]:
    return [_target_record(root, target) for target in targets]


def _records_digest(records: list[dict[str, str]]) -> str:
    return sha256_bytes(b"".join(canonical_bytes(record) for record in records))


def _targets(source: dict[str, Any]) -> tuple[str, ...]:
    return tuple(
        sorted(
            (
                ".codex/config.toml",
                *(f".codex/agents/{name}" for name in ROLE_NAMES),
                *(f".codex/skills/{name}" for name in source["skills"]),
            )
        )
    )


def _recovery_root(home: Path) -> Path:
    return _path(home, RECOVERY_DIRECTORY)


def _ensure_no_recovery(home: Path) -> None:
    root = _recovery_root(home)
    if root.exists():
        if root.is_symlink() or not root.is_dir():
            raise TaskError("INVALID_PRODUCTION_RECOVERY_STATE")
        _read_recovery(home)
        raise TaskError("PRODUCTION_RECOVERY_REQUIRED")


def _bundle_source(bundle_root: Path, bundle_digest: str) -> tuple[dict[str, Any], dict[str, Any]]:
    require_sha256(bundle_digest, "INVALID_BUNDLE_DIGEST")
    try:
        verified = verify_bundle_root(bundle_root)
    except BundleError:
        raise TaskError("INVALID_PRODUCTION_BUNDLE") from None
    if verified["contentDigest"] != bundle_digest:
        raise TaskError("BUNDLE_DIGEST_MISMATCH")
    source, _ = load_role_source(bundle_root)
    return source, role_catalog(bundle_root, bundle_digest)


def _validate_inputs(home: Path, source: dict[str, Any], targets: tuple[str, ...]) -> bytes:
    raw = _config_bytes(home)
    for name in source["duplicateSkills"]:
        _regular(
            _path(home, f".agents/skills/{name}/SKILL.md"),
            "DUPLICATE_SKILL_MISSING",
            "DUPLICATE_SKILL_MISSING",
        )
    _records(home, targets)
    return raw


def _plan_value(bundle_digest: str, source: dict[str, Any], catalog: dict[str, Any], targets: tuple[str, ...]) -> dict[str, Any]:
    value = {
        "schemaVersion": 1,
        "operation": "production-migration",
        "bundleDigest": bundle_digest,
        "roleSourceDigest": catalog["roleSourceDigest"],
        "hardRulesDigest": catalog["hardRulesDigest"],
        "installRoles": sorted(role_files_from_catalog(catalog)),
        "installSkills": source["skills"],
        "disableDuplicateSkills": source["duplicateSkills"],
        "managedTargets": list(targets),
        "recoverySurface": RECOVERY_DIRECTORY,
        "productionTarget": True,
    }
    value["planDigest"] = digest_object(value)
    return value


def role_files_from_catalog(catalog: dict[str, Any]) -> list[str]:
    return [f"{role['name']}.toml" for role in catalog["roles"]]


def production_migration_plan(bundle_root: Path, home_value: Path, bundle_digest: str) -> dict[str, Any]:
    home = _production_home(home_value)
    _ensure_no_recovery(home)
    source, catalog = _bundle_source(bundle_root, bundle_digest)
    targets = _targets(source)
    _validate_inputs(home, source, targets)
    return _plan_value(bundle_digest, source, catalog, targets)


def _stage_desired(
    stage: Path,
    bundle_root: Path,
    home: Path,
    bundle_digest: str,
    source: dict[str, Any],
    raw_config: bytes,
) -> None:
    roles = role_files(bundle_root, bundle_digest)
    for name, content in roles.items():
        atomic_write(stage / ".codex" / "agents" / name, content, mode=0o644)
    for name in source["skills"]:
        _copy_skill(bundle_root / "skills" / name, stage / ".codex" / "skills" / name)
    atomic_write(
        stage / ".codex" / "config.toml",
        _managed_config(home, source["duplicateSkills"], raw_config),
        mode=0o600,
    )


def _desired_records(
    bundle_root: Path,
    home: Path,
    bundle_digest: str,
    source: dict[str, Any],
    targets: tuple[str, ...],
    raw_config: bytes,
) -> list[dict[str, str]]:
    with tempfile.TemporaryDirectory(prefix="gkd-production-doctor-") as temporary:
        stage = Path(temporary)
        _stage_desired(stage, bundle_root, home, bundle_digest, source, raw_config)
        return _records(stage, targets)


def _copy_preimage(home: Path, backup: Path, record: dict[str, str]) -> None:
    if record["type"] == "missing":
        return
    source = _path(home, record["path"])
    target = _path(backup, record["path"])
    target.parent.mkdir(parents=True, exist_ok=True)
    if record["type"] == "file":
        shutil.copy2(source, target)
    else:
        shutil.copytree(source, target, copy_function=shutil.copy2)
    if _target_record(backup, record["path"]) != record:
        raise TaskError("PRODUCTION_BACKUP_MISMATCH")


def _write_recovery(
    root: Path,
    plan: dict[str, Any],
    before: list[dict[str, str]],
    staged: list[dict[str, str]],
) -> dict[str, Any]:
    value = {
        "schemaVersion": 1,
        "status": "active",
        "planDigest": plan["planDigest"],
        "beforeDigest": _records_digest(before),
        "stagedDigest": _records_digest(staged),
        "targets": [
            {"path": prior["path"], "before": prior, "staged": desired}
            for prior, desired in zip(before, staged, strict=True)
        ],
    }
    value["recordDigest"] = digest_object(value)
    atomic_write(root / RECOVERY_FILE, canonical_bytes(value), mode=0o600)
    return value


def _validate_record(record: Any) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise TaskError("INVALID_PRODUCTION_RECOVERY_STATE")
    require_keys(
        record,
        {"schemaVersion", "status", "planDigest", "beforeDigest", "stagedDigest", "targets", "recordDigest"},
        "INVALID_PRODUCTION_RECOVERY_STATE",
    )
    if record["schemaVersion"] != 1 or record["status"] != "active" or not isinstance(record["targets"], list):
        raise TaskError("INVALID_PRODUCTION_RECOVERY_STATE")
    for key in ("planDigest", "beforeDigest", "stagedDigest", "recordDigest"):
        require_sha256(record[key], "INVALID_PRODUCTION_RECOVERY_STATE")
    unsigned = dict(record)
    actual = unsigned.pop("recordDigest")
    if actual != digest_object(unsigned):
        raise TaskError("INVALID_PRODUCTION_RECOVERY_STATE")
    targets = []
    for item in record["targets"]:
        if not isinstance(item, dict):
            raise TaskError("INVALID_PRODUCTION_RECOVERY_STATE")
        require_keys(item, {"path", "before", "staged"}, "INVALID_PRODUCTION_RECOVERY_STATE")
        if not isinstance(item["path"], str) or item["path"] != item["before"].get("path") or item["path"] != item["staged"].get("path"):
            raise TaskError("INVALID_PRODUCTION_RECOVERY_STATE")
        targets.append(item)
    if [item["path"] for item in targets] != sorted(item["path"] for item in targets):
        raise TaskError("INVALID_PRODUCTION_RECOVERY_STATE")
    before = [item["before"] for item in targets]
    staged = [item["staged"] for item in targets]
    if record["beforeDigest"] != _records_digest(before) or record["stagedDigest"] != _records_digest(staged):
        raise TaskError("INVALID_PRODUCTION_RECOVERY_STATE")
    return record


def _read_recovery(home: Path) -> dict[str, Any]:
    root = _recovery_root(home)
    if root.is_symlink() or not root.is_dir():
        raise TaskError("INVALID_PRODUCTION_RECOVERY_STATE")
    entries = {path.name for path in root.iterdir()}
    if entries != {"backup", "stage", RECOVERY_FILE}:
        raise TaskError("INVALID_PRODUCTION_RECOVERY_STATE")
    for name in ("backup", "stage"):
        path = root / name
        if path.is_symlink() or not path.is_dir():
            raise TaskError("INVALID_PRODUCTION_RECOVERY_STATE")
    recovery_file = root / RECOVERY_FILE
    if recovery_file.is_symlink() or not recovery_file.is_file() or stat.S_IMODE(recovery_file.lstat().st_mode) != 0o600:
        raise TaskError("INVALID_PRODUCTION_RECOVERY_STATE")
    try:
        raw = recovery_file.read_bytes()
        record = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise TaskError("INVALID_PRODUCTION_RECOVERY_STATE") from None
    if raw != canonical_bytes(record):
        raise TaskError("INVALID_PRODUCTION_RECOVERY_STATE")
    record = _validate_record(record)
    before = [item["before"] for item in record["targets"]]
    staged = [item["staged"] for item in record["targets"]]
    targets = tuple(item["path"] for item in record["targets"])
    if _records(root / "backup", targets) != before or _records(root / "stage", targets) != staged:
        raise TaskError("UNRECOVERABLE_PRODUCTION_STATE")
    return record


def _replace_with_stage(home: Path, stage: Path, record: dict[str, str]) -> None:
    target = _path(home, record["path"])
    desired = _path(stage, record["path"])
    current = _target_record(home, record["path"])
    if current["type"] == "directory":
        shutil.rmtree(target)
    elif current["type"] == "file":
        target.unlink()
    target.parent.mkdir(parents=True, exist_ok=True)
    if record["type"] == "file":
        shutil.copy2(desired, target)
    else:
        shutil.copytree(desired, target, copy_function=shutil.copy2)
    if _target_record(home, record["path"]) != record:
        raise TaskError("PRODUCTION_APPLY_MISMATCH")


def _installed_inventory(
    home: Path,
    bundle_root: Path,
    bundle_digest: str,
    source: dict[str, Any],
    plan: dict[str, Any],
) -> dict[str, Any]:
    raw = _validate_inputs(home, source, tuple(plan["managedTargets"]))
    expected = _desired_records(
        bundle_root,
        home,
        bundle_digest,
        source,
        tuple(plan["managedTargets"]),
        raw,
    )
    actual = _records(home, tuple(plan["managedTargets"]))
    if actual != expected:
        raise TaskError("PRODUCTION_DOCTOR_MISMATCH")
    catalog = role_catalog(bundle_root, bundle_digest)
    inventory = {
        "roles": {role["name"]: role["roleDigest"] for role in catalog["roles"]},
        "skills": {record["path"]: record.get("treeDigest", record.get("sha256")) for record in actual if "/skills/" in record["path"]},
        "configDigest": next(record["sha256"] for record in actual if record["path"] == ".codex/config.toml"),
    }
    return {"managedSurfaceDigest": _records_digest(actual), "inventoryDigest": digest_object(inventory)}


def apply_production_migration(
    bundle_root: Path,
    home_value: Path,
    bundle_digest: str,
    failure_hook: Callable[[str, Path], None] | None = None,
) -> dict[str, Any]:
    home = _production_home(home_value)
    _ensure_no_recovery(home)
    source, catalog = _bundle_source(bundle_root, bundle_digest)
    targets = _targets(source)
    raw = _validate_inputs(home, source, targets)
    plan = _plan_value(bundle_digest, source, catalog, targets)
    root = _recovery_root(home)
    root.mkdir(mode=0o700)
    stage = root / "stage"
    backup = root / "backup"
    stage.mkdir(mode=0o700)
    backup.mkdir(mode=0o700)
    hook = failure_hook or (lambda phase, path: None)
    recorded = False
    try:
        _stage_desired(stage, bundle_root, home, bundle_digest, source, raw)
        hook("staged", stage)
        staged = _records(stage, targets)
        expected = _desired_records(bundle_root, home, bundle_digest, source, targets, raw)
        if staged != expected:
            raise TaskError("STAGED_CONTENT_TAMPERED")
        before = _records(home, targets)
        for record in before:
            _copy_preimage(home, backup, record)
        recovery = _write_recovery(root, plan, before, staged)
        recorded = True
        hook("recovery-recorded", root)
        for record in staged:
            _replace_with_stage(home, stage, record)
            hook("target-mutated", root)
        verified = _installed_inventory(home, bundle_root, bundle_digest, source, plan)
        shutil.rmtree(root)
        return {
            "schemaVersion": 1,
            "status": "production_migration_applied",
            "planDigest": plan["planDigest"],
            "beforeDigest": recovery["beforeDigest"],
            **verified,
        }
    except Exception:
        if not recorded and root.exists():
            shutil.rmtree(root)
        raise


def doctor_production_migration(bundle_root: Path, home_value: Path, bundle_digest: str) -> dict[str, Any]:
    home = _production_home(home_value)
    root = _recovery_root(home)
    if root.exists():
        recovery = _read_recovery(home)
        return {
            "schemaVersion": 1,
            "status": "production_recovery_required",
            "planDigest": recovery["planDigest"],
            "beforeDigest": recovery["beforeDigest"],
        }
    plan = production_migration_plan(bundle_root, home, bundle_digest)
    source, _ = _bundle_source(bundle_root, bundle_digest)
    verified = _installed_inventory(home, bundle_root, bundle_digest, source, plan)
    return {
        "schemaVersion": 1,
        "status": "production_migration_healthy",
        "planDigest": plan["planDigest"],
        **verified,
    }


def _restore(home_value: Path, status: str) -> dict[str, Any]:
    home = _production_home(home_value)
    recovery = _read_recovery(home)
    root = _recovery_root(home)
    targets = tuple(item["path"] for item in recovery["targets"])
    before = [item["before"] for item in recovery["targets"]]
    staged = [item["staged"] for item in recovery["targets"]]
    current = _records(home, targets)
    for current_record, before_record, staged_record in zip(current, before, staged, strict=True):
        if current_record not in (before_record, staged_record) and current_record["type"] != "missing":
            raise TaskError("UNRECOVERABLE_PRODUCTION_STATE")
    for record in before:
        target = _path(home, record["path"])
        current_record = _target_record(home, record["path"])
        if current_record["type"] == "directory":
            shutil.rmtree(target)
        elif current_record["type"] == "file":
            target.unlink()
        if record["type"] == "missing":
            continue
        backup = _path(root / "backup", record["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        if record["type"] == "file":
            shutil.copy2(backup, target)
        else:
            shutil.copytree(backup, target, copy_function=shutil.copy2)
    if _records(home, targets) != before:
        raise TaskError("PRODUCTION_ROLLBACK_MISMATCH")
    shutil.rmtree(root)
    return {
        "schemaVersion": 1,
        "status": status,
        "planDigest": recovery["planDigest"],
        "beforeDigest": recovery["beforeDigest"],
    }


def rollback_production_migration(home_value: Path) -> dict[str, Any]:
    return _restore(home_value, "production_migration_rolled_back")


def recover_production_migration(home_value: Path) -> dict[str, Any]:
    return _restore(home_value, "production_migration_recovered")
