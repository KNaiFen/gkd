"""Atomic temporary-home role and Skill migration."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile
import tomllib
from typing import Any, Callable

from gkd_task.canonical import atomic_write, canonical_bytes, digest_object, require_sha256, sha256_bytes
from gkd_task.errors import TaskError

from .roles import load_role_source, role_catalog, role_files


MANAGED_BEGIN = "# gkd-skill-overrides:begin"
MANAGED_END = "# gkd-skill-overrides:end"
LEGACY_ROLES = ("ci-reviewer.toml", "ci_reviewer.toml")
SECURITY_DESCRIPTION = "Use only when the user explicitly requests a security review or the task changes authentication, authorization, secrets, or sensitive-data exposure; do not trigger for ordinary third-party input."


def _temporary_home(value: Path) -> Path:
    if value.is_symlink() or not value.is_dir():
        raise TaskError("INVALID_MIGRATION_HOME")
    resolved = value.resolve()
    system = Path(tempfile.gettempdir()).resolve()
    try:
        resolved.relative_to(system)
    except ValueError:
        raise TaskError("MIGRATION_PRODUCTION_FORBIDDEN") from None
    if resolved == system or resolved.parent == resolved:
        raise TaskError("INVALID_MIGRATION_HOME")
    return resolved


def _regular(path: Path, code: str) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise TaskError(code)
    return path.read_bytes()


def _managed_block(home: Path, duplicates: list[str]) -> bytes:
    lines = [MANAGED_BEGIN]
    for name in duplicates:
        skill = home / ".agents" / "skills" / name / "SKILL.md"
        lines.extend(("[[skills.config]]", f"path = {json.dumps(os.fspath(skill), ensure_ascii=True)}", "enabled = false", ""))
    lines.append(MANAGED_END)
    return ("\n".join(lines) + "\n").encode("utf-8")


def _update_config(path: Path, home: Path, duplicates: list[str]) -> None:
    raw = _regular(path, "INVALID_CODEX_CONFIG") if path.exists() else b""
    try:
        text = raw.decode("utf-8")
        tomllib.loads(text or "")
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        raise TaskError("INVALID_CODEX_CONFIG") from None
    pattern = re.compile(re.escape(MANAGED_BEGIN) + r"\n.*?" + re.escape(MANAGED_END) + r"\n?", re.DOTALL)
    if text.count(MANAGED_BEGIN) != text.count(MANAGED_END) or text.count(MANAGED_BEGIN) > 1:
        raise TaskError("INVALID_CODEX_CONFIG")
    base = pattern.sub("", text).rstrip()
    block = _managed_block(home, duplicates).decode("utf-8")
    updated = ((base + "\n\n") if base else "") + block
    try:
        parsed = tomllib.loads(updated)
    except tomllib.TOMLDecodeError:
        raise TaskError("INVALID_CODEX_CONFIG") from None
    entries = parsed.get("skills", {}).get("config", [])
    expected = {os.fspath(home / ".agents" / "skills" / name / "SKILL.md") for name in duplicates}
    selected = [entry for entry in entries if isinstance(entry, dict) and entry.get("path") in expected]
    if len(selected) != len(expected) or {entry.get("path") for entry in selected} != expected or any(entry.get("enabled") is not False for entry in selected):
        raise TaskError("SKILL_OVERRIDE_MISMATCH")
    atomic_write(path, updated.encode("utf-8"), mode=0o600)


def _repair_security_skill(skill_root: Path) -> None:
    path = skill_root / "SKILL.md"
    raw = _regular(path, "SECURITY_SKILL_MISSING")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise TaskError("SECURITY_SKILL_INVALID") from None
    if not text.startswith("---\n") or "\nname: security-and-hardening\n" not in text:
        raise TaskError("SECURITY_SKILL_INVALID")
    updated, count = re.subn(r"(?m)^description: .+$", f"description: {SECURITY_DESCRIPTION}", text, count=1)
    if count != 1:
        raise TaskError("SECURITY_SKILL_INVALID")
    updated = re.sub(
        r"\n## See Also\n\nFor detailed security checklists and pre-commit verification steps, see `references/security-checklist\.md`\.\n",
        "\n",
        updated,
        count=1,
    )
    references = sorted(set(re.findall(r"`(references/[^`]+)`", updated)))
    if any(not (skill_root / reference).is_file() for reference in references):
        raise TaskError("SECURITY_SKILL_BROKEN_REFERENCE")
    atomic_write(path, updated.encode("utf-8"), mode=0o644)


def _copy_skill(source: Path, target: Path) -> None:
    if source.is_symlink() or not source.is_dir():
        raise TaskError("INVALID_SKILL_INVENTORY")
    if target.exists() or target.is_symlink():
        if target.is_symlink() or not target.is_dir():
            raise TaskError("INVALID_SKILL_TARGET")
        shutil.rmtree(target)
    shutil.copytree(source, target, symlinks=False)
    for path in [target, *target.rglob("*")]:
        if path.is_symlink():
            raise TaskError("INVALID_SKILL_TARGET")
        os.chmod(path, 0o755 if path.is_dir() else 0o644)


def _surface_records(home: Path, normalize_home: bool = True) -> list[dict[str, Any]]:
    roots = [home / ".codex" / "config.toml", home / ".codex" / "agents", home / ".codex" / "skills", home / ".codex" / "AGENTS.md", home / ".agents" / "skills"]
    records = []
    marker = os.fspath(home).encode("utf-8")
    for root in roots:
        if not root.exists() and not root.is_symlink():
            records.append({"path": root.relative_to(home).as_posix(), "type": "missing"})
            continue
        candidates = [root]
        if root.is_dir() and not root.is_symlink():
            candidates.extend(sorted(root.rglob("*")))
        for path in candidates:
            metadata = path.lstat()
            record = {"path": path.relative_to(home).as_posix(), "mode": format(stat.S_IMODE(metadata.st_mode), "04o")}
            if stat.S_ISREG(metadata.st_mode):
                data = path.read_bytes()
                if normalize_home and path == home / ".codex" / "config.toml":
                    data = data.replace(marker, b"<HOME>")
                record.update(type="file", sha256=sha256_bytes(data))
            elif stat.S_ISDIR(metadata.st_mode):
                record["type"] = "directory"
            elif stat.S_ISLNK(metadata.st_mode):
                record.update(type="symlink", targetSha256=sha256_bytes(os.readlink(path).encode("utf-8")))
            else:
                record["type"] = "other"
            records.append(record)
    return sorted(records, key=lambda item: (item["path"], item["type"]))


def _surface_digest(home: Path) -> str:
    return sha256_bytes(b"".join(canonical_bytes(item) for item in _surface_records(home)))


def migration_plan(bundle_root: Path, home_value: Path, bundle_digest: str) -> dict[str, Any]:
    home = _temporary_home(home_value)
    require_sha256(bundle_digest, "INVALID_BUNDLE_DIGEST")
    source, rules = load_role_source(bundle_root)
    catalog = role_catalog(bundle_root, bundle_digest)
    codex = home / ".codex"
    agents = codex / "agents"
    skills = codex / "skills"
    if codex.is_symlink() or not codex.is_dir() or agents.is_symlink() or not agents.is_dir() or skills.is_symlink() or not skills.is_dir():
        raise TaskError("INVALID_MIGRATION_HOME")
    legacy = [name for name in LEGACY_ROLES if (agents / name).exists() or (agents / name).is_symlink()]
    already_installed = all((agents / f"{name}.toml").is_file() for name in ("gkd_acceptor", "gkd_ci_reviewer", "gkd_executor"))
    if len(legacy) > 1 or (not legacy and not already_installed):
        raise TaskError("LEGACY_ROLE_AMBIGUOUS")
    if legacy and ((agents / legacy[0]).is_symlink() or not (agents / legacy[0]).is_file()):
        raise TaskError("LEGACY_ROLE_AMBIGUOUS")
    for name in source["duplicateSkills"]:
        _regular(skills / name / "SKILL.md", "CANONICAL_SKILL_MISSING")
        _regular(home / ".agents" / "skills" / name / "SKILL.md", "DUPLICATE_SKILL_MISSING")
    value = {
        "schemaVersion": 1,
        "bundleDigest": bundle_digest,
        "roleSourceDigest": catalog["roleSourceDigest"],
        "hardRulesDigest": digest_object(rules),
        "legacyRole": "ci_reviewer",
        "installRoles": sorted(role_files(bundle_root, bundle_digest)),
        "installSkills": source["skills"],
        "disableDuplicateSkills": source["duplicateSkills"],
        "securitySkillRepair": True,
        "productionTarget": False,
    }
    value["planDigest"] = digest_object(value)
    return value


def _apply_to_stage(bundle_root: Path, stage: Path, final_home: Path, bundle_digest: str, plan: dict[str, Any]) -> None:
    source, _ = load_role_source(bundle_root)
    agents = stage / ".codex" / "agents"
    skills = stage / ".codex" / "skills"
    for name in LEGACY_ROLES:
        path = agents / name
        if path.exists() or path.is_symlink():
            if path.is_symlink() or not path.is_file():
                raise TaskError("LEGACY_ROLE_AMBIGUOUS")
            path.unlink()
    for name, content in role_files(bundle_root, bundle_digest).items():
        atomic_write(agents / name, content, mode=0o644)
    for name in source["skills"]:
        _copy_skill(bundle_root / "skills" / name, skills / name)
    _repair_security_skill(skills / "security-and-hardening")
    _update_config(stage / ".codex" / "config.toml", final_home, source["duplicateSkills"])
    verify_migration(bundle_root, stage, bundle_digest, expected_plan=plan, logical_home=final_home)


def apply_migration(
    bundle_root: Path,
    home_value: Path,
    bundle_digest: str,
    failure_hook: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    home = _temporary_home(home_value)
    plan = migration_plan(bundle_root, home, bundle_digest)
    before = _surface_digest(home)
    parent = home.parent
    stage = Path(tempfile.mkdtemp(prefix=".gkd-migration-stage-", dir=parent))
    stage.rmdir()
    backup = parent / f".gkd-migration-backup-{hashlib.sha256(os.fspath(home).encode()).hexdigest()[:16]}"
    if backup.exists() or backup.is_symlink():
        raise TaskError("MIGRATION_RECOVERY_REQUIRED")
    hook = failure_hook or (lambda phase: None)
    moved_old = False
    moved_new = False
    frozen = False
    try:
        shutil.copytree(home, stage, symlinks=True)
        _apply_to_stage(bundle_root, stage, home, bundle_digest, plan)
        hook("staged")
        os.replace(home, backup)
        moved_old = True
        hook("old_moved")
        os.replace(stage, home)
        moved_new = True
        hook("new_moved")
        shutil.rmtree(backup)
        moved_old = False
    except Exception:
        try:
            if moved_new and home.exists():
                os.replace(home, stage)
                moved_new = False
            if moved_old and backup.exists():
                os.replace(backup, home)
                moved_old = False
        except OSError:
            frozen = True
            # Keep both recovery images when an atomic rename cannot be completed.
            if not stage.exists() and home.exists():
                shutil.copytree(home, stage, symlinks=True)
            freeze = {
                "schemaVersion": 1,
                "status": "migration_frozen",
                "planDigest": plan["planDigest"],
                "beforeDigest": before,
                "backupDigest": _surface_digest(backup) if backup.exists() else None,
                "stageDigest": _surface_digest(stage) if stage.exists() else None,
            }
            atomic_write(parent / ".gkd-migration-freeze.json", canonical_bytes(freeze), mode=0o600)
            raise TaskError("MIGRATION_FROZEN") from None
        raise
    finally:
        if not frozen:
            for path in (stage, backup):
                if path.exists() and path != home:
                    shutil.rmtree(path)
    verified = verify_migration(bundle_root, home, bundle_digest, expected_plan=plan)
    return {"status": "migration_applied", "planDigest": plan["planDigest"], "beforeDigest": before, "afterDigest": verified["surfaceDigest"], "inventoryDigest": verified["inventoryDigest"]}


def verify_migration(bundle_root: Path, home_value: Path, bundle_digest: str, expected_plan: dict[str, Any] | None = None, logical_home: Path | None = None) -> dict[str, Any]:
    home = _temporary_home(home_value)
    configured_home = logical_home or home
    plan = expected_plan or migration_plan(bundle_root, home, bundle_digest)
    source, rules = load_role_source(bundle_root)
    catalog = role_catalog(bundle_root, bundle_digest)
    agents = home / ".codex" / "agents"
    skills = home / ".codex" / "skills"
    expected_roles = role_files(bundle_root, bundle_digest)
    for name, content in expected_roles.items():
        if _regular(agents / name, "ROLE_INSTALL_MISMATCH") != content:
            raise TaskError("ROLE_INSTALL_MISMATCH")
    if any((agents / name).exists() or (agents / name).is_symlink() for name in LEGACY_ROLES):
        raise TaskError("LEGACY_ROLE_PRESENT")
    for name in source["skills"]:
        if not (skills / name / "SKILL.md").is_file():
            raise TaskError("SKILL_INSTALL_MISMATCH")
    security = _regular(skills / "security-and-hardening" / "SKILL.md", "SECURITY_SKILL_MISSING").decode("utf-8")
    if f"description: {SECURITY_DESCRIPTION}" not in security or "references/security-checklist.md" in security:
        raise TaskError("SECURITY_SKILL_BROKEN_REFERENCE")
    config = tomllib.loads(_regular(home / ".codex" / "config.toml", "INVALID_CODEX_CONFIG").decode("utf-8"))
    entries = config.get("skills", {}).get("config", [])
    expected_paths = {os.fspath(configured_home / ".agents" / "skills" / name / "SKILL.md") for name in source["duplicateSkills"]}
    actual = {entry.get("path") for entry in entries if isinstance(entry, dict) and entry.get("enabled") is False}
    if not expected_paths.issubset(actual):
        raise TaskError("SKILL_OVERRIDE_MISMATCH")
    inventory = {
        "roles": {name: sha256_bytes(content) for name, content in sorted(expected_roles.items())},
        "skills": catalog["skillDigests"],
        "hardRulesDigest": digest_object(rules),
        "disabledDuplicates": source["duplicateSkills"],
    }
    return {"status": "migration_valid", "planDigest": plan["planDigest"], "surfaceDigest": _surface_digest(home), "inventoryDigest": digest_object(inventory), "roleDigests": {role["name"]: role["roleDigest"] for role in catalog["roles"]}, "skillDigests": catalog["skillDigests"]}
