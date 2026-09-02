from __future__ import annotations

import json
from pathlib import Path


BUNDLE_ROOT = Path("canonical/payload")
SOURCE_ROOT = Path("canonical")
def bundle_digest() -> str:
    return json.loads((SOURCE_ROOT / "manifest.lock.json").read_text(encoding="utf-8"))["contentDigest"]
