from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = json.loads((ROOT / "canonical" / "payload" / "fixtures" / "review" / "multi-repository.json").read_text(encoding="utf-8"))


def adapter() -> dict:
    return json.loads(json.dumps(FIXTURE))


def state():
    from gkd_review.core import begin_review

    return begin_review(
        "targeted",
        adapter(),
        target="alpha",
        intent="review change",
        machine_facts={"baseBranch": "main", "requiredChecks": ["GKD Verify"]},
    )
