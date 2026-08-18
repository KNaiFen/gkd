from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
LIBRARY = ROOT / "canonical" / "payload" / "lib"
if str(LIBRARY) not in sys.path:
    sys.path.insert(0, str(LIBRARY))

import gkd_bundle  # noqa: E402


def copy_source(destination: Path) -> Path:
    source = destination / "canonical"
    shutil.copytree(ROOT / "canonical", source, copy_function=shutil.copy2, symlinks=True)
    return source


def copy_governance_repo(destination: Path) -> Path:
    repo = destination / "repo"
    repo.mkdir()
    shutil.copytree(ROOT / "canonical", repo / "canonical", copy_function=shutil.copy2)
    shutil.copytree(ROOT / "docs", repo / "docs", copy_function=shutil.copy2)
    for name in ("VISION.md", "README.md", "AGENTS.md"):
        shutil.copy2(ROOT / name, repo / name)
    return repo


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        (sys.executable, str(ROOT / "canonical" / "payload" / "bin" / "gkd-bundle"), *arguments),
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
