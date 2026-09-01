from __future__ import annotations

import json
from pathlib import Path
import unittest

from gkd_main.facts import (
    parse_facts_block,
    render_facts_block,
    render_machine_facts,
    validate_machine_facts,
)
from gkd_task.canonical import canonical_bytes
from gkd_task.documents import parse_sections
from gkd_task.errors import TaskError
from tests.task_core.helpers import TaskRepo


class DocumentFactsContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TaskRepo()

    def tearDown(self) -> None:
        self.repo.close()

    def test_renderer_is_byte_deterministic(self) -> None:
        state = self.repo.state()
        first = render_machine_facts("requirements", state)
        second = render_machine_facts("requirements", state)
        self.assertEqual(canonical_bytes(first), canonical_bytes(second))
        self.assertEqual(first["factsDigest"], second["factsDigest"])

    def test_renderer_rejects_path_and_capability_facts(self) -> None:
        facts = render_machine_facts("requirements", self.repo.state())
        facts["task"]["candidateRoot"] = "/private/tmp/fixture"
        facts["factsDigest"] = __import__("gkd_task.canonical", fromlist=["digest_object"]).digest_object(
            {key: value for key, value in facts.items() if key != "factsDigest"}
        )
        with self.assertRaisesRegex(TaskError, "INVALID_DOCUMENT_FACTS"):
            validate_machine_facts(facts)

    def test_markdown_facts_block_round_trips_and_human_text_is_ignored(self) -> None:
        facts = render_machine_facts("plan", self.repo.state(), requirements_digest="a" * 64)
        block = render_facts_block(facts)
        parsed = parse_facts_block(("# Human note\n\nChanged narrative.\n\n" + block).encode("utf-8"))
        self.assertEqual(facts, parsed)
        sections = parse_sections(
            ("# Fixture\n\n## Goal\n\nKeep the intent.\n\n" + block).encode("utf-8"),
            ("Goal",),
        )
        self.assertEqual("Keep the intent.", sections["Goal"])

    def test_legacy_document_without_facts_remains_readable(self) -> None:
        raw = b"# Legacy\n\n## Goal\n\nExisting text.\n"
        self.assertEqual({"Goal": "Existing text."}, parse_sections(raw, ("Goal",)))

    def test_tampered_facts_digest_fails_closed(self) -> None:
        facts = render_machine_facts("requirements", self.repo.state())
        facts["task"]["phase"] = "delivered"
        with self.assertRaisesRegex(TaskError, "DOCUMENT_FACTS_TAMPERED"):
            validate_machine_facts(facts)


if __name__ == "__main__":
    unittest.main()
