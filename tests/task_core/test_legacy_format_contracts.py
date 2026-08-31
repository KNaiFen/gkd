from __future__ import annotations

import json
import unittest

from gkd_task.canonical import digest_object
from gkd_task.errors import TaskError
from gkd_task.model import validate_offer
from gkd_task.runtime import RuntimeStore, validate_envelope
from tests.task_core.helpers import CONFIG_DIGEST, FUTURE_TIME, ROLE_DIGEST, TaskRepo


class LegacyFormatContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TaskRepo()
        service = self.repo.ready_and_authorized()
        service.offer(*self.repo.cas(), "manual", ROLE_DIGEST, CONFIG_DIGEST, FUTURE_TIME)
        self.service = service
        self.handoff = service.handoff()

    def tearDown(self) -> None:
        self.repo.close()

    def _offer(self) -> dict:
        return json.loads((self.repo.task_root / "offer.json").read_text(encoding="utf-8"))

    def _envelope(self) -> dict:
        return RuntimeStore(self.repo.runtime_root).read_envelope(self.handoff["envelopeId"])

    def test_offer_v1_remains_readable(self) -> None:
        offer = self._offer()
        self.assertEqual(1, offer["schemaVersion"])
        validate_offer(offer)

    def test_offer_v1_rejects_automatic_route(self) -> None:
        offer = self._offer()
        offer["route"] = "automatic"
        with self.assertRaisesRegex(TaskError, "INVALID_OFFER"):
            validate_offer(offer)

    def test_launch_envelope_v1_remains_readable(self) -> None:
        envelope = self._envelope()
        self.assertEqual(1, envelope["schemaVersion"])
        validate_envelope(envelope)

    def test_launch_envelope_v1_rejects_automatic_route(self) -> None:
        envelope = self._envelope()
        envelope["route"] = "automatic"
        envelope["envelopeDigest"] = digest_object(
            {key: value for key, value in envelope.items() if key != "envelopeDigest"}
        )
        with self.assertRaisesRegex(TaskError, "INVALID_LAUNCH_ENVELOPE"):
            validate_envelope(envelope)


if __name__ == "__main__":
    unittest.main()
