"""Strict role source, TOML rendering, and minimal context manifests."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from gkd_task.canonical import (
    canonical_bytes,
    digest_object,
    read_canonical_json,
    require_keys,
    require_sha256,
    require_string,
    sha256_bytes,
)
from gkd_task.errors import TaskError


ROLE_NAMES = ("gkd_acceptor", "gkd_ci_reviewer", "gkd_executor")
SKILL_NAMES = (
    "gkd-accept",
    "gkd-ci-monitor",
    "gkd-execute",
    "gkd-local-verify",
    "gkd-main",
)
OPTIONAL_PACKS = {
    "ci-advice": {"roles": ("gkd_ci_reviewer", "gkd_executor"), "skills": ("gkd-optimize-ci",)},
    "review-remediation": {"roles": ("gkd_ci_reviewer", "gkd_executor"), "skills": ("gkd-review-remediation",)},
}
ALL_SKILL_NAMES = SKILL_NAMES + tuple(
    skill for name in sorted(OPTIONAL_PACKS) for skill in OPTIONAL_PACKS[name]["skills"]
)
SANDBOX_MODES = {"read-only", "workspace-write"}
ACTIVATION_PROVIDER = {"contractVersion": 1, "name": "codex-host-runtime"}
ROLE_CONTRACT = {
    "gkd_executor": ("gpt-5.6-sol", "xhigh", "workspace-write", 43200),
    "gkd_acceptor": ("gpt-5.6-sol", "xhigh", "read-only", 43200),
    "gkd_ci_reviewer": ("gpt-5.6-terra", "high", "read-only", 3600),
}


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def validate_role_source(value: dict[str, Any]) -> None:
    require_keys(
        value,
        {"schemaVersion", "roleConfigVersion", "roles", "skills", "optionalPacks", "duplicateSkills", "roleActions", "activationProvider"},
        "INVALID_ROLE_SOURCE",
    )
    if value["schemaVersion"] != 2 or value["roleConfigVersion"] != 2:
        raise TaskError("INVALID_ROLE_SOURCE")
    if value["skills"] != list(SKILL_NAMES):
        raise TaskError("INVALID_ROLE_SOURCE")
    if value["activationProvider"] != ACTIVATION_PROVIDER:
        raise TaskError("INVALID_ROLE_SOURCE")
    expected_packs = {
        name: {"roles": list(definition["roles"]), "skills": list(definition["skills"])}
        for name, definition in OPTIONAL_PACKS.items()
    }
    if value["optionalPacks"] != expected_packs:
        raise TaskError("INVALID_ROLE_SOURCE")
    actions = value["roleActions"]
    if not isinstance(actions, dict) or tuple(sorted(actions)) != ROLE_NAMES:
        raise TaskError("INVALID_ROLE_SOURCE")
    for names in actions.values():
        if not isinstance(names, list) or names != sorted(set(names)) or any(not isinstance(name, str) for name in names):
            raise TaskError("INVALID_ROLE_SOURCE")
    duplicates = value["duplicateSkills"]
    if not isinstance(duplicates, list) or duplicates != sorted(set(duplicates)) or len(duplicates) != 6:
        raise TaskError("INVALID_ROLE_SOURCE")
    roles = value["roles"]
    if not isinstance(roles, list) or sorted(role.get("name") for role in roles if isinstance(role, dict)) != list(ROLE_NAMES):
        raise TaskError("INVALID_ROLE_SOURCE")
    for role in roles:
        require_keys(
            role,
            {
                "name",
                "description",
                "model",
                "modelReasoningEffort",
                "sandboxMode",
                "runtimeSeconds",
                "developerInstructions",
                "skills",
                "hardRules",
            },
            "INVALID_ROLE_SOURCE",
        )
        for field in ("name", "model", "modelReasoningEffort", "sandboxMode"):
            require_string(role[field], "INVALID_ROLE_SOURCE")
        if not isinstance(role["description"], str) or not role["description"].strip() or "\x00" in role["description"]:
            raise TaskError("INVALID_ROLE_SOURCE")
        if role["sandboxMode"] not in SANDBOX_MODES or role["runtimeSeconds"] not in {3600, 43200}:
            raise TaskError("INVALID_ROLE_SOURCE")
        if (role["model"], role["modelReasoningEffort"], role["sandboxMode"], role["runtimeSeconds"]) != ROLE_CONTRACT[role["name"]]:
            raise TaskError("INVALID_ROLE_SOURCE")
        if not isinstance(role["developerInstructions"], str) or not role["developerInstructions"].strip():
            raise TaskError("INVALID_ROLE_SOURCE")
        if not isinstance(role["skills"], list) or len(role["skills"]) != len(set(role["skills"])) or not set(role["skills"]).issubset(SKILL_NAMES):
            raise TaskError("INVALID_ROLE_SOURCE")
        if not role["skills"] or role["hardRules"] != sorted(set(role["hardRules"])) or not role["hardRules"]:
            raise TaskError("INVALID_ROLE_SOURCE")


def validate_hard_rules(value: dict[str, Any]) -> None:
    require_keys(value, {"schemaVersion", "rules"}, "INVALID_HARD_RULES")
    if value["schemaVersion"] != 1 or not isinstance(value["rules"], list) or not value["rules"]:
        raise TaskError("INVALID_HARD_RULES")
    identifiers = []
    for rule in value["rules"]:
        if not isinstance(rule, dict):
            raise TaskError("INVALID_HARD_RULES")
        require_keys(rule, {"id", "owner", "summary"}, "INVALID_HARD_RULES")
        for field in ("id", "owner"):
            require_string(rule[field], "INVALID_HARD_RULES")
        if not isinstance(rule["summary"], str) or not rule["summary"].strip():
            raise TaskError("INVALID_HARD_RULES")
        identifiers.append(rule["id"])
    if identifiers != sorted(set(identifiers)):
        raise TaskError("INVALID_HARD_RULES")


def load_role_source(bundle_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    if bundle_root.is_symlink() or not bundle_root.is_dir():
        raise TaskError("INVALID_BUNDLE_ROOT")
    root = bundle_root.resolve()
    source = read_canonical_json(root / "config" / "role-routing.json", "INVALID_ROLE_SOURCE", validate_role_source)
    rules = read_canonical_json(root / "config" / "hard-rules.json", "INVALID_HARD_RULES", validate_hard_rules)
    return source, rules


def locked_bundle_record(bundle_root: Path) -> dict[str, Any]:
    root = bundle_root.resolve()
    candidates = [root / ".bundle" / "manifest.lock.json", root.parent / "manifest.lock.json"]
    matches = [path for path in candidates if path.is_file() and not path.is_symlink()]
    if len(matches) != 1:
        raise TaskError("INVALID_BUNDLE_ROOT")
    lock = read_canonical_json(matches[0], "INVALID_BUNDLE_ROOT")
    keys = {"bundleVersion", "contentDigest", "digestInputs", "inputFiles", "installFiles", "manifestSha256", "releaseStatus", "schemaSha256", "schemaVersion"}
    if lock.get("schemaVersion") == 2:
        keys |= {"coreDigest", "packs"}
    require_keys(lock, keys, "INVALID_BUNDLE_ROOT")
    require_sha256(lock["contentDigest"], "INVALID_BUNDLE_ROOT")
    return lock


def locked_bundle_digest(bundle_root: Path) -> str:
    return locked_bundle_record(bundle_root)["contentDigest"]


def locked_pack_digests(bundle_root: Path) -> dict[str, str]:
    lock = locked_bundle_record(bundle_root)
    result = {}
    for pack in lock.get("packs", ()):
        if not isinstance(pack, dict) or set(pack) != {"name", "files", "inputs", "packDigest"}:
            raise TaskError("INVALID_BUNDLE_ROOT")
        require_sha256(pack["packDigest"], "INVALID_BUNDLE_ROOT")
        result[pack["name"]] = pack["packDigest"]
    return result


def render_role(role: dict[str, Any], all_skills: list[str]) -> bytes:
    lines = [
        f"name = {_toml_string(role['name'])}",
        f"description = {_toml_string(role['description'])}",
        f"model = {_toml_string(role['model'])}",
        f"model_reasoning_effort = {_toml_string(role['modelReasoningEffort'])}",
        f"sandbox_mode = {_toml_string(role['sandboxMode'])}",
        f"developer_instructions = {_toml_string(role['developerInstructions'])}",
        "",
        "[agents]",
        "enabled = false",
    ]
    enabled = set(role["skills"])
    for skill in all_skills:
        lines.extend(
            (
                "",
                "[[skills.config]]",
                f"path = {_toml_string(f'../skills/{skill}/SKILL.md')}",
                f"enabled = {'true' if skill in enabled else 'false'}",
            )
        )
    return ("\n".join(lines) + "\n").encode("utf-8")


def _skill_inventory(bundle_root: Path, names: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for name in names:
        root = bundle_root / "skills" / name
        if root.is_symlink() or not root.is_dir():
            raise TaskError("INVALID_SKILL_INVENTORY")
        records = []
        for path in sorted(root.rglob("*")):
            if path.is_symlink() or (path.exists() and not path.is_file()):
                if path.is_dir() and not path.is_symlink():
                    continue
                raise TaskError("INVALID_SKILL_INVENTORY")
            records.append({"path": path.relative_to(root).as_posix(), "sha256": sha256_bytes(path.read_bytes())})
        if not records or records[0]["path"] != "SKILL.md":
            raise TaskError("INVALID_SKILL_INVENTORY")
        result[name] = digest_object(records)
    return result


def _selected_packs(names: Any) -> tuple[str, ...]:
    if not isinstance(names, (list, tuple)) or any(not isinstance(name, str) for name in names):
        raise TaskError("INVALID_OPTIONAL_PACK")
    selected = tuple(sorted(names))
    if len(selected) != len(set(selected)) or not set(selected).issubset(OPTIONAL_PACKS):
        raise TaskError("UNKNOWN_OPTIONAL_PACK")
    return selected


def _role_skills(role: dict[str, Any], packs: tuple[str, ...]) -> list[str]:
    skills = list(role["skills"])
    for name in packs:
        definition = OPTIONAL_PACKS[name]
        if role["name"] in definition["roles"]:
            skills.extend(definition["skills"])
    return skills


def _available_skills(packs: tuple[str, ...]) -> list[str]:
    return [*SKILL_NAMES, *(skill for name in packs for skill in OPTIONAL_PACKS[name]["skills"])]


def role_catalog(bundle_root: Path, bundle_digest: str, packs: tuple[str, ...] = ()) -> dict[str, Any]:
    require_sha256(bundle_digest, "INVALID_BUNDLE_DIGEST")
    if locked_bundle_digest(bundle_root) != bundle_digest:
        raise TaskError("BUNDLE_DIGEST_MISMATCH")
    source, rules = load_role_source(bundle_root)
    selected_packs = _selected_packs(packs)
    available_skills = _available_skills(selected_packs)
    skill_digests = _skill_inventory(bundle_root.resolve(), available_skills)
    rule_ids = {rule["id"] for rule in rules["rules"]}
    roles = []
    for role in sorted(source["roles"], key=lambda item: item["name"]):
        if not set(role["hardRules"]).issubset(rule_ids):
            raise TaskError("INVALID_ROLE_SOURCE")
        effective_skills = _role_skills(role, selected_packs)
        rendered = render_role({**role, "skills": effective_skills}, available_skills)
        semantic = deepcopy(role)
        semantic["skills"] = effective_skills
        semantic["optionalPacks"] = list(selected_packs)
        semantic["actions"] = source["roleActions"][role["name"]]
        semantic["skillDigests"] = {name: skill_digests[name] for name in effective_skills}
        semantic["roleConfigVersion"] = source["roleConfigVersion"]
        roles.append(
            {
                "name": role["name"],
                "model": role["model"],
                "modelReasoningEffort": role["modelReasoningEffort"],
                "sandboxMode": role["sandboxMode"],
                "runtimeSeconds": role["runtimeSeconds"],
                "skills": effective_skills,
                "hardRules": role["hardRules"],
                "roleDigest": digest_object(semantic),
                "configDigest": sha256_bytes(rendered),
            }
        )
    return {
        "schemaVersion": 1,
        "bundleDigest": bundle_digest,
        "activationProvider": deepcopy(source["activationProvider"]),
        "activationProviderDigest": digest_object(source["activationProvider"]),
        "roleSourceDigest": digest_object(source),
        "hardRulesDigest": digest_object(rules),
        "skillDigests": skill_digests,
        "roles": roles,
    }


def activation_provider(catalog: dict[str, Any]) -> dict[str, str | int]:
    require_keys(catalog, {"schemaVersion", "bundleDigest", "activationProvider", "activationProviderDigest", "roleSourceDigest", "hardRulesDigest", "skillDigests", "roles"}, "INVALID_ROLE_CATALOG")
    if catalog["schemaVersion"] != 1 or catalog["activationProvider"] != ACTIVATION_PROVIDER or catalog["activationProviderDigest"] != digest_object(ACTIVATION_PROVIDER):
        raise TaskError("INVALID_ROLE_CATALOG")
    require_sha256(catalog["activationProviderDigest"], "INVALID_ROLE_CATALOG")
    return deepcopy(catalog["activationProvider"])


def role_record(catalog: dict[str, Any], name: str) -> dict[str, Any]:
    require_string(name, "UNKNOWN_ROLE")
    matches = [role for role in catalog["roles"] if role["name"] == name]
    if len(matches) != 1:
        raise TaskError("UNKNOWN_ROLE")
    return deepcopy(matches[0])


def context_manifest(bundle_root: Path, bundle_digest: str, role_name: str, packs: tuple[str, ...] = ()) -> dict[str, Any]:
    source, rules = load_role_source(bundle_root)
    selected_packs = _selected_packs(packs)
    catalog = role_catalog(bundle_root, bundle_digest, selected_packs)
    role = role_record(catalog, role_name)
    definitions = {item["name"]: item for item in source["roles"]}
    definition = definitions[role_name]
    rule_map = {item["id"]: item for item in rules["rules"]}
    value = {
        "schemaVersion": 2,
        "roleName": role_name,
        "bundleDigest": bundle_digest,
        "roleDigest": role["roleDigest"],
        "configDigest": role["configDigest"],
        "skills": [
            {"name": name, "digest": catalog["skillDigests"][name]}
            for name in role["skills"]
        ],
        "optionalPacks": list(selected_packs),
        "packDigests": {
            name: locked_pack_digests(bundle_root)[name] for name in selected_packs
        },
        "omittedSkills": sorted(set(ALL_SKILL_NAMES) - set(role["skills"])),
        "hardRules": [rule_map[name] for name in definition["hardRules"]],
        "omittedContext": ["conversation-transcripts", "full-ci-logs", "private-session-state", "repository-pack", "wait-history"],
    }
    value["contextDigest"] = digest_object(value)
    return value


def role_files(bundle_root: Path, bundle_digest: str, packs: tuple[str, ...] = ()) -> dict[str, bytes]:
    source, _ = load_role_source(bundle_root)
    selected_packs = _selected_packs(packs)
    available_skills = _available_skills(selected_packs)
    catalog = role_catalog(bundle_root, bundle_digest, selected_packs)
    records = {item["name"]: item for item in catalog["roles"]}
    result = {}
    for role in source["roles"]:
        effective = {**role, "skills": _role_skills(role, selected_packs)}
        rendered = render_role(effective, available_skills)
        if sha256_bytes(rendered) != records[role["name"]]["configDigest"]:
            raise TaskError("ROLE_CONFIG_DRIFT")
        result[f"{role['name']}.toml"] = rendered
    return result


def role_action(bundle_root: Path, role_name: str, action: str) -> dict[str, Any]:
    source, _ = load_role_source(bundle_root)
    require_string(role_name, "UNKNOWN_ROLE")
    require_string(action, "INVALID_ROLE_ACTION")
    if role_name not in source["roleActions"]:
        raise TaskError("UNKNOWN_ROLE")
    allowed = action in source["roleActions"][role_name]
    value = {"schemaVersion": 1, "roleName": role_name, "action": action, "allowed": allowed}
    value["decisionDigest"] = digest_object(value)
    return value


def resume_snapshot(context: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    require_keys(context, {"roleName", "roleDigest", "configDigest", "contextDigest"}, "INVALID_RESUME_SNAPSHOT")
    require_keys(task, {"taskId", "phase", "head", "revision", "requirementsDigest", "planDigest", "implementationDigest"}, "INVALID_RESUME_SNAPSHOT")
    require_string(context["roleName"], "INVALID_RESUME_SNAPSHOT")
    for field in ("roleDigest", "configDigest", "contextDigest"):
        require_sha256(context[field], "INVALID_RESUME_SNAPSHOT")
    require_string(task["taskId"], "INVALID_RESUME_SNAPSHOT")
    require_string(task["phase"], "INVALID_RESUME_SNAPSHOT")
    if not isinstance(task["revision"], int) or task["revision"] < 0:
        raise TaskError("INVALID_RESUME_SNAPSHOT")
    from gkd_task.canonical import require_sha1

    require_sha1(task["head"], "INVALID_RESUME_SNAPSHOT")
    for field in ("requirementsDigest", "planDigest", "implementationDigest"):
        require_sha256(task[field], "INVALID_RESUME_SNAPSHOT")
    value = {"schemaVersion": 1, **context, "task": deepcopy(task), "omitted": ["documentBodies", "logs", "transcripts", "runtimeSecrets"]}
    value["snapshotDigest"] = digest_object(value)
    return value
