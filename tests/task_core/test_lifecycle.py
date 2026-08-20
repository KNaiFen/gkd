from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

from gkd_task.canonical import canonical_bytes
from gkd_task.errors import TaskError
from gkd_task.runtime import RuntimeStore
from tests.task_core.helpers import CONFIG_DIGEST, FUTURE_TIME, ROLE_DIGEST, TaskRepo, run


class LifecycleContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TaskRepo()

    def tearDown(self) -> None:
        self.repo.close()

    def test_offer_requires_separate_implementation_authorization(self) -> None:
        service = self.repo.service()
        service.requirements_ready(*self.repo.cas())
        service.approve_plan(*self.repo.cas(), "plan-only")
        with self.assertRaisesRegex(TaskError, "IMPLEMENTATION_NOT_AUTHORIZED"):
            service.offer(*self.repo.cas(), "manual", ROLE_DIGEST, CONFIG_DIGEST, FUTURE_TIME)

    def test_offer_binds_all_planning_authorization_and_role_facts(self) -> None:
        service = self.repo.ready_and_authorized()
        service.offer(*self.repo.cas(), "manual", ROLE_DIGEST, CONFIG_DIGEST, FUTURE_TIME)
        offer = json.loads((self.repo.task_root / "offer.json").read_text(encoding="utf-8"))
        state = self.repo.state()
        authorization = json.loads((self.repo.task_root / "authorization.json").read_text(encoding="utf-8"))
        self.assertEqual(state["taskId"], offer["taskId"])
        self.assertEqual(state["repository"]["identity"], offer["repository"])
        self.assertEqual(state["documents"]["plan"]["materialDigest"], offer["planMaterialDigest"])
        self.assertEqual(authorization["authorizationDigest"], offer["authorizationDigest"])
        self.assertEqual(authorization["allowedActions"], offer["allowedActions"])
        self.assertEqual(ROLE_DIGEST, offer["roleDigest"])
        self.assertEqual(CONFIG_DIGEST, offer["configDigest"])

    def test_offer_commits_only_capability_digest(self) -> None:
        service = self.repo.ready_and_authorized()
        service.offer(*self.repo.cas(), "manual", ROLE_DIGEST, CONFIG_DIGEST, FUTURE_TIME)
        offer_id = json.loads((self.repo.task_root / "offer.json").read_text(encoding="utf-8"))["offerId"]
        capability = RuntimeStore(self.repo.runtime_root).read_capability(offer_id)
        tracked = subprocess.run(
            ["git", "-C", str(self.repo.candidate), "grep", "-n", capability["capability"], "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
        self.assertEqual(1, tracked.returncode)
        self.assertEqual("", tracked.stdout)
        offer = (self.repo.task_root / "offer.json").read_text(encoding="utf-8")
        self.assertNotIn(capability["capability"], offer)
        self.assertIn(capability["capabilityDigest"], offer)

    def test_capability_write_failure_leaves_offer_retryable_without_commit(self) -> None:
        service = self.repo.ready_and_authorized()
        before_head, before_revision = self.repo.cas()
        before_commits = self.repo.commits()
        with mock.patch.object(service.runtime, "write_capability", side_effect=TaskError("CAPABILITY_UNAVAILABLE")):
            with self.assertRaisesRegex(TaskError, "CAPABILITY_UNAVAILABLE"):
                service.offer(*self.repo.cas(), "manual", ROLE_DIGEST, CONFIG_DIGEST, FUTURE_TIME)
        self.assertEqual((before_head, before_revision), self.repo.cas())
        self.assertEqual(before_commits, self.repo.commits())
        self.assertEqual("planning", self.repo.state()["lifecycle"]["phase"])
        result = service.offer(*self.repo.cas(), "manual", ROLE_DIGEST, CONFIG_DIGEST, FUTURE_TIME)
        self.assertEqual("awaiting_claim", result["status"])

    def test_offer_commit_interruption_recovers_with_capability_intact(self) -> None:
        self.repo.ready_and_authorized()

        def committed_failure(phase: str) -> None:
            if phase == "committed":
                raise RuntimeError("injected-offer-commit")

        service = self.repo.service(failure_hook=committed_failure)
        with self.assertRaisesRegex(RuntimeError, "injected-offer-commit"):
            service.offer(*self.repo.cas(), "manual", ROLE_DIGEST, CONFIG_DIGEST, FUTURE_TIME)
        self.assertEqual("recovered_committed", service.recover()["status"])
        self.assertEqual("awaiting_claim", self.repo.state()["lifecycle"]["phase"])
        self.assertEqual("handoff_ready", self.repo.service().handoff()["status"])

    def test_handoff_changes_no_tracked_byte_or_head(self) -> None:
        service = self.repo.ready_and_authorized()
        service.offer(*self.repo.cas(), "manual", ROLE_DIGEST, CONFIG_DIGEST, FUTURE_TIME)
        before_head = self.repo.head()
        before_tree = subprocess.check_output(["git", "-C", str(self.repo.candidate), "write-tree"], text=True).strip()
        result = service.handoff()
        after_tree = subprocess.check_output(["git", "-C", str(self.repo.candidate), "write-tree"], text=True).strip()
        self.assertEqual(before_head, self.repo.head())
        self.assertEqual(before_tree, after_tree)
        self.assertEqual({"status", "offerId", "envelopeId"}, set(result))

    def test_claim_cleans_every_envelope_for_consumed_offer(self) -> None:
        service = self.repo.ready_and_authorized()
        service.offer(*self.repo.cas(), "manual", ROLE_DIGEST, CONFIG_DIGEST, FUTURE_TIME)
        first = service.handoff()["envelopeId"]
        second = service.handoff()["envelopeId"]
        self.assertNotEqual(first, second)
        service.claim(*self.repo.cas(), first)
        envelope_root = self.repo.runtime_root / "envelopes"
        self.assertEqual([], list(envelope_root.iterdir()))

    def test_expired_offer_is_rejected(self) -> None:
        service = self.repo.ready_and_authorized()
        with self.assertRaisesRegex(TaskError, "OFFER_EXPIRED"):
            service.offer(*self.repo.cas(), "manual", ROLE_DIGEST, CONFIG_DIGEST, "2025-01-01T00:00:00Z")

    def test_wrong_capability_is_rejected_without_claim_commit(self) -> None:
        service = self.repo.ready_and_authorized()
        service.offer(*self.repo.cas(), "manual", ROLE_DIGEST, CONFIG_DIGEST, FUTURE_TIME)
        handoff = service.handoff()
        path = RuntimeStore(self.repo.runtime_root)._path("envelopes", handoff["envelopeId"])
        envelope = json.loads(path.read_text(encoding="utf-8"))
        envelope["capability"] = "x" * 64
        unsigned = dict(envelope)
        unsigned.pop("envelopeDigest")
        from gkd_task.canonical import digest_object

        envelope["envelopeDigest"] = digest_object(unsigned)
        path.write_bytes(canonical_bytes(envelope))
        commits = self.repo.commits()
        with self.assertRaisesRegex(TaskError, "CAPABILITY_MISMATCH"):
            service.claim(*self.repo.cas(), handoff["envelopeId"])
        self.assertEqual(commits, self.repo.commits())

    def test_wrong_runtime_role_config_or_route_is_rejected(self) -> None:
        service = self.repo.ready_and_authorized()
        service.offer(*self.repo.cas(), "manual", ROLE_DIGEST, CONFIG_DIGEST, FUTURE_TIME)
        handoff = service.handoff()
        mismatched = self.repo.service()
        mismatched.evidence_provider.evidence["route"] = "automatic"
        unsigned = dict(mismatched.evidence_provider.evidence)
        unsigned.pop("evidenceDigest")
        from gkd_task.canonical import digest_object

        mismatched.evidence_provider.evidence["evidenceDigest"] = digest_object(unsigned)
        with self.assertRaisesRegex(TaskError, "RUNTIME_EVIDENCE_MISMATCH"):
            mismatched.claim(*self.repo.cas(), handoff["envelopeId"])

    def test_claim_consumes_offer_and_capability_once(self) -> None:
        service = self.repo.ready_and_authorized()
        service.offer(*self.repo.cas(), "manual", ROLE_DIGEST, CONFIG_DIGEST, FUTURE_TIME)
        handoff = service.handoff()
        result = service.claim(*self.repo.cas(), handoff["envelopeId"])
        self.assertEqual("implementing", result["status"])
        offer = json.loads((self.repo.task_root / "offer.json").read_text(encoding="utf-8"))
        self.assertEqual("consumed", offer["status"])
        with self.assertRaisesRegex(TaskError, "INVALID_LAUNCH_ENVELOPE|OFFER_CONFLICT"):
            service.claim(*self.repo.cas(), handoff["envelopeId"])

    def test_claim_receipt_write_failure_repairs_from_committed_journal(self) -> None:
        service = self.repo.ready_and_authorized()
        service.offer(*self.repo.cas(), "manual", ROLE_DIGEST, CONFIG_DIGEST, FUTURE_TIME)
        handoff = service.handoff()
        with mock.patch.object(service.runtime, "write_claim_receipt", side_effect=TaskError("CLAIM_RECEIPT_WRITE_FAILED")):
            with self.assertRaisesRegex(TaskError, "CLAIM_RECEIPT_WRITE_FAILED"):
                service.claim(*self.repo.cas(), handoff["envelopeId"])
        state = self.repo.state()
        self.assertEqual("implementing", state["lifecycle"]["phase"])
        claim_id = state["lifecycle"]["claim"]["claimId"]
        result = self.repo.deliver(service, claim_id)
        self.assertEqual("delivered", result["status"])
        receipt = RuntimeStore(self.repo.runtime_root).read_claim_receipt(claim_id)
        self.assertEqual(claim_id, receipt["claimId"])

    def test_late_executor_with_stale_envelope_remains_rejected(self) -> None:
        service = self.repo.ready_and_authorized()
        service.offer(*self.repo.cas(), "manual", ROLE_DIGEST, CONFIG_DIGEST, FUTURE_TIME)
        handoff = service.handoff()
        store = RuntimeStore(self.repo.runtime_root)
        stale = store.read_envelope(handoff["envelopeId"])
        service.claim(*self.repo.cas(), handoff["envelopeId"])
        store.write_envelope(handoff["envelopeId"], stale)
        with self.assertRaisesRegex(TaskError, "OFFER_CONFLICT|CAPABILITY_MISMATCH"):
            service.claim(*self.repo.cas(), handoff["envelopeId"])

    def test_concurrent_subprocess_claim_has_exactly_one_winner(self) -> None:
        service = self.repo.ready_and_authorized()
        service.offer(*self.repo.cas(), "manual", ROLE_DIGEST, CONFIG_DIGEST, FUTURE_TIME)
        envelope = service.handoff()["envelopeId"]
        claim_head, revision = self.repo.cas()
        base_count = self.repo.commits()
        command = [
            sys.executable,
            "-m",
            "tests.task_core.claim_worker",
            "--candidate",
            str(self.repo.candidate),
            "--task-path",
            self.repo.task_path,
            "--runtime",
            str(self.repo.runtime_root),
            "--head",
            claim_head,
            "--revision",
            str(revision),
            "--envelope",
            envelope,
        ]
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONPATH"] = "canonical/payload/lib:."
        first = subprocess.Popen(command + ["--writer", "writer-a"], cwd=Path.cwd(), env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        second = subprocess.Popen(command + ["--writer", "writer-b"], cwd=Path.cwd(), env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        first_output = first.communicate(timeout=15)
        second_output = second.communicate(timeout=15)
        winners = [process for process in (first, second) if process.returncode == 0]
        self.assertEqual(1, len(winners), (first.returncode, second.returncode, first_output, second_output))
        self.assertEqual(base_count + 1, self.repo.commits())
        self.assertEqual("implementing", self.repo.state()["lifecycle"]["phase"])

    def test_revoke_advances_epoch_and_permanently_rejects_old_envelope(self) -> None:
        service = self.repo.ready_and_authorized()
        service.offer(*self.repo.cas(), "manual", ROLE_DIGEST, CONFIG_DIGEST, FUTURE_TIME)
        envelope = service.handoff()["envelopeId"]
        service.revoke(*self.repo.cas(), "authority-revoked")
        state = self.repo.state()
        self.assertEqual(1, state["lifecycle"]["epoch"])
        self.assertEqual("planning", state["lifecycle"]["phase"])
        with self.assertRaisesRegex(TaskError, "INVALID_LAUNCH_ENVELOPE|OFFER_CONFLICT|CAPABILITY"):
            service.claim(*self.repo.cas(), envelope)

    def test_reclaim_requires_terminal_or_missing_writer_evidence(self) -> None:
        service, _ = self.repo.offer_and_claim()
        with self.assertRaisesRegex(TaskError, "WRITER_STILL_ACTIVE"):
            service.reclaim(*self.repo.cas(), "writer-stalled")
        terminal = self.repo.service(evidence_status="terminal")
        terminal.reclaim(*self.repo.cas(), "writer-terminal")
        state = self.repo.state()
        self.assertEqual("planning", state["lifecycle"]["phase"])
        self.assertEqual(1, state["lifecycle"]["epoch"])
        self.assertEqual(1, len(state["lifecycle"]["retiredClaims"]))

    def test_reclaim_rejects_terminal_evidence_for_wrong_bound_writer(self) -> None:
        self.repo.offer_and_claim()
        terminal = self.repo.service(evidence_status="terminal")
        evidence = terminal.evidence_provider.evidence
        evidence["writerId"] = "different-writer"
        unsigned = dict(evidence)
        unsigned.pop("evidenceDigest")
        from gkd_task.canonical import digest_object

        evidence["evidenceDigest"] = digest_object(unsigned)
        with self.assertRaisesRegex(TaskError, "WRITER_STILL_ACTIVE"):
            terminal.reclaim(*self.repo.cas(), "wrong-writer")

    def test_block_and_resume_preserve_underlying_phase(self) -> None:
        service = self.repo.ready_and_authorized()
        service.offer(*self.repo.cas(), "manual", ROLE_DIGEST, CONFIG_DIGEST, FUTURE_TIME)
        service.block(*self.repo.cas(), "waiting", "main")
        self.assertEqual("awaiting_claim", self.repo.state()["lifecycle"]["phase"])
        with self.assertRaisesRegex(TaskError, "TASK_BLOCKED"):
            service.claim(*self.repo.cas(), service.handoff()["envelopeId"])
        service.resume(*self.repo.cas())
        self.assertEqual("awaiting_claim", self.repo.state()["lifecycle"]["phase"])

    def test_delivery_requires_current_claim_and_clean_candidate(self) -> None:
        service, claim_id = self.repo.offer_and_claim()
        with self.assertRaisesRegex(TaskError, "CLAIM_MISMATCH"):
            service.deliver(*self.repo.cas(), "0" * 64)
        document_path, document_digest = self.repo.prepare_delivery_document()
        dirty = self.repo.candidate / "unrelated.txt"
        dirty.write_text("dirty\n", encoding="utf-8")
        with self.assertRaisesRegex(TaskError, "WORKTREE_NOT_CLEAN"):
            service.deliver(*self.repo.cas(), claim_id, None, document_path, document_digest)
        dirty.unlink()
        result = service.deliver(*self.repo.cas(), claim_id, None, document_path, document_digest)
        self.assertEqual("delivered", result["status"])
        self.assertIsNone(self.repo.state()["lifecycle"]["writer"])

    def test_delivery_requires_precommitted_canonical_document_binding(self) -> None:
        service, claim_id = self.repo.offer_and_claim()
        before = self.repo.cas()
        with self.assertRaisesRegex(TaskError, "DELIVERY_DOCUMENT_REQUIRED"):
            service.deliver(*before, claim_id)
        self.assertEqual(before, self.repo.cas())

        document_path, document_digest = self.repo.prepare_delivery_document()
        before = self.repo.cas()
        with self.assertRaisesRegex(TaskError, "DELIVERY_DOCUMENT_MISMATCH"):
            service.deliver(*before, claim_id, None, document_path, "0" * 64)
        self.assertEqual(before, self.repo.cas())

        result = service.deliver(*self.repo.cas(), claim_id, None, document_path, document_digest)
        delivery = self.repo.state()["lifecycle"]["delivery"]
        self.assertEqual("delivered", result["status"])
        self.assertEqual(document_path, delivery["deliveryDocumentPath"])
        self.assertEqual(document_digest, delivery["deliveryDocumentDigest"])
        self.assertEqual(self.repo.head(), result["head"])
        self.assertEqual(
            delivery["implementationHead"],
            run("git", "rev-parse", f"{delivery['deliveryDocumentCommit']}^", cwd=self.repo.candidate),
        )
        self.assertEqual(
            delivery["deliveryDocumentCommit"],
            run("git", "rev-parse", f"{self.repo.head()}^", cwd=self.repo.candidate),
        )

    def test_delivery_rejects_document_commit_with_extra_tracked_path(self) -> None:
        service, claim_id = self.repo.offer_and_claim()
        document_path = self.repo.task_root / "delivery.md"
        document_path.write_text("# Fixture Delivery\n", encoding="utf-8")
        extra = self.repo.candidate / "delivery-extra.txt"
        extra.write_text("unexpected\n", encoding="utf-8")
        relative_document = f"{self.repo.task_path}/delivery.md"
        run("git", "add", relative_document, "delivery-extra.txt", cwd=self.repo.candidate)
        run("git", "commit", "-m", "invalid delivery document commit", cwd=self.repo.candidate)
        before = self.repo.cas()
        with self.assertRaisesRegex(TaskError, "INVALID_DELIVERY_DOCUMENT"):
            service.deliver(
                *before,
                claim_id,
                None,
                relative_document,
                hashlib.sha256(document_path.read_bytes()).hexdigest(),
            )
        self.assertEqual(before, self.repo.cas())
        self.assertEqual("implementing", self.repo.state()["lifecycle"]["phase"])

    def test_delivery_rejects_path_traversal_before_any_write(self) -> None:
        service, claim_id = self.repo.offer_and_claim()
        before = self.repo.cas()
        with self.assertRaisesRegex(TaskError, "INVALID_DELIVERY_DOCUMENT"):
            service.deliver(
                *before,
                claim_id,
                None,
                f"{self.repo.task_path}/../delivery.md",
                "0" * 64,
            )
        self.assertEqual(before, self.repo.cas())

    def test_delivery_rejects_duplicate_document_on_fresh_attempt(self) -> None:
        service, claim_id = self.repo.offer_and_claim()
        document_path, document_digest = self.repo.prepare_delivery_document()
        document = self.repo.task_root / "delivery.md"
        document.write_text("# Duplicate\n", encoding="utf-8")
        run("git", "add", document_path, cwd=self.repo.candidate)
        run("git", "commit", "-m", "duplicate delivery document", "--", document_path, cwd=self.repo.candidate)
        with self.assertRaisesRegex(TaskError, "DUPLICATE_DELIVERY_DOCUMENT"):
            service.deliver(
                *self.repo.cas(),
                claim_id,
                None,
                document_path,
                hashlib.sha256(document.read_bytes()).hexdigest(),
            )
        self.assertEqual("implementing", self.repo.state()["lifecycle"]["phase"])

    def test_delivery_freezes_future_execution_transitions(self) -> None:
        service, _ = self.repo.delivered()
        with self.assertRaisesRegex(TaskError, "INVALID_TRANSITION"):
            service.offer(*self.repo.cas(), "manual", ROLE_DIGEST, CONFIG_DIGEST, FUTURE_TIME)
        delivery = self.repo.state()["lifecycle"]["delivery"]
        with self.assertRaisesRegex(TaskError, "INVALID_TRANSITION"):
            service.deliver(
                *self.repo.cas(),
                delivery["claimId"],
                None,
                delivery["deliveryDocumentPath"],
                delivery["deliveryDocumentDigest"],
            )

    def test_status_never_exposes_runtime_path_or_capability(self) -> None:
        service = self.repo.ready_and_authorized()
        service.offer(*self.repo.cas(), "manual", ROLE_DIGEST, CONFIG_DIGEST, FUTURE_TIME)
        encoded = canonical_bytes(service.status()).decode("utf-8")
        offer_id = json.loads((self.repo.task_root / "offer.json").read_text(encoding="utf-8"))["offerId"]
        capability = RuntimeStore(self.repo.runtime_root).read_capability(offer_id)["capability"]
        self.assertNotIn(str(self.repo.root), encoded)
        self.assertNotIn(capability, encoded)


if __name__ == "__main__":
    unittest.main()
