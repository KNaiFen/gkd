from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tests.foundation.helpers import copy_governance_repo, gkd_bundle


class GovernanceContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repo = copy_governance_repo(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_vision_has_exactly_seven_required_sections(self) -> None:
        result = gkd_bundle.validate_repo(self.repo)
        self.assertEqual(result, {"status": "valid", "visionSections": 7})

    def test_mutation_missing_vision_section_is_rejected(self) -> None:
        path = self.repo / "VISION.md"
        path.write_text(path.read_text(encoding="utf-8").replace("## 演进规则", "## 变更"), encoding="utf-8")
        with self.assertRaisesRegex(gkd_bundle.BundleError, "VISION_SECTIONS_INVALID"):
            gkd_bundle.validate_repo(self.repo)

    def test_duplicate_vision_section_is_rejected(self) -> None:
        path = self.repo / "VISION.md"
        path.write_text(path.read_text(encoding="utf-8") + "\n## 使命\n\n重复。\n", encoding="utf-8")
        with self.assertRaisesRegex(gkd_bundle.BundleError, "VISION_SECTIONS_INVALID"):
            gkd_bundle.validate_repo(self.repo)

    def test_decision_index_and_machine_principle_id_are_rejected(self) -> None:
        path = self.repo / "VISION.md"
        original = path.read_text(encoding="utf-8")
        for mutation in ("\nGKD-001\n", "\nPRINCIPLE-1\n"):
            with self.subTest(mutation=mutation.strip()):
                path.write_text(original + mutation, encoding="utf-8")
                with self.assertRaisesRegex(gkd_bundle.BundleError, "VISION_CONTAINS_VOLATILE_DETAIL"):
                    gkd_bundle.validate_repo(self.repo)
        path.write_text(original, encoding="utf-8")

    def test_model_runtime_runner_and_schema_constants_are_rejected(self) -> None:
        path = self.repo / "VISION.md"
        original = path.read_text(encoding="utf-8")
        for mutation in ("\nGPT-next\n", "\nruntime\n", "\nrunner\n", "\nschema\n"):
            with self.subTest(mutation=mutation.strip()):
                path.write_text(original + mutation, encoding="utf-8")
                with self.assertRaisesRegex(gkd_bundle.BundleError, "VISION_CONTAINS_VOLATILE_DETAIL"):
                    gkd_bundle.validate_repo(self.repo)
        path.write_text(original, encoding="utf-8")

    def test_readme_and_agents_must_link_without_copying_vision(self) -> None:
        readme = self.repo / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8").replace("[VISION](VISION.md)", "VISION"), encoding="utf-8")
        with self.assertRaisesRegex(gkd_bundle.BundleError, "VISION_LINK_MISSING"):
            gkd_bundle.validate_repo(self.repo)
        readme.write_text("# GKD\n\n[VISION](VISION.md)\n\n## 使命\n", encoding="utf-8")
        with self.assertRaisesRegex(gkd_bundle.BundleError, "VISION_TEXT_DUPLICATED"):
            gkd_bundle.validate_repo(self.repo)

    def test_document_layering_and_templates_are_complete(self) -> None:
        governance = (self.repo / "docs/governance.md").read_text(encoding="utf-8")
        for term in ("VISION", "decision", "ADR", "AGENTS", "Skill/reference", "repo policy"):
            self.assertIn(term, governance)
        self.assertIn("不是完整 decision/ADR 历史", governance)
        for template in ("docs/decisions/template.md", "docs/adr/template.md"):
            content = (self.repo / template).read_text(encoding="utf-8")
            for heading in ("## Status", "## Context", "## Decision", "## Consequences"):
                self.assertIn(heading, content)

    def test_alignment_template_is_generated_and_cannot_expand_authorization(self) -> None:
        destination = self.root / "alignment.md"
        gkd_bundle.write_alignment(destination)
        content = destination.read_text(encoding="utf-8")
        self.assertEqual(content, (self.repo / "docs/vision-alignment-template.md").read_text(encoding="utf-8"))
        for heading in (
            "## 可读原则名称",
            "## 支持方式",
            "## 张力或偏离",
            "## 是否改变当前材料性承诺",
            "## 方案内 decision/ADR 引用（仅在需要时）",
        ):
            self.assertIn(heading, content)
        self.assertIn("愿景一致性不构成授权", content)
        self.assertIn("executor 与 acceptor 不得", content)


if __name__ == "__main__":
    unittest.main()
