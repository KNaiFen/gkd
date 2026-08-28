#!/usr/bin/env python3
"""Consume canonical verifier results and emit O3 evidence."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile

import gkd_bundle
from gkd_task.results import CanonicalResultError, SCOPE_NAMES, canonical_bytes, digest_object, load_canonical_results


def _directory(path: Path, code: str) -> Path:
    if path.is_symlink() or not path.is_dir():
        raise CanonicalResultError(code)
    return path.resolve()


def _within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--temporary-root", type=Path, required=True)
    parser.add_argument("--protected-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        repository = Path(__file__).resolve().parents[2]
        results_dir = _directory(args.canonical_results, "CANONICAL_RESULT_MISSING")
        temporary = _directory(args.temporary_root, "INVALID_TEMPORARY_ROOT")
        protected = _directory(args.protected_root, "INVALID_PROTECTED_ROOT")
        output_parent = _directory(args.output.parent, "INVALID_EVIDENCE_OUTPUT")
        output = output_parent / args.output.name
        system_temporary = Path(tempfile.gettempdir()).resolve()
        if temporary == system_temporary or not _within(temporary, system_temporary) or any(temporary.iterdir()):
            raise CanonicalResultError("INVALID_TEMPORARY_ROOT")
        if output.is_symlink() or output.is_dir() or any(_within(output, root) or _within(root, output) for root in (repository, results_dir, temporary, protected)):
            raise CanonicalResultError("EVIDENCE_OUTPUT_OVERLAP")
        before = gkd_bundle._snapshot_protected(protected)
        consumed = {scope: load_canonical_results(results_dir, scope, repository) for scope in SCOPE_NAMES}
        if any(temporary.iterdir()):
            raise CanonicalResultError("TEMPORARY_ROOT_NOT_CLEAN")
        after = gkd_bundle._snapshot_protected(protected)
        if before != after:
            raise CanonicalResultError("PROTECTED_HOME_CHANGED")
        manifest = json.loads((results_dir / "manifest.json").read_text(encoding="utf-8"))
        manifest_digest = manifest["manifestDigest"]
        evidence = {
            "baseSha": manifest["baseSha"],
            "canonicalResultsDigest": manifest_digest,
            "environment": manifest["environment"],
            "evidenceDigest": None,
            "headSha": manifest["headSha"],
            "schemaVersion": 1,
            "scopes": {
                scope: {
                    "behaviorExecutionCount": 1,
                    "resultDigest": consumed[scope]["resultDigest"],
                    "reused": True,
                    "tests": len(consumed[scope]["tests"]),
                }
                for scope in SCOPE_NAMES
            },
            "task": "GKD-O3",
            "totalTests": sum(len(consumed[scope]["tests"]) for scope in SCOPE_NAMES),
            "protected": {"before": before, "after": after, "unchanged": True},
            "temporaryRoot": {"cleanBefore": True, "cleanAfter": True},
            "outcome": "verifier_result_reuse_ready",
        }
        unsigned = dict(evidence)
        unsigned.pop("evidenceDigest")
        evidence["evidenceDigest"] = digest_object(unsigned)
        encoded = canonical_bytes(evidence)
        for forbidden in (os.fspath(repository), os.fspath(results_dir), os.fspath(temporary), os.fspath(protected)):
            if forbidden.encode("utf-8") in encoded:
                raise CanonicalResultError("EVIDENCE_CONTAINS_MACHINE_DETAIL")
        output.write_bytes(encoded)
        print(canonical_bytes({"canonicalResultsDigest": manifest_digest, "evidenceDigest": evidence["evidenceDigest"], "outcome": evidence["outcome"], "tests": evidence["totalTests"]}).decode(), end="")
        return 0
    except CanonicalResultError as error:
        print(canonical_bytes({"error": error.code, "status": "error"}).decode(), end="")
        return 2
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError, KeyError):
        print(canonical_bytes({"error": "FILESYSTEM_ERROR", "status": "error"}).decode(), end="")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

