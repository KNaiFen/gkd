"""Exact-file Git transactions with prepared journal recovery."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Any, Callable

from .canonical import atomic_write, canonical_bytes, digest_object, read_canonical_json, relative_path, require_keys, require_sha1, require_sha256, require_utc, unlink_file
from .errors import TaskError
from .gitops import changed_paths, commit_exact, git, head, require_clean
from .model import read_state
from .runtime import RuntimeStore


JOURNAL_SCHEMA_VERSION = 1


def _encode(value: bytes | None) -> str | None:
    return None if value is None else base64.b64encode(value).decode("ascii")


def _decode(value: str | None) -> bytes | None:
    if value is None:
        return None
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except (ValueError, UnicodeEncodeError):
        raise TaskError("INVALID_TRANSACTION_JOURNAL") from None


def validate_journal(value: dict[str, Any]) -> None:
    require_keys(
        value,
        {
            "schemaVersion",
            "transactionId",
            "runtimeKey",
            "status",
            "expectedHead",
            "expectedRevision",
            "files",
            "createdAt",
            "committedHead",
            "journalDigest",
        },
        "INVALID_TRANSACTION_JOURNAL",
    )
    if value["schemaVersion"] != JOURNAL_SCHEMA_VERSION or value["status"] not in {"prepared", "committed", "rolled_back"}:
        raise TaskError("INVALID_TRANSACTION_JOURNAL")
    require_sha256(value["transactionId"], "INVALID_TRANSACTION_JOURNAL")
    require_sha256(value["runtimeKey"], "INVALID_TRANSACTION_JOURNAL")
    require_sha1(value["expectedHead"], "INVALID_TRANSACTION_JOURNAL")
    if not isinstance(value["expectedRevision"], int) or value["expectedRevision"] < 0:
        raise TaskError("INVALID_TRANSACTION_JOURNAL")
    if not isinstance(value["files"], list) or not value["files"]:
        raise TaskError("INVALID_TRANSACTION_JOURNAL")
    paths = []
    for record in value["files"]:
        if not isinstance(record, dict):
            raise TaskError("INVALID_TRANSACTION_JOURNAL")
        require_keys(record, {"path", "preimage", "postimage"}, "INVALID_TRANSACTION_JOURNAL")
        paths.append(relative_path(record["path"], "INVALID_TRANSACTION_JOURNAL"))
        _decode(record["preimage"])
        _decode(record["postimage"])
        if record["preimage"] == record["postimage"]:
            raise TaskError("INVALID_TRANSACTION_JOURNAL")
    if paths != sorted(set(paths)):
        raise TaskError("INVALID_TRANSACTION_JOURNAL")
    require_utc(value["createdAt"], "INVALID_TRANSACTION_JOURNAL")
    if value["committedHead"] is not None:
        require_sha1(value["committedHead"], "INVALID_TRANSACTION_JOURNAL")
    require_sha256(value["journalDigest"], "INVALID_TRANSACTION_JOURNAL")
    unsigned = dict(value)
    actual = unsigned.pop("journalDigest")
    if digest_object(unsigned) != actual:
        raise TaskError("INVALID_TRANSACTION_JOURNAL")


def _finalize_journal(value: dict[str, Any]) -> dict[str, Any]:
    result = dict(value)
    result.pop("journalDigest", None)
    result["journalDigest"] = digest_object(result)
    return result


@dataclass(frozen=True)
class TransactionChange:
    files: dict[str, bytes | None]
    message: str
    result: dict[str, Any]


class TransactionManager:
    def __init__(
        self,
        candidate_root: Path,
        task_path: str,
        runtime: RuntimeStore,
        runtime_key: str,
        clock: Any,
        nonce: Any,
        failure_hook: Callable[[str], None] | None = None,
    ) -> None:
        self.candidate_root = candidate_root.resolve()
        self.task_path = relative_path(task_path, "INVALID_TASK_PATH")
        self.state_path = f"{self.task_path}/task.json"
        self.runtime = runtime
        self.runtime_key = runtime_key
        self.clock = clock
        self.nonce = nonce
        self.failure_hook = failure_hook or (lambda phase: None)

    def _current_active(self) -> dict[str, Any] | None:
        path = self.runtime.active_transaction_path(self.runtime_key)
        if not path.exists():
            return None
        pointer = read_canonical_json(path, "INVALID_TRANSACTION_JOURNAL")
        require_keys(pointer, {"schemaVersion", "transactionId"}, "INVALID_TRANSACTION_JOURNAL")
        if pointer["schemaVersion"] != JOURNAL_SCHEMA_VERSION:
            raise TaskError("INVALID_TRANSACTION_JOURNAL")
        require_sha256(pointer["transactionId"], "INVALID_TRANSACTION_JOURNAL")
        return pointer

    def ensure_safe(self) -> None:
        if self.runtime.doubt_path(self.runtime_key).exists():
            raise TaskError("transaction_in_doubt")
        if self._current_active() is not None:
            raise TaskError("TRANSACTION_RECOVERY_REQUIRED")

    def execute(
        self,
        expected_head: str,
        expected_revision: int,
        builder: Callable[[dict[str, Any]], TransactionChange],
        state_loader: Callable[[], dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        require_sha1(expected_head, "HEAD_MISMATCH")
        if not isinstance(expected_revision, int) or expected_revision < 0:
            raise TaskError("REVISION_MISMATCH")
        owner_token = self.nonce.token()
        owner_digest = digest_object({"owner": owner_token})
        with self.runtime.lock(self.runtime_key, owner_digest):
            self.ensure_safe()
            if head(self.candidate_root) != expected_head:
                raise TaskError("HEAD_MISMATCH")
            require_clean(self.candidate_root)
            state = (
                state_loader()
                if state_loader is not None
                else read_state(
                    self.candidate_root / self.state_path,
                    self.candidate_root / self.task_path,
                )
            )
            if state["revision"] != expected_revision:
                raise TaskError("REVISION_MISMATCH")
            change = builder(state)
            normalized: dict[str, bytes | None] = {}
            preimages: dict[str, bytes | None] = {}
            for path, postimage in change.files.items():
                relative = relative_path(path, "INVALID_COORDINATION_PATH")
                target = self.candidate_root / relative
                if target.is_symlink() or (target.exists() and not target.is_file()):
                    raise TaskError("INVALID_COORDINATION_PATH")
                preimage = target.read_bytes() if target.exists() else None
                if preimage != postimage:
                    normalized[relative] = postimage
                    preimages[relative] = preimage
            if self.state_path not in normalized:
                raise TaskError("INVALID_TRANSACTION_CHANGE")
            transaction_id = digest_object(
                {
                    "runtimeKey": self.runtime_key,
                    "expectedHead": expected_head,
                    "expectedRevision": expected_revision,
                    "nonce": self.nonce.token(),
                }
            )
            journal = _finalize_journal(
                {
                    "schemaVersion": JOURNAL_SCHEMA_VERSION,
                    "transactionId": transaction_id,
                    "runtimeKey": self.runtime_key,
                    "status": "prepared",
                    "expectedHead": expected_head,
                    "expectedRevision": expected_revision,
                    "files": [
                        {"path": path, "preimage": _encode(preimages[path]), "postimage": _encode(normalized[path])}
                        for path in sorted(normalized)
                    ],
                    "createdAt": self.clock.now(),
                    "committedHead": None,
                }
            )
            journal_path = self.runtime.journal_path(transaction_id)
            atomic_write(journal_path, canonical_bytes(journal), mode=0o600)
            atomic_write(
                self.runtime.active_transaction_path(self.runtime_key),
                canonical_bytes({"schemaVersion": JOURNAL_SCHEMA_VERSION, "transactionId": transaction_id}),
                mode=0o600,
            )
            self.failure_hook("prepared")
            for path in sorted(normalized):
                target = self.candidate_root / path
                if normalized[path] is None:
                    unlink_file(target)
                else:
                    atomic_write(target, normalized[path] or b"")
            self.failure_hook("written")
            committed_head = commit_exact(self.candidate_root, sorted(normalized), change.message)
            self.failure_hook("committed")
            journal["status"] = "committed"
            journal["committedHead"] = committed_head
            journal = _finalize_journal(journal)
            atomic_write(journal_path, canonical_bytes(journal), mode=0o600)
            unlink_file(self.runtime.active_transaction_path(self.runtime_key))
            require_clean(self.candidate_root)
            result = dict(change.result)
            result["head"] = committed_head
            result["transactionId"] = transaction_id
            result["transactionDigest"] = journal["journalDigest"]
            return result

    def _write_doubt(self, transaction_id: str) -> None:
        marker = {
            "schemaVersion": JOURNAL_SCHEMA_VERSION,
            "status": "transaction_in_doubt",
            "transactionId": transaction_id,
            "recordedAt": self.clock.now(),
        }
        atomic_write(self.runtime.doubt_path(self.runtime_key), canonical_bytes(marker), mode=0o600)

    def recover(self) -> dict[str, Any]:
        owner_digest = digest_object({"owner": self.nonce.token()})
        with self.runtime.lock(self.runtime_key, owner_digest):
            if self.runtime.doubt_path(self.runtime_key).exists():
                raise TaskError("transaction_in_doubt")
            pointer = self._current_active()
            if pointer is None:
                return {"status": "no_recovery_needed"}
            transaction_id = pointer["transactionId"]
            journal_path = self.runtime.journal_path(transaction_id)
            journal = read_canonical_json(journal_path, "INVALID_TRANSACTION_JOURNAL", validate_journal)
            if journal["runtimeKey"] != self.runtime_key:
                self._write_doubt(transaction_id)
                raise TaskError("transaction_in_doubt")
            current_head = head(self.candidate_root)
            records = {record["path"]: record for record in journal["files"]}
            current: dict[str, bytes | None] = {}
            for path in records:
                target = self.candidate_root / path
                if target.is_symlink() or (target.exists() and not target.is_file()):
                    self._write_doubt(transaction_id)
                    raise TaskError("transaction_in_doubt")
                current[path] = target.read_bytes() if target.exists() else None
            pre = {path: _decode(record["preimage"]) for path, record in records.items()}
            post = {path: _decode(record["postimage"]) for path, record in records.items()}
            if journal["status"] == "committed" and current_head == journal["committedHead"] and current == post:
                unlink_file(self.runtime.active_transaction_path(self.runtime_key))
                return {"status": "recovered_committed", "head": current_head}
            if current_head == journal["expectedHead"] and all(current[path] in {pre[path], post[path]} for path in records):
                for path in sorted(records):
                    target = self.candidate_root / path
                    if pre[path] is None:
                        unlink_file(target)
                    else:
                        atomic_write(target, pre[path] or b"")
                git(self.candidate_root, "restore", "--staged", "--", *sorted(records), code="TRANSACTION_RECOVERY_FAILED")
                require_clean(self.candidate_root)
                journal["status"] = "rolled_back"
                journal = _finalize_journal(journal)
                atomic_write(journal_path, canonical_bytes(journal), mode=0o600)
                unlink_file(self.runtime.active_transaction_path(self.runtime_key))
                return {"status": "recovered_rolled_back", "head": current_head}
            if current == post and is_direct_child(self.candidate_root, journal["expectedHead"], current_head) and changed_paths(self.candidate_root, current_head) == sorted(records):
                journal["status"] = "committed"
                journal["committedHead"] = current_head
                journal = _finalize_journal(journal)
                atomic_write(journal_path, canonical_bytes(journal), mode=0o600)
                unlink_file(self.runtime.active_transaction_path(self.runtime_key))
                return {"status": "recovered_committed", "head": current_head}
            self._write_doubt(transaction_id)
            raise TaskError("transaction_in_doubt")


def is_direct_child(root: Path, expected_parent: str, current_head: str) -> bool:
    require_sha1(expected_parent, "INVALID_GIT_HEAD")
    require_sha1(current_head, "INVALID_GIT_HEAD")
    try:
        parent = git(root, "rev-parse", f"{current_head}^", code="GIT_OPERATION_FAILED").decode("ascii").strip()
    except UnicodeDecodeError:
        raise TaskError("GIT_OPERATION_FAILED") from None
    return parent == expected_parent
