"""Deterministic bootstrap tooling for the GKD development bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tempfile
import gkd_toml as tomllib
from typing import Any


sys.dont_write_bytecode = True


SCHEMA_VERSION = 1
DEVELOPMENT_VERSION = re.compile(r"^0\.0\.0-dev\.[0-9]+$")
STABLE_VERSION = re.compile(r"^(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)$")
HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_MODES = {"0644", "0755"}
ALLOWED_KINDS = {"executable", "library"}
ALLOWED_INPUT_KINDS = {"test", "release-verification"}
METADATA_ROOT = "gkd/.bundle"
SCHEMA_TARGET = f"{METADATA_ROOT}/manifest.schema.json"
MANIFEST_TARGET = f"{METADATA_ROOT}/manifest.json"
LOCK_TARGET = f"{METADATA_ROOT}/manifest.lock.json"
INSTALL_TARGET = f"{METADATA_ROOT}/install.json"
PROTECTED_SURFACES = (
    "config.toml",
    "skills",
    "agents",
    "roles",
    "plugins",
    "mcp",
    "gkd",
    ".gkd",
)
VISION_HEADINGS = (
    "使命",
    "服务对象与用户承诺",
    "成功标准",
    "核心原则",
    "冲突时的决策顺序",
    "明确非目标",
    "演进规则",
)
ALIGNMENT_TEMPLATE = """# Vision Alignment

> 愿景一致性不构成授权。executor 与 acceptor 不得借此扩大已批准范围；如方案改变材料性承诺，必须先取得新的用户决定。

## 可读原则名称

<!-- 使用 VISION.md 中的人类可读原则名称，不填写机器 ID。 -->

## 支持方式

<!-- 说明方案如何支持这些原则。 -->

## 张力或偏离

<!-- 写明已知张力、取舍或偏离；没有时写“无”。 -->

## 是否改变当前材料性承诺

<!-- 只能填写“否”或说明需要用户重新决定，不能自行授权。 -->

## 方案内 decision/ADR 引用（仅在需要时）

<!-- 只引用本方案实际需要的 decision/ADR；没有时写“无”。 -->
"""


class BundleError(Exception):
    """A stable, path-free machine error."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class MachineParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise BundleError("INVALID_ARGUMENTS")


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _require_keys(value: dict[str, Any], expected: set[str], code: str) -> None:
    if set(value) != expected:
        raise BundleError(code)


def _relative_path(value: Any, code: str, prefix: str | None = None) -> str:
    if (
        not isinstance(value, str)
        or not value
        or "\\" in value
        or ":" in value
        or "\x00" in value
    ):
        raise BundleError(code)
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise BundleError(code)
    normalized = path.as_posix()
    if normalized != value or (prefix and not normalized.startswith(prefix)):
        raise BundleError(code)
    return normalized


def _existing_directory(value: Path, code: str) -> Path:
    if value.is_symlink() or not value.is_dir():
        raise BundleError(code)
    return value.resolve()


def _require_regular_mode(
    path: Path,
    expected_mode: int,
    type_code: str,
    mode_code: str,
) -> os.stat_result:
    try:
        metadata = path.lstat()
    except OSError:
        raise BundleError(type_code) from None
    if not stat.S_ISREG(metadata.st_mode):
        raise BundleError(type_code)
    if stat.S_IMODE(metadata.st_mode) != expected_mode:
        raise BundleError(mode_code)
    return metadata


def _read_canonical_json(
    path: Path,
    code: str,
    mode_code: str | None = None,
) -> dict[str, Any]:
    _require_regular_mode(path, 0o644, code, mode_code or code)
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise BundleError(code) from None
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise BundleError(code)
    return value


def _atomic_write(path: Path, content: bytes, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _forbidden_content(data: bytes) -> bool:
    text = data.decode("utf-8", errors="ignore").casefold()
    current_roots = (
        Path.home().resolve().as_posix().casefold(),
        Path(tempfile.gettempdir()).resolve().as_posix().casefold(),
    )
    for root in current_roots:
        if root and re.search(
            rf"(?<![a-z0-9._-]){re.escape(root.rstrip('/'))}(?:/|(?=$|[\s\"'<>]))",
            text,
        ):
            return True
    machine_path_patterns = (
        r"(?<![a-z0-9._-])/(?:users|home)/[^/\s\"'<>]+(?:/[^\s\"'<>]*)?",
        r"(?<![a-z0-9._-])/(?:tmp|private/(?:tmp|var)|var/folders)/[^\s\"'<>]+",
        r"(?<![a-z0-9._-])[a-z]:[\\/][^\s\"'<>]+",
    )
    return any(re.search(pattern, text) for pattern in machine_path_patterns)


def _contains_project_marker(data: bytes) -> bool:
    text = data.decode("utf-8", errors="ignore").casefold()
    phrases = (
        "".join(("ai", "o coding hub")),
        "".join(("ai", "o-coding-hub")),
    )
    path_segment = "".join(("a", "io"))
    return any(phrase in text for phrase in phrases) or re.search(
        rf"(?:^|[\\/]){path_segment}(?:[\\/]|$)", text
    ) is not None


def _walk_regular_files(root: Path, code: str) -> dict[str, Path]:
    if root.is_symlink() or not root.is_dir():
        raise BundleError(code)
    found: dict[str, Path] = {}
    for current, directories, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        for name in directories:
            candidate = current_path / name
            if candidate.is_symlink():
                raise BundleError(code)
        for name in files:
            candidate = current_path / name
            metadata = candidate.lstat()
            if not stat.S_ISREG(metadata.st_mode):
                raise BundleError(code)
            found[candidate.relative_to(root).as_posix()] = candidate
    return found


def _validate_schema_document(schema: Any) -> None:
    if not isinstance(schema, dict):
        raise BundleError("INVALID_MANIFEST_SCHEMA")
    _require_keys(
        schema,
        {"schemaVersion", "title", "type", "additionalProperties", "required", "properties"},
        "INVALID_MANIFEST_SCHEMA",
    )
    if (
        schema["schemaVersion"] != SCHEMA_VERSION
        or schema["type"] != "object"
        or schema["additionalProperties"] is not False
        or schema["required"]
        != ["schemaVersion", "bundleVersion", "releaseStatus", "components"]
        or not isinstance(schema["properties"], dict)
        or set(schema["properties"])
        != {"schemaVersion", "bundleVersion", "releaseStatus", "components"}
        or schema["properties"].get("schemaVersion") != {"const": SCHEMA_VERSION}
    ):
        raise BundleError("INVALID_MANIFEST_SCHEMA")


def _load_schema(source_root: Path) -> bytes:
    path = source_root / "manifest.schema.json"
    _require_regular_mode(
        path,
        0o644,
        "INVALID_MANIFEST_SCHEMA",
        "SOURCE_METADATA_MODE_MISMATCH",
    )
    try:
        raw = path.read_bytes()
        schema = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise BundleError("INVALID_MANIFEST_SCHEMA") from None
    _validate_schema_document(schema)
    return raw


def _load_source_declaration(source_root: Path) -> dict[str, Any]:
    path = source_root / "source.toml"
    try:
        if not stat.S_ISREG(path.lstat().st_mode):
            raise BundleError("INVALID_SOURCE_DECLARATION")
        with path.open("rb") as stream:
            declaration = tomllib.load(stream)
    except BundleError:
        raise
    except (OSError, tomllib.TOMLDecodeError):
        raise BundleError("INVALID_SOURCE_DECLARATION") from None
    if not isinstance(declaration, dict):
        raise BundleError("INVALID_SOURCE_DECLARATION")
    _require_keys(
        declaration,
        {"schema_version", "bundle_version", "release_status", "components", "inputs"},
        "INVALID_SOURCE_DECLARATION",
    )
    if declaration["schema_version"] != SCHEMA_VERSION:
        raise BundleError("INVALID_SOURCE_DECLARATION")
    version = declaration["bundle_version"]
    if not isinstance(version, str) or not (DEVELOPMENT_VERSION.fullmatch(version) or STABLE_VERSION.fullmatch(version)):
        raise BundleError("INVALID_BUNDLE_VERSION")
    expected_status = "development" if DEVELOPMENT_VERSION.fullmatch(version) else "release-candidate"
    if declaration["release_status"] != expected_status:
        raise BundleError("INVALID_RELEASE_STATUS")
    components = declaration["components"]
    if not isinstance(components, list) or not components:
        raise BundleError("INVALID_SOURCE_DECLARATION")

    names: set[str] = set()
    sources: set[str] = set()
    targets: set[str] = set()
    inputs = declaration["inputs"]
    if not isinstance(inputs, list) or not inputs:
        raise BundleError("INVALID_SOURCE_DECLARATION")
    input_names: set[str] = set()
    input_sources: set[str] = set()
    normalized_inputs = []
    for input_file in inputs:
        if not isinstance(input_file, dict):
            raise BundleError("INVALID_INPUT_FILE")
        _require_keys(input_file, {"name", "kind", "source", "mode"}, "INVALID_INPUT_FILE")
        name = input_file["name"]
        kind = input_file["kind"]
        source = _relative_path(input_file["source"], "INVALID_INPUT_PATH", "inputs/")
        mode = input_file["mode"]
        if (
            not isinstance(name, str)
            or not re.fullmatch(r"[a-z][a-z0-9-]*", name)
            or name in input_names
            or kind not in ALLOWED_INPUT_KINDS
            or mode not in ALLOWED_MODES
            or source in input_sources
            or source in sources
            or _forbidden_content(name.encode("utf-8"))
            or _forbidden_content(source.encode("utf-8"))
        ):
            raise BundleError("INVALID_INPUT_FILE")
        input_names.add(name)
        input_sources.add(source)
        input_path = source_root / source
        _require_regular_mode(
            input_path, int(mode, 8), "INVALID_INPUT_FILE", "INPUT_MODE_MISMATCH"
        )
        content = input_path.read_bytes()
        if _forbidden_content(content):
            raise BundleError("FORBIDDEN_SOURCE_CONTENT")
        normalized_inputs.append(
            {
                "name": name,
                "kind": kind,
                "source": source,
                "type": "file",
                "mode": mode,
                "size": len(content),
                "sha256": sha256_bytes(content),
            }
        )
    normalized_components = []
    for component in components:
        if not isinstance(component, dict):
            raise BundleError("INVALID_COMPONENT")
        _require_keys(component, {"name", "kind", "files"}, "INVALID_COMPONENT")
        name = component["name"]
        kind = component["kind"]
        files = component["files"]
        if (
            not isinstance(name, str)
            or not re.fullmatch(r"[a-z][a-z0-9-]*", name)
            or name in names
            or kind not in ALLOWED_KINDS
            or not isinstance(files, list)
            or not files
        ):
            raise BundleError("INVALID_COMPONENT")
        if _forbidden_content(name.encode("utf-8")):
            raise BundleError("FORBIDDEN_DECLARATION_CONTENT")
        names.add(name)
        normalized_files = []
        for item in files:
            if not isinstance(item, dict):
                raise BundleError("INVALID_COMPONENT_FILE")
            _require_keys(item, {"source", "target", "mode"}, "INVALID_COMPONENT_FILE")
            source = _relative_path(item["source"], "INVALID_SOURCE_PATH", "payload/")
            target = _relative_path(item["target"], "INVALID_TARGET_PATH", "gkd/")
            mode = item["mode"]
            if _forbidden_content(source.encode("utf-8")) or _forbidden_content(
                target.encode("utf-8")
            ):
                raise BundleError("FORBIDDEN_DECLARATION_CONTENT")
            if mode not in ALLOWED_MODES or source in sources or target in targets:
                raise BundleError("INVALID_COMPONENT_FILE")
            sources.add(source)
            targets.add(target)
            normalized_files.append(
                {"source": source, "target": target, "type": "file", "mode": mode}
            )
        normalized_components.append(
            {"name": name, "kind": kind, "files": sorted(normalized_files, key=lambda x: x["source"])}
        )

    payload_files = _walk_regular_files(source_root / "payload", "INVALID_PAYLOAD_TYPE")
    actual_sources = {f"payload/{path}" for path in payload_files}
    if actual_sources != sources:
        raise BundleError("UNDECLARED_OR_MISSING_PAYLOAD")
    input_files = _walk_regular_files(source_root / "inputs", "INVALID_INPUT_TYPE")
    actual_inputs = {f"inputs/{path}" for path in input_files}
    if actual_inputs != input_sources:
        raise BundleError("UNDECLARED_OR_MISSING_INPUT")
    for source in sorted(sources):
        path = source_root / source
        actual_mode = stat.S_IMODE(path.lstat().st_mode)
        declared_mode = next(
            item["mode"]
            for component in normalized_components
            for item in component["files"]
            if item["source"] == source
        )
        if actual_mode != int(declared_mode, 8):
            raise BundleError("SOURCE_MODE_MISMATCH")
        if _forbidden_content(path.read_bytes()):
            raise BundleError("FORBIDDEN_SOURCE_CONTENT")

    return {
        "schemaVersion": SCHEMA_VERSION,
        "bundleVersion": version,
        "releaseStatus": expected_status,
        "components": sorted(normalized_components, key=lambda x: x["name"]),
        "inputs": sorted(normalized_inputs, key=lambda x: x["source"]),
    }


def _digest_record(path: str, mode: str, content: bytes) -> dict[str, Any]:
    return {
        "path": path,
        "type": "file",
        "mode": mode,
        "sha256": sha256_bytes(content),
    }


def _validate_generated_metadata_modes(source_root: Path) -> None:
    for name, type_code in (
        ("manifest.json", "INVALID_MANIFEST"),
        ("manifest.lock.json", "INVALID_LOCK"),
    ):
        path = source_root / name
        if path.exists() or path.is_symlink():
            _require_regular_mode(
                path,
                0o644,
                type_code,
                "SOURCE_METADATA_MODE_MISMATCH",
            )


def _validate_project_contamination(source_root: Path) -> None:
    files = _walk_regular_files(source_root, "INVALID_CANONICAL_SOURCE_TYPE")
    if any(_contains_project_marker(path.read_bytes()) for path in files.values()):
        raise BundleError("PROJECT_SPECIFIC_SOURCE_CONTENT")


def _build_source_outputs(source_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    _validate_generated_metadata_modes(source_root)
    schema_bytes = _load_schema(source_root)
    declaration = _load_source_declaration(source_root)
    manifest = {
        key: declaration[key]
        for key in ("schemaVersion", "bundleVersion", "releaseStatus", "components")
    }
    manifest_bytes = canonical_bytes(manifest)
    digest_inputs = [
        _digest_record("manifest.schema.json", "0644", schema_bytes),
        _digest_record("manifest.json", "0644", manifest_bytes),
    ]
    install_files = []
    for component in manifest["components"]:
        for item in component["files"]:
            content = (source_root / item["source"]).read_bytes()
            digest_inputs.append(_digest_record(item["source"], item["mode"], content))
            install_files.append(
                {
                    "component": component["name"],
                    "source": item["source"],
                    "target": item["target"],
                    "type": "file",
                    "mode": item["mode"],
                    "size": len(content),
                    "sha256": sha256_bytes(content),
                }
            )
    input_files = [dict(item) for item in declaration["inputs"]]
    for item in input_files:
        digest_inputs.append(
            {
                "path": item["source"],
                "type": item["type"],
                "mode": item["mode"],
                "sha256": item["sha256"],
            }
        )
    digest_inputs.sort(key=lambda item: item["path"])
    install_files.sort(key=lambda item: item["source"])
    content_digest = sha256_bytes(b"".join(canonical_bytes(item) for item in digest_inputs))
    lock = {
        "schemaVersion": SCHEMA_VERSION,
        "bundleVersion": manifest["bundleVersion"],
        "releaseStatus": manifest["releaseStatus"],
        "schemaSha256": sha256_bytes(schema_bytes),
        "manifestSha256": sha256_bytes(manifest_bytes),
        "digestInputs": digest_inputs,
        "installFiles": install_files,
        "inputFiles": input_files,
        "contentDigest": content_digest,
    }
    return manifest, lock


def generate(source_root_value: Path) -> dict[str, Any]:
    source_root = _existing_directory(source_root_value, "INVALID_SOURCE_ROOT")
    manifest, lock = _build_source_outputs(source_root)
    _atomic_write(source_root / "manifest.json", canonical_bytes(manifest))
    _atomic_write(source_root / "manifest.lock.json", canonical_bytes(lock))
    return {
        "status": "generated",
        "bundleVersion": manifest["bundleVersion"],
        "contentDigest": lock["contentDigest"],
        "files": len(lock["installFiles"]),
    }


def _validated_source(source_root_value: Path) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    source_root = _existing_directory(source_root_value, "INVALID_SOURCE_ROOT")
    expected_manifest, expected_lock = _build_source_outputs(source_root)
    actual_manifest = _read_canonical_json(
        source_root / "manifest.json",
        "INVALID_MANIFEST",
        "SOURCE_METADATA_MODE_MISMATCH",
    )
    actual_lock = _read_canonical_json(
        source_root / "manifest.lock.json",
        "INVALID_LOCK",
        "SOURCE_METADATA_MODE_MISMATCH",
    )
    if actual_manifest != expected_manifest:
        raise BundleError("MANIFEST_MISMATCH")
    if actual_lock != expected_lock:
        raise BundleError("LOCK_OR_DIGEST_MISMATCH")
    return source_root, actual_manifest, actual_lock


def verify_input(source_root_value: Path, name: str) -> dict[str, Any]:
    """Verify one explicit test or release-verification input outside the install surface."""

    source_root, _, lock = _validated_source(source_root_value)
    if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9-]*", name):
        raise BundleError("INVALID_INPUT_NAME")
    for item in lock["inputFiles"]:
        if item["name"] != name:
            continue
        path = source_root / item["source"]
        _require_regular_mode(path, int(item["mode"], 8), "INPUT_MISSING", "INPUT_MODE_MISMATCH")
        content = path.read_bytes()
        if len(content) != item["size"] or sha256_bytes(content) != item["sha256"]:
            raise BundleError("INPUT_CONTENT_MISMATCH")
        return {
            "status": "verified",
            "name": item["name"],
            "kind": item["kind"],
            "source": item["source"],
            "sha256": item["sha256"],
        }
    raise BundleError("INPUT_UNKNOWN")


def verify_bundle_root(bundle_root_value: Path) -> dict[str, Any]:
    """Verify the complete canonical or installed bundle behind a payload root."""

    bundle_root = _existing_directory(bundle_root_value, "INVALID_BUNDLE_ROOT")
    source_root = bundle_root.parent
    if bundle_root.name == "payload" and (source_root / "source.toml").is_file():
        _, manifest, lock = _validated_source(source_root)
        return {
            "status": "verified",
            "layout": "canonical-source",
            "bundleVersion": manifest["bundleVersion"],
            "contentDigest": lock["contentDigest"],
            "files": len(lock["installFiles"]),
        }
    if bundle_root.name == "gkd" and (bundle_root / ".bundle").is_dir():
        result = _verify_target(bundle_root.parent)
        return {
            "status": result["status"],
            "layout": "installed",
            "bundleVersion": result["bundleVersion"],
            "contentDigest": result["contentDigest"],
            "files": len(result["files"]),
        }
    raise BundleError("INVALID_BUNDLE_ROOT")


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _safe_temp_paths(temporary_root_value: Path, target_value: Path) -> tuple[Path, Path]:
    temporary_root = _existing_directory(temporary_root_value, "INVALID_TEMPORARY_ROOT")
    target = _existing_directory(target_value, "INVALID_TARGET")
    system_temporary = Path(tempfile.gettempdir()).resolve()
    home = Path.home().resolve()
    if (
        not _is_within(temporary_root, system_temporary)
        or temporary_root == system_temporary
        or not _is_within(target, temporary_root)
        or target == temporary_root
        or _is_within(target, home)
    ):
        raise BundleError("TARGET_OUTSIDE_TEMPORARY_BOUNDARY")
    relative = target.relative_to(temporary_root)
    current = temporary_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise BundleError("TARGET_SYMLINK")
    return temporary_root, target


def _install_record(manifest: dict[str, Any], lock: dict[str, Any]) -> dict[str, Any]:
    metadata = (
        (SCHEMA_TARGET, lock["schemaSha256"]),
        (MANIFEST_TARGET, lock["manifestSha256"]),
        (LOCK_TARGET, sha256_bytes(canonical_bytes(lock))),
    )
    owned_files = [
        {
            "path": item["target"],
            "type": "file",
            "mode": item["mode"],
            "size": item["size"],
            "sha256": item["sha256"],
        }
        for item in lock["installFiles"]
    ]
    for path, digest in metadata:
        owned_files.append(
            {"path": path, "type": "file", "mode": "0644", "sha256": digest}
        )
    owned_files.sort(key=lambda item: item["path"])
    return {
        "schemaVersion": SCHEMA_VERSION,
        "bundleVersion": manifest["bundleVersion"],
        "releaseStatus": manifest["releaseStatus"],
        "contentDigest": lock["contentDigest"],
        "ownedFiles": owned_files,
    }


def _expected_directories(files: set[str]) -> set[str]:
    directories = {"gkd"}
    for value in files:
        parent = PurePosixPath(value).parent
        while parent.as_posix() not in {".", ""}:
            directories.add(parent.as_posix())
            parent = parent.parent
    return directories


def _scan_installed(target: Path) -> tuple[set[str], set[str]]:
    owned_root = target / "gkd"
    if owned_root.is_symlink() or not owned_root.is_dir():
        raise BundleError("MISSING_INSTALLATION")
    files: set[str] = set()
    directories = {"gkd"}
    for current, child_directories, child_files in os.walk(owned_root, followlinks=False):
        current_path = Path(current)
        for name in child_directories:
            candidate = current_path / name
            if candidate.is_symlink():
                raise BundleError("TARGET_DRIFT_SYMLINK")
            directories.add(candidate.relative_to(target).as_posix())
        for name in child_files:
            candidate = current_path / name
            metadata = candidate.lstat()
            if not stat.S_ISREG(metadata.st_mode):
                raise BundleError("TARGET_DRIFT_TYPE")
            files.add(candidate.relative_to(target).as_posix())
    return files, directories


def _validate_input_records(inputs: Any, code: str) -> None:
    if not isinstance(inputs, list) or not inputs:
        raise BundleError(code)
    names: set[str] = set()
    sources: set[str] = set()
    for item in inputs:
        if not isinstance(item, dict):
            raise BundleError(code)
        _require_keys(item, {"name", "kind", "source", "type", "mode", "size", "sha256"}, code)
        name = item["name"]
        source = _relative_path(item["source"], code, "inputs/")
        if (
            not isinstance(name, str)
            or not re.fullmatch(r"[a-z][a-z0-9-]*", name)
            or name in names
            or item["kind"] not in ALLOWED_INPUT_KINDS
            or item["type"] != "file"
            or item["mode"] not in ALLOWED_MODES
            or not isinstance(item["size"], int)
            or item["size"] < 0
            or not isinstance(item["sha256"], str)
            or not HEX_SHA256.fullmatch(item["sha256"])
            or source in sources
            or _forbidden_content(name.encode("utf-8"))
            or _forbidden_content(source.encode("utf-8"))
        ):
            raise BundleError(code)
        names.add(name)
        sources.add(source)
    if inputs != sorted(inputs, key=lambda item: item["source"]):
        raise BundleError(code)


def _validate_installed_manifest(manifest: dict[str, Any]) -> None:
    _require_keys(
        manifest,
        {"schemaVersion", "bundleVersion", "releaseStatus", "components"},
        "INSTALLED_MANIFEST_INVALID",
    )
    if (
        manifest["schemaVersion"] != SCHEMA_VERSION
        or not isinstance(manifest["bundleVersion"], str)
        or not (DEVELOPMENT_VERSION.fullmatch(manifest["bundleVersion"]) or STABLE_VERSION.fullmatch(manifest["bundleVersion"]))
        or manifest["releaseStatus"] != ("development" if DEVELOPMENT_VERSION.fullmatch(manifest["bundleVersion"]) else "release-candidate")
        or not isinstance(manifest["components"], list)
        or not manifest["components"]
    ):
        raise BundleError("INSTALLED_MANIFEST_INVALID")
    seen_names: set[str] = set()
    seen_sources: set[str] = set()
    seen_targets: set[str] = set()
    for component in manifest["components"]:
        if not isinstance(component, dict):
            raise BundleError("INSTALLED_MANIFEST_INVALID")
        _require_keys(component, {"name", "kind", "files"}, "INSTALLED_MANIFEST_INVALID")
        name = component["name"]
        if (
            not isinstance(name, str)
            or not re.fullmatch(r"[a-z][a-z0-9-]*", name)
            or name in seen_names
            or _forbidden_content(name.encode("utf-8"))
            or component["kind"] not in ALLOWED_KINDS
            or not isinstance(component["files"], list)
            or not component["files"]
        ):
            raise BundleError("INSTALLED_MANIFEST_INVALID")
        seen_names.add(name)
        for item in component["files"]:
            if not isinstance(item, dict):
                raise BundleError("INSTALLED_MANIFEST_INVALID")
            _require_keys(item, {"source", "target", "type", "mode"}, "INSTALLED_MANIFEST_INVALID")
            source = _relative_path(item["source"], "INSTALLED_MANIFEST_INVALID", "payload/")
            target = _relative_path(item["target"], "INSTALLED_MANIFEST_INVALID", "gkd/")
            if (
                item["type"] != "file"
                or item["mode"] not in ALLOWED_MODES
                or source in seen_sources
                or target in seen_targets
            ):
                raise BundleError("INSTALLED_MANIFEST_INVALID")
            seen_sources.add(source)
            seen_targets.add(target)
    if manifest["components"] != sorted(manifest["components"], key=lambda item: item["name"]):
        raise BundleError("INSTALLED_MANIFEST_INVALID")
    if any(
        component["files"] != sorted(component["files"], key=lambda item: item["source"])
        for component in manifest["components"]
    ):
        raise BundleError("INSTALLED_MANIFEST_INVALID")


def _verify_target(target: Path) -> dict[str, Any]:
    actual_files, actual_directories = _scan_installed(target)
    schema_path = target / SCHEMA_TARGET
    manifest_path = target / MANIFEST_TARGET
    lock_path = target / LOCK_TARGET
    install_path = target / INSTALL_TARGET
    schema_metadata = _require_regular_mode(
        schema_path,
        0o644,
        "INSTALLED_SCHEMA_INVALID",
        "TARGET_DRIFT_MODE",
    )
    try:
        schema_bytes = schema_path.read_bytes()
        schema = json.loads(schema_bytes)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise BundleError("INSTALLED_SCHEMA_INVALID") from None
    try:
        _validate_schema_document(schema)
    except BundleError:
        raise BundleError("INSTALLED_SCHEMA_INVALID") from None
    manifest_metadata = _require_regular_mode(
        manifest_path,
        0o644,
        "INSTALLED_MANIFEST_INVALID",
        "TARGET_DRIFT_MODE",
    )
    _require_regular_mode(
        lock_path,
        0o644,
        "INSTALLED_LOCK_INVALID",
        "TARGET_DRIFT_MODE",
    )
    _require_regular_mode(
        install_path,
        0o644,
        "INSTALL_RECORD_INVALID",
        "TARGET_DRIFT_MODE",
    )
    manifest = _read_canonical_json(
        manifest_path, "INSTALLED_MANIFEST_INVALID", "TARGET_DRIFT_MODE"
    )
    lock = _read_canonical_json(
        lock_path, "INSTALLED_LOCK_INVALID", "TARGET_DRIFT_MODE"
    )
    install_record = _read_canonical_json(
        install_path, "INSTALL_RECORD_INVALID", "TARGET_DRIFT_MODE"
    )
    _validate_installed_manifest(manifest)
    _require_keys(
        lock,
        {
            "schemaVersion",
            "bundleVersion",
            "releaseStatus",
            "schemaSha256",
            "manifestSha256",
            "digestInputs",
            "installFiles",
            "inputFiles",
            "contentDigest",
        },
        "INSTALLED_LOCK_INVALID",
    )
    if (
        lock["schemaVersion"] != SCHEMA_VERSION
        or lock["bundleVersion"] != manifest["bundleVersion"]
        or lock["releaseStatus"] != manifest["releaseStatus"]
        or lock["schemaSha256"] != sha256_bytes(schema_bytes)
        or lock["manifestSha256"] != sha256_bytes(canonical_bytes(manifest))
        or not isinstance(lock["installFiles"], list)
        or not isinstance(lock["inputFiles"], list)
        or not isinstance(lock["digestInputs"], list)
        or not isinstance(lock["contentDigest"], str)
        or not HEX_SHA256.fullmatch(lock["contentDigest"])
    ):
        raise BundleError("INSTALLED_LOCK_INVALID")

    manifest_mapping = {
        item["source"]: (component["name"], item["target"], item["mode"])
        for component in manifest["components"]
        for item in component["files"]
    }
    _validate_input_records(lock["inputFiles"], "INSTALLED_LOCK_INVALID")
    digest_inputs = [
        _digest_record(
            "manifest.schema.json",
            format(stat.S_IMODE(schema_metadata.st_mode), "04o"),
            schema_bytes,
        ),
        _digest_record(
            "manifest.json",
            format(stat.S_IMODE(manifest_metadata.st_mode), "04o"),
            canonical_bytes(manifest),
        ),
    ]
    for item in lock["inputFiles"]:
        digest_inputs.append(
            {
                "path": item["source"],
                "type": item["type"],
                "mode": item["mode"],
                "sha256": item["sha256"],
            }
        )
    normalized_files = []
    seen_sources: set[str] = set()
    for item in lock["installFiles"]:
        if not isinstance(item, dict):
            raise BundleError("INSTALLED_LOCK_INVALID")
        _require_keys(
            item,
            {"component", "source", "target", "type", "mode", "size", "sha256"},
            "INSTALLED_LOCK_INVALID",
        )
        source = item["source"]
        if (
            source not in manifest_mapping
            or source in seen_sources
            or manifest_mapping[source] != (item["component"], item["target"], item["mode"])
            or item["type"] != "file"
            or not isinstance(item["size"], int)
            or not isinstance(item["sha256"], str)
            or not HEX_SHA256.fullmatch(item["sha256"])
        ):
            raise BundleError("INSTALLED_LOCK_INVALID")
        seen_sources.add(source)
        path = target / item["target"]
        try:
            metadata = path.lstat()
            content = path.read_bytes()
        except OSError:
            raise BundleError("TARGET_DRIFT_MISSING") from None
        if not stat.S_ISREG(metadata.st_mode):
            raise BundleError("TARGET_DRIFT_TYPE")
        if stat.S_IMODE(metadata.st_mode) != int(item["mode"], 8):
            raise BundleError("TARGET_DRIFT_MODE")
        if len(content) != item["size"] or sha256_bytes(content) != item["sha256"]:
            raise BundleError("TARGET_DRIFT_CONTENT")
        digest_inputs.append(_digest_record(source, item["mode"], content))
        normalized_files.append(
            {
                "path": item["target"],
                "type": "file",
                "mode": item["mode"],
                "size": item["size"],
                "sha256": item["sha256"],
            }
        )
    if set(manifest_mapping) != seen_sources:
        raise BundleError("INSTALLED_LOCK_INVALID")
    digest_inputs.sort(key=lambda value: value["path"])
    if digest_inputs != lock["digestInputs"]:
        raise BundleError("INSTALLED_LOCK_INVALID")
    digest = sha256_bytes(b"".join(canonical_bytes(item) for item in digest_inputs))
    if digest != lock["contentDigest"]:
        raise BundleError("INSTALLED_DIGEST_MISMATCH")

    expected_install = _install_record(manifest, lock)
    if install_record != expected_install:
        raise BundleError("INSTALL_RECORD_INVALID")
    expected_files = {item["path"] for item in expected_install["ownedFiles"]}
    expected_files.add(INSTALL_TARGET)
    if actual_files != expected_files:
        raise BundleError("TARGET_DRIFT_EXTRA_OR_MISSING")
    if actual_directories != _expected_directories(expected_files):
        raise BundleError("TARGET_DRIFT_DIRECTORY")
    for path in (SCHEMA_TARGET, MANIFEST_TARGET, LOCK_TARGET, INSTALL_TARGET):
        installed_path = target / path
        metadata = installed_path.lstat()
        content = installed_path.read_bytes()
        normalized_files.append(
            {
                "path": path,
                "type": "file",
                "mode": format(stat.S_IMODE(metadata.st_mode), "04o"),
                "size": len(content),
                "sha256": sha256_bytes(content),
            }
        )
    normalized_files.sort(key=lambda item: item["path"])
    return {
        "status": "verified",
        "bundleVersion": manifest["bundleVersion"],
        "contentDigest": lock["contentDigest"],
        "files": normalized_files,
    }


def install(source_root_value: Path, temporary_root_value: Path, target_value: Path) -> dict[str, Any]:
    source_root, manifest, lock = _validated_source(source_root_value)
    temporary_root, target = _safe_temp_paths(temporary_root_value, target_value)
    owned_root = target / "gkd"
    if owned_root.exists() or owned_root.is_symlink():
        try:
            verified = _verify_target(target)
        except BundleError:
            raise BundleError("TARGET_NOT_CLEAN") from None
        if (
            verified["bundleVersion"] != manifest["bundleVersion"]
            or verified["contentDigest"] != lock["contentDigest"]
        ):
            raise BundleError("TARGET_NOT_CLEAN")
        return {
            "status": "already_installed",
            "bundleVersion": verified["bundleVersion"],
            "contentDigest": verified["contentDigest"],
            "files": len(verified["files"]),
        }

    stage = Path(tempfile.mkdtemp(prefix="gkd-stage-", dir=temporary_root))
    try:
        for item in lock["installFiles"]:
            destination = stage / item["target"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_root / item["source"], destination, follow_symlinks=False)
            os.chmod(destination, int(item["mode"], 8))
        _atomic_write(stage / SCHEMA_TARGET, (source_root / "manifest.schema.json").read_bytes())
        _atomic_write(stage / MANIFEST_TARGET, canonical_bytes(manifest))
        _atomic_write(stage / LOCK_TARGET, canonical_bytes(lock))
        _atomic_write(stage / INSTALL_TARGET, canonical_bytes(_install_record(manifest, lock)))
        verified = _verify_target(stage)
        os.replace(stage / "gkd", owned_root)
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    return {
        "status": "installed",
        "bundleVersion": verified["bundleVersion"],
        "contentDigest": verified["contentDigest"],
        "files": len(verified["files"]),
    }


def verify(temporary_root_value: Path, target_value: Path) -> dict[str, Any]:
    _, target = _safe_temp_paths(temporary_root_value, target_value)
    return _verify_target(target)


def version(temporary_root_value: Path, target_value: Path) -> dict[str, Any]:
    result = verify(temporary_root_value, target_value)
    return {
        "status": "verified",
        "bundleVersion": result["bundleVersion"],
        "contentDigest": result["contentDigest"],
        "files": len(result["files"]),
    }


def _validate_vision(vision: str) -> None:
    headings = re.findall(r"^## (.+)$", vision, flags=re.MULTILINE)
    if tuple(headings) != VISION_HEADINGS:
        raise BundleError("VISION_SECTIONS_INVALID")
    forbidden = (
        r"GKD-[0-9]{3}",
        r"\b(?:GPT|reasoning|xhigh|runtime|runner|schema)\b",
        r"\b[0-9]+\.[0-9]+\.[0-9]+\b",
        r"\b[0-9a-f]{40}\b",
        r"\b(?:P|PRINCIPLE)[-_]?[0-9]+\b",
        r"docs/(?:decisions|adr)",
    )
    if any(re.search(pattern, vision, flags=re.IGNORECASE) for pattern in forbidden):
        raise BundleError("VISION_CONTAINS_VOLATILE_DETAIL")
    if _forbidden_content(vision.encode("utf-8")):
        raise BundleError("VISION_CONTAINS_MACHINE_DETAIL")


def validate_repo(repo_root_value: Path) -> dict[str, Any]:
    repo_root = _existing_directory(repo_root_value, "INVALID_REPOSITORY_ROOT")
    required = {
        "VISION.md",
        "README.md",
        "AGENTS.md",
        "docs/governance.md",
        "docs/decisions/README.md",
        "docs/decisions/template.md",
        "docs/adr/README.md",
        "docs/adr/template.md",
        "docs/vision-alignment-template.md",
    }
    if any(not (repo_root / value).is_file() for value in required):
        raise BundleError("GOVERNANCE_DOCUMENT_MISSING")
    vision = (repo_root / "VISION.md").read_text(encoding="utf-8")
    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    agents = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    _validate_vision(vision)
    if "[VISION](VISION.md)" not in readme or "VISION.md" not in agents:
        raise BundleError("VISION_LINK_MISSING")
    vision_sections = {f"## {heading}" for heading in VISION_HEADINGS}
    if any(section in readme or section in agents for section in vision_sections):
        raise BundleError("VISION_TEXT_DUPLICATED")
    alignment = (repo_root / "docs/vision-alignment-template.md").read_text(encoding="utf-8")
    if alignment != ALIGNMENT_TEMPLATE:
        raise BundleError("ALIGNMENT_TEMPLATE_DRIFT")
    governance = (repo_root / "docs/governance.md").read_text(encoding="utf-8")
    required_terms = ("VISION", "decision", "ADR", "AGENTS", "Skill/reference", "repo policy")
    if any(term not in governance for term in required_terms):
        raise BundleError("GOVERNANCE_LAYERING_INCOMPLETE")
    for template in ("docs/decisions/template.md", "docs/adr/template.md"):
        text = (repo_root / template).read_text(encoding="utf-8")
        if not all(heading in text for heading in ("## Status", "## Context", "## Decision", "## Consequences")):
            raise BundleError("DECISION_TEMPLATE_INCOMPLETE")
    return {"status": "valid", "visionSections": len(VISION_HEADINGS)}


def write_alignment(output: Path) -> dict[str, Any]:
    _atomic_write(output, ALIGNMENT_TEMPLATE.encode("utf-8"))
    return {"status": "generated", "template": "vision-alignment"}


def _snapshot_protected(root_value: Path) -> dict[str, Any]:
    root = _existing_directory(root_value, "INVALID_PROTECTED_ROOT")
    records = []
    for surface in PROTECTED_SURFACES:
        path = root / surface
        if not path.exists() and not path.is_symlink():
            records.append({"surface": surface, "type": "missing"})
            continue
        candidates = [path]
        if path.is_dir() and not path.is_symlink():
            candidates.extend(sorted(path.rglob("*")))
        for candidate in candidates:
            metadata = candidate.lstat()
            relative = candidate.relative_to(root).as_posix()
            mode = format(stat.S_IMODE(metadata.st_mode), "04o")
            if stat.S_ISREG(metadata.st_mode):
                records.append(
                    {
                        "path": relative,
                        "type": "file",
                        "mode": mode,
                        "sha256": sha256_bytes(candidate.read_bytes()),
                    }
                )
            elif stat.S_ISDIR(metadata.st_mode):
                records.append({"path": relative, "type": "directory", "mode": mode})
            elif stat.S_ISLNK(metadata.st_mode):
                records.append(
                    {
                        "path": relative,
                        "type": "symlink",
                        "mode": mode,
                        "targetSha256": sha256_bytes(os.readlink(candidate).encode("utf-8")),
                    }
                )
            else:
                records.append({"path": relative, "type": "other", "mode": mode})
    records.sort(key=lambda item: (item.get("path", item.get("surface", "")), item["type"]))
    return {
        "digest": sha256_bytes(b"".join(canonical_bytes(item) for item in records)),
        "entries": len(records),
    }


def _paths_overlap(first: Path, second: Path) -> bool:
    return _is_within(first, second) or _is_within(second, first)


def _resolve_evidence_output(output: Path) -> Path:
    if output.is_symlink() or output.is_dir():
        raise BundleError("INVALID_EVIDENCE_OUTPUT")
    parent = _existing_directory(output.parent, "INVALID_EVIDENCE_OUTPUT")
    return parent / output.name


def _validate_evidence_boundaries(
    source_root: Path,
    temporary_root: Path,
    protected_root: Path,
    output: Path,
) -> None:
    roots = (source_root, temporary_root, protected_root)
    if any(
        _paths_overlap(first, second)
        for index, first in enumerate(roots)
        for second in roots[index + 1 :]
    ):
        raise BundleError("EVIDENCE_BOUNDARY_OVERLAP")
    if any(_paths_overlap(output, root) for root in roots):
        raise BundleError("EVIDENCE_OUTPUT_OVERLAP")


def _cleanup_evidence_targets(*targets: Path) -> None:
    for target in targets:
        try:
            if target.exists() or target.is_symlink():
                shutil.rmtree(target)
        except OSError:
            raise BundleError("EVIDENCE_CLEANUP_FAILED") from None
        if target.exists() or target.is_symlink():
            raise BundleError("EVIDENCE_CLEANUP_FAILED")


def generate_evidence(
    source_root_value: Path,
    temporary_root_value: Path,
    protected_root_value: Path,
    output: Path,
) -> dict[str, Any]:
    source_root, manifest, lock = _validated_source(source_root_value)
    temporary_root = _existing_directory(temporary_root_value, "INVALID_TEMPORARY_ROOT")
    protected_root = _existing_directory(protected_root_value, "INVALID_PROTECTED_ROOT")
    resolved_output = _resolve_evidence_output(output)
    _validate_evidence_boundaries(
        source_root, temporary_root, protected_root, resolved_output
    )
    _validate_project_contamination(source_root)
    system_temporary = Path(tempfile.gettempdir()).resolve()
    if temporary_root == system_temporary or not _is_within(temporary_root, system_temporary):
        raise BundleError("INVALID_TEMPORARY_ROOT")
    if any(temporary_root.iterdir()):
        raise BundleError("TEMPORARY_ROOT_NOT_CLEAN")
    before = _snapshot_protected(protected_root)
    first = temporary_root / "install-a"
    second = temporary_root / "install-b"
    try:
        first.mkdir()
        second.mkdir()
        first_install = install(source_root, temporary_root, first)
        repeated_install = install(source_root, temporary_root, first)
        second_install = install(source_root, temporary_root, second)
        first_verified = verify(temporary_root, first)
        second_verified = verify(temporary_root, second)
        first_version = version(temporary_root, first)
        second_version = version(temporary_root, second)
        validate_repo(source_root.parent)
        if first_verified != second_verified or first_version != second_version:
            raise BundleError("INSTALLATIONS_DIFFER")
        if repeated_install["status"] != "already_installed":
            raise BundleError("INSTALL_NOT_IDEMPOTENT")
    finally:
        _cleanup_evidence_targets(first, second)

    if any(temporary_root.iterdir()):
        raise BundleError("EVIDENCE_CLEANUP_FAILED")
    after = _snapshot_protected(protected_root)
    if before != after:
        raise BundleError("PROTECTED_HOME_CHANGED")
    evidence = {
        "schemaVersion": SCHEMA_VERSION,
        "task": "GKD-M0-A",
        "outcome": "canonical_foundation_ready",
        "bundleVersion": manifest["bundleVersion"],
        "contentDigest": lock["contentDigest"],
        "manifestSha256": lock["manifestSha256"],
        "installations": {
            "first": first_install,
            "second": second_install,
            "normalizedInstalledFiles": first_verified["files"],
            "versionsMatch": True,
            "idempotent": True,
        },
        "protectedHome": {
            "beforeDigest": before["digest"],
            "afterDigest": after["digest"],
            "entries": before["entries"],
            "unchanged": True,
        },
        "contracts": {
            "sourceManifestAndLockValidated": "pass",
            "temporaryBoundaryEnforced": "pass",
            "twoCleanInstallsMatch": "pass",
            "repeatInstallIdempotent": "pass",
            "installedVerifyAndVersion": "pass",
            "cleanupBeforeFinalSnapshot": "pass",
            "evidenceOutputDisjoint": "pass",
            "visionAndDocumentationLayering": "pass",
        },
    }
    encoded_evidence = canonical_bytes(evidence)
    if _forbidden_content(encoded_evidence) or _contains_project_marker(encoded_evidence):
        raise BundleError("EVIDENCE_CONTAINS_MACHINE_DETAIL")
    evidence["evidenceDigest"] = sha256_bytes(encoded_evidence)
    _atomic_write(resolved_output, canonical_bytes(evidence))
    return {
        "status": "generated",
        "outcome": evidence["outcome"],
        "bundleVersion": evidence["bundleVersion"],
        "contentDigest": evidence["contentDigest"],
        "evidenceDigest": evidence["evidenceDigest"],
    }


def _parser() -> MachineParser:
    parser = MachineParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True, parser_class=MachineParser)

    generate_parser = commands.add_parser("generate")
    generate_parser.add_argument("--source-root", type=Path, required=True)

    install_parser = commands.add_parser("install")
    install_parser.add_argument("--source-root", type=Path, required=True)
    install_parser.add_argument("--temporary-root", type=Path, required=True)
    install_parser.add_argument("--target", type=Path, required=True)

    input_parser = commands.add_parser("verify-input")
    input_parser.add_argument("--source-root", type=Path, required=True)
    input_parser.add_argument("--name", required=True)

    for name in ("verify", "version"):
        command = commands.add_parser(name)
        command.add_argument("--temporary-root", type=Path, required=True)
        command.add_argument("--target", type=Path, required=True)

    validate_parser = commands.add_parser("validate-repo")
    validate_parser.add_argument("--repo-root", type=Path, required=True)

    alignment_parser = commands.add_parser("alignment")
    alignment_parser.add_argument("--output", type=Path, required=True)

    evidence_parser = commands.add_parser("evidence")
    evidence_parser.add_argument("--source-root", type=Path, required=True)
    evidence_parser.add_argument("--temporary-root", type=Path, required=True)
    evidence_parser.add_argument("--protected-root", type=Path, required=True)
    evidence_parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        if args.command == "generate":
            result = generate(args.source_root)
        elif args.command == "install":
            result = install(args.source_root, args.temporary_root, args.target)
        elif args.command == "verify-input":
            result = verify_input(args.source_root, args.name)
        elif args.command == "verify":
            result = verify(args.temporary_root, args.target)
        elif args.command == "version":
            result = version(args.temporary_root, args.target)
        elif args.command == "validate-repo":
            result = validate_repo(args.repo_root)
        elif args.command == "alignment":
            result = write_alignment(args.output)
        elif args.command == "evidence":
            result = generate_evidence(
                args.source_root, args.temporary_root, args.protected_root, args.output
            )
        else:
            raise BundleError("INVALID_ARGUMENTS")
    except BundleError as error:
        print(canonical_bytes({"status": "error", "error": error.code}).decode("utf-8"), end="", file=sys.stderr)
        return 2
    except (OSError, UnicodeDecodeError):
        print(canonical_bytes({"status": "error", "error": "FILESYSTEM_ERROR"}).decode("utf-8"), end="", file=sys.stderr)
        return 2
    except (ValueError, TypeError, KeyError, OverflowError):
        print(canonical_bytes({"status": "error", "error": "INTERNAL_ERROR"}).decode("utf-8"), end="", file=sys.stderr)
        return 2
    print(canonical_bytes(result).decode("utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
