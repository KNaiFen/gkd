from __future__ import annotations

import json
from pathlib import Path


BUNDLE_ROOT = Path("canonical/payload")
SOURCE_ROOT = Path("canonical")
DUPLICATES = (
    "code-review-and-quality",
    "code-simplification",
    "context-budget",
    "documentation-and-adrs",
    "repomix-explorer",
    "security-and-hardening",
)


def bundle_digest() -> str:
    return json.loads((SOURCE_ROOT / "manifest.lock.json").read_text(encoding="utf-8"))["contentDigest"]


def build_migration_home(home: Path) -> None:
    codex = home / ".codex"
    agents = codex / "agents"
    skills = codex / "skills"
    duplicate_root = home / ".agents" / "skills"
    agents.mkdir(parents=True)
    skills.mkdir()
    duplicate_root.mkdir(parents=True)
    (codex / "config.toml").write_text('model = "gpt-5.6-sol"\n', encoding="utf-8")
    (codex / "AGENTS.md").write_text("# Rules\n\n- Preserve every approved hard rule.\n", encoding="utf-8")
    (agents / "ci-reviewer.toml").write_text('name = "ci_reviewer"\n', encoding="utf-8")
    unrelated = skills / "unrelated-skill"
    unrelated.mkdir()
    (unrelated / "SKILL.md").write_text("---\nname: unrelated-skill\ndescription: unrelated\n---\n", encoding="utf-8")
    for name in DUPLICATES:
        for root in (skills, duplicate_root):
            target = root / name
            target.mkdir()
            text = f"---\nname: {name}\ndescription: broad legacy trigger\n---\n\n# {name}\n"
            if name == "security-and-hardening":
                text += "\n## See Also\n\nFor detailed security checklists and pre-commit verification steps, see `references/security-checklist.md`.\n"
            (target / "SKILL.md").write_text(text, encoding="utf-8")


def duplicate_bytes(home: Path) -> dict[str, bytes]:
    return {name: (home / ".agents" / "skills" / name / "SKILL.md").read_bytes() for name in DUPLICATES}
