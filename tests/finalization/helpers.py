from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any


FIXTURE = Path("canonical/payload/fixtures/finalization/generic-input.json")
ADAPTER_DIGEST = "f" * 64
AUTHORIZATION_DIGEST = "9" * 64
ASSET_DIGEST = "8" * 64


def finalization_input(mode: str = "closeout-only") -> dict[str, Any]:
    value = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if mode == "release":
        value["mode"] = "release"
        value["releaseSideEffects"] = True
        value["adapterDigest"] = ADAPTER_DIGEST
        value["authorizationDigest"] = AUTHORIZATION_DIGEST
        value["assets"] = [
            {
                "name": "gkd-1.2.3.tar.gz",
                "sourceSha": value["metadata"]["sourceSha"],
                "bundleDigest": value["metadata"]["bundleDigest"],
                "sha256": ASSET_DIGEST,
            }
        ]
    return deepcopy(value)
