"""Strict parsing for the reviewed planning package."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from .canonical import canonical_bytes, sha256_bytes
from .errors import TaskError


REQUIREMENTS_SECTIONS = (
    "Goal",
    "User Decisions",
    "Scope",
    "Non-Goals",
    "Acceptance Criteria",
)
PLAN_MATERIAL_SECTIONS = (
    "Goal",
    "User Decisions",
    "Behavior And Defaults",
    "Scope",
    "Non-Goals",
    "Acceptance Criteria",
    "Compatibility",
    "Security And Data",
    "Migration",
    "Public Interfaces",
    "Execution Route",
    "External Side Effects",
    "Action Mode",
)
PLAN_SECTIONS = PLAN_MATERIAL_SECTIONS + ("Implementation Notes",)
IMPLEMENTATION_SECTIONS = ("Internal Design", "Execution Details")
DOCUMENT_NAMES = ("requirements.md", "plan.md", "implementation.md")


def _read_document(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise TaskError("INVALID_PLANNING_DOCUMENT")
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        raise TaskError("INVALID_PLANNING_DOCUMENT") from None
    if len(raw) > 1024 * 1024 or b"\x00" in raw or "\r" in text or not text.endswith("\n"):
        raise TaskError("INVALID_PLANNING_DOCUMENT")
    return raw


def _document_for_sections(expected: tuple[str, ...]) -> str | None:
    if expected == REQUIREMENTS_SECTIONS:
        return "requirements"
    if expected == PLAN_SECTIONS:
        return "plan"
    if expected == IMPLEMENTATION_SECTIONS:
        return "implementation"
    return None


def parse_sections(
    raw: bytes,
    expected: tuple[str, ...],
    document: str | None = None,
) -> dict[str, str]:
    # P4 documents may carry a trusted, canonical machine-facts block after
    # their human sections.  Legacy documents without the block keep the exact
    # historical parser behavior.
    try:
        from gkd_main.facts import strip_facts_block

        raw = strip_facts_block(raw, document or _document_for_sections(expected))
    except TaskError:
        raise
    except (ImportError, UnicodeDecodeError):
        raise TaskError("INVALID_PLANNING_DOCUMENT") from None
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise TaskError("INVALID_PLANNING_DOCUMENT") from None
    lines = text.splitlines()
    if not lines or not re.fullmatch(r"# .+", lines[0]):
        raise TaskError("INVALID_PLANNING_DOCUMENT")
    headings = [(index, line[3:]) for index, line in enumerate(lines) if line.startswith("## ")]
    if tuple(value for _, value in headings) != expected:
        raise TaskError("INVALID_PLANNING_DOCUMENT")
    sections: dict[str, str] = {}
    for position, (line_index, heading) in enumerate(headings):
        end = headings[position + 1][0] if position + 1 < len(headings) else len(lines)
        body = "\n".join(lines[line_index + 1 : end]).strip()
        if not body:
            raise TaskError("INVALID_PLANNING_DOCUMENT")
        sections[heading] = body
    return sections


def parse_document_facts(raw: bytes, document: str) -> dict[str, Any] | None:
    """Read the optional P4 machine-facts block without changing legacy reads."""

    if document not in {"requirements", "plan", "implementation", "delivery", "acceptance"}:
        raise TaskError("INVALID_DOCUMENT_KIND")
    try:
        from gkd_main.facts import parse_facts_block

        value = parse_facts_block(raw, document)
    except (UnicodeDecodeError, TaskError):
        raise TaskError("INVALID_DOCUMENT_FACTS") from None
    return value


def render_document_facts(raw: bytes, document: str) -> dict[str, Any] | None:
    """Alias used by high-level consumers while retaining a small API surface."""

    return parse_document_facts(raw, document)


def inspect_package(root: Path) -> tuple[dict[str, Any], dict[str, bytes]]:
    if root.is_symlink() or not root.is_dir():
        raise TaskError("INVALID_PLANNING_PACKAGE")
    raw = {name: _read_document(root / name) for name in DOCUMENT_NAMES}
    parse_sections(raw["requirements.md"], REQUIREMENTS_SECTIONS, "requirements")
    plan_sections = parse_sections(raw["plan.md"], PLAN_SECTIONS, "plan")
    parse_sections(raw["implementation.md"], IMPLEMENTATION_SECTIONS, "implementation")
    material = {name: plan_sections[name] for name in PLAN_MATERIAL_SECTIONS}
    records = {
        "requirements": {
            "path": "requirements.md",
            "version": 1,
            "documentRevision": 1,
            "digest": sha256_bytes(raw["requirements.md"]),
            "status": "draft",
        },
        "plan": {
            "path": "plan.md",
            "version": 1,
            "documentRevision": 1,
            "digest": sha256_bytes(raw["plan.md"]),
            "materialDigest": sha256_bytes(canonical_bytes(material)),
            "status": "proposed",
        },
        "implementation": {
            "path": "implementation.md",
            "version": 1,
            "documentRevision": 1,
            "digest": sha256_bytes(raw["implementation.md"]),
        },
    }
    return records, raw


def inspect_tracked_package(task_root: Path) -> dict[str, Any]:
    records, _ = inspect_package(task_root)
    return records


def inspect_plan(raw: bytes) -> tuple[str, str]:
    sections = parse_sections(raw, PLAN_SECTIONS)
    material = {name: sections[name] for name in PLAN_MATERIAL_SECTIONS}
    return sha256_bytes(raw), sha256_bytes(canonical_bytes(material))
