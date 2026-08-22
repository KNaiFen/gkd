#!/usr/bin/env python3
"""Read-only fake for the narrow `gh api` surface used by M3-A tests."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys


def main() -> int:
    scenario_path = os.environ.get("GKD_FAKE_GITHUB_SCENARIO")
    if not scenario_path:
        return 2
    scenario = json.loads(Path(scenario_path).read_text(encoding="utf-8"))
    if scenario.get("transportFailure"):
        sys.stderr.write("Authorization: Bearer fixture-secret /Users/private/error\n")
        return 1
    if len(sys.argv) != 7 or sys.argv[1:6] != [
        "api",
        "--method",
        "GET",
        "-H",
        "Accept: application/vnd.github+json",
    ]:
        return 3
    endpoint = sys.argv[6]
    page_match = re.search(r"[?&]page=(\d+)", endpoint)
    page = page_match.group(1) if page_match else "1"
    if "/pulls/" in endpoint:
        value = scenario["pullRequest"]
    elif "/check-runs?" in endpoint:
        value = scenario.get("checkPages", {}).get(page, {"check_runs": [], "total_count": 0})
    elif "/statuses?" in endpoint:
        value = scenario.get("statusPages", {}).get(page, [])
    elif "/contents/canary.json?" in endpoint:
        reference = re.search(r"[?&]ref=([0-9a-f]{40})$", endpoint)
        if reference is None:
            return 4
        value = scenario.get("canaryMarkers", {}).get(reference.group(1))
        if value is None:
            return 4
    else:
        return 4
    sys.stdout.write(json.dumps(value, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
