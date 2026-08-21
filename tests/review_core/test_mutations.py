from __future__ import annotations

from copy import deepcopy
import unittest

from gkd_review.adapter import validate_adapter
from gkd_review.core import validate_review_state
from gkd_review.remediation import validate_remediation
from gkd_task.errors import TaskError
from tests.review_core.helpers import adapter, state


class ReviewMutationContracts(unittest.TestCase):
    def test_adapter_duplicate_repository_ids_fail_closed(self) -> None:
        value = adapter()
        value["repositories"][1]["id"] = value["repositories"][0]["id"]
        with self.assertRaisesRegex(TaskError, "ADAPTER_INVALID"):
            validate_adapter(value)

    def test_state_unknown_approval_fails_closed(self) -> None:
        value = state()
        value["approval"]["approved"] = ["merge"]
        with self.assertRaisesRegex(TaskError, "REVIEW_STATE_INVALID"):
            validate_review_state(value)

    def test_remediation_unknown_finding_reference_fails_closed(self) -> None:
        from gkd_review.remediation import begin_remediation

        value = begin_remediation(state(), [{"id": "F-001", "severity": "medium", "summary": "safe summary"}])
        value = deepcopy(value)
        value["pendingFindings"] = ["F-999"]
        with self.assertRaisesRegex(TaskError, "REMEDIATION_INVALID"):
            validate_remediation(value)


if __name__ == "__main__":
    unittest.main()
