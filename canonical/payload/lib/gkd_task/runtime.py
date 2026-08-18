"""Machine-local attachments, secrets, envelopes, locks, and journals."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import os
import stat
import time
from typing import Any, Iterator

from .canonical import (
    atomic_write,
    canonical_bytes,
    digest_object,
    read_canonical_json,
    require_keys,
    require_sha256,
    require_string,
    require_utc,
    sha256_bytes,
    unlink_file,
)
from .errors import TaskError


RUNTIME_SCHEMA_VERSION = 1


def runtime_key(repository: str, task_id: str, task_branch: str) -> str:
    return digest_object(
        {"repository": repository, "taskId": task_id, "taskBranch": task_branch}
    )


def _absolute_directory(value: Any, code: str, must_exist: bool = True) -> Path:
    if not isinstance(value, str) or not value.startswith("/") or "\x00" in value:
        raise TaskError(code)
    path = Path(value)
    if path.is_symlink() or (must_exist and not path.is_dir()):
        raise TaskError(code)
    try:
        resolved = path.resolve(strict=must_exist)
    except OSError:
        raise TaskError(code) from None
    if not resolved.is_absolute():
        raise TaskError(code)
    return resolved


def validate_attachment(value: dict[str, Any]) -> None:
    require_keys(
        value,
        {
            "schemaVersion",
            "kind",
            "repository",
            "taskId",
            "taskBranch",
            "taskPath",
            "candidateRoot",
            "commonDir",
            "updatedAt",
            "attachmentDigest",
        },
        "INVALID_RUNTIME_ATTACHMENT",
    )
    if value["schemaVersion"] != RUNTIME_SCHEMA_VERSION or value["kind"] != "attachment":
        raise TaskError("INVALID_RUNTIME_ATTACHMENT")
    for field in ("repository", "taskId", "taskBranch", "taskPath"):
        require_string(value[field], "INVALID_RUNTIME_ATTACHMENT")
    _absolute_directory(value["candidateRoot"], "INVALID_RUNTIME_ATTACHMENT")
    _absolute_directory(value["commonDir"], "INVALID_RUNTIME_ATTACHMENT")
    require_utc(value["updatedAt"], "INVALID_RUNTIME_ATTACHMENT")
    require_sha256(value["attachmentDigest"], "INVALID_RUNTIME_ATTACHMENT")
    unsigned = dict(value)
    actual = unsigned.pop("attachmentDigest")
    if digest_object(unsigned) != actual:
        raise TaskError("INVALID_RUNTIME_ATTACHMENT")


def validate_capability(value: dict[str, Any]) -> None:
    require_keys(
        value,
        {"schemaVersion", "kind", "offerId", "epoch", "capability", "capabilityDigest", "createdAt"},
        "INVALID_RUNTIME_CAPABILITY",
    )
    if value["schemaVersion"] != RUNTIME_SCHEMA_VERSION or value["kind"] != "capability":
        raise TaskError("INVALID_RUNTIME_CAPABILITY")
    require_sha256(value["offerId"], "INVALID_RUNTIME_CAPABILITY")
    if not isinstance(value["epoch"], int) or value["epoch"] < 0:
        raise TaskError("INVALID_RUNTIME_CAPABILITY")
    if not isinstance(value["capability"], str) or not 32 <= len(value["capability"]) <= 256:
        raise TaskError("INVALID_RUNTIME_CAPABILITY")
    require_sha256(value["capabilityDigest"], "INVALID_RUNTIME_CAPABILITY")
    if sha256_bytes(value["capability"].encode("utf-8")) != value["capabilityDigest"]:
        raise TaskError("INVALID_RUNTIME_CAPABILITY")
    require_utc(value["createdAt"], "INVALID_RUNTIME_CAPABILITY")


def validate_envelope(value: dict[str, Any]) -> None:
    legacy_keys = {
            "schemaVersion",
            "kind",
            "envelopeId",
            "offerId",
            "epoch",
            "capability",
            "candidateRoot",
            "taskPath",
            "route",
            "roleDigest",
            "configDigest",
            "createdAt",
            "envelopeDigest",
        }
    if "roleName" in value or "bundleDigest" in value:
        require_keys(value, legacy_keys | {"roleName", "bundleDigest"}, "INVALID_LAUNCH_ENVELOPE")
        require_string(value["roleName"], "INVALID_LAUNCH_ENVELOPE")
        require_sha256(value["bundleDigest"], "INVALID_LAUNCH_ENVELOPE")
    else:
        require_keys(value, legacy_keys, "INVALID_LAUNCH_ENVELOPE")
    if value["schemaVersion"] != RUNTIME_SCHEMA_VERSION or value["kind"] != "launch-envelope":
        raise TaskError("INVALID_LAUNCH_ENVELOPE")
    for field in ("envelopeId", "offerId", "roleDigest", "configDigest", "envelopeDigest"):
        require_sha256(value[field], "INVALID_LAUNCH_ENVELOPE")
    if not isinstance(value["epoch"], int) or value["epoch"] < 0:
        raise TaskError("INVALID_LAUNCH_ENVELOPE")
    if not isinstance(value["capability"], str) or not 32 <= len(value["capability"]) <= 256:
        raise TaskError("INVALID_LAUNCH_ENVELOPE")
    _absolute_directory(value["candidateRoot"], "INVALID_LAUNCH_ENVELOPE")
    for field in ("taskPath", "route"):
        require_string(value[field], "INVALID_LAUNCH_ENVELOPE")
    require_utc(value["createdAt"], "INVALID_LAUNCH_ENVELOPE")
    unsigned = dict(value)
    actual = unsigned.pop("envelopeDigest")
    if digest_object(unsigned) != actual:
        raise TaskError("INVALID_LAUNCH_ENVELOPE")


def validate_claim_receipt(value: dict[str, Any]) -> None:
    require_keys(
        value,
        {
            "schemaVersion",
            "kind",
            "taskId",
            "repository",
            "taskBranch",
            "taskPath",
            "offerId",
            "claimId",
            "epoch",
            "claimBaseHead",
            "claimCommit",
            "claimStateDigest",
            "offerDigest",
            "transactionId",
            "transactionDigest",
            "recordedAt",
            "receiptDigest",
        },
        "INVALID_CLAIM_RECEIPT",
    )
    if value["schemaVersion"] != RUNTIME_SCHEMA_VERSION or value["kind"] != "claim-receipt":
        raise TaskError("INVALID_CLAIM_RECEIPT")
    for field in ("taskId", "repository", "taskBranch", "taskPath"):
        require_string(value[field], "INVALID_CLAIM_RECEIPT")
    for field in ("offerId", "claimId", "claimStateDigest", "offerDigest", "transactionId", "transactionDigest", "receiptDigest"):
        require_sha256(value[field], "INVALID_CLAIM_RECEIPT")
    if not isinstance(value["epoch"], int) or value["epoch"] < 0:
        raise TaskError("INVALID_CLAIM_RECEIPT")
    for field in ("claimBaseHead", "claimCommit"):
        if not isinstance(value[field], str) or len(value[field]) != 40 or any(c not in "0123456789abcdef" for c in value[field]):
            raise TaskError("INVALID_CLAIM_RECEIPT")
    require_utc(value["recordedAt"], "INVALID_CLAIM_RECEIPT")
    unsigned = dict(value)
    actual = unsigned.pop("receiptDigest")
    if digest_object(unsigned) != actual:
        raise TaskError("INVALID_CLAIM_RECEIPT")


class RuntimeStore:
    def __init__(self, root: Path) -> None:
        if not root.is_absolute() or root.is_symlink():
            raise TaskError("INVALID_RUNTIME_ROOT")
        parent = root.parent
        if parent.is_symlink() or not parent.is_dir():
            raise TaskError("INVALID_RUNTIME_ROOT")
        root.mkdir(mode=0o700, parents=False, exist_ok=True)
        if root.is_symlink() or not root.is_dir():
            raise TaskError("INVALID_RUNTIME_ROOT")
        os.chmod(root, 0o700)
        self.root = root.resolve()

    def _path(self, category: str, key: str, suffix: str = ".json") -> Path:
        require_sha256(key, "INVALID_RUNTIME_KEY")
        directory = self.root / category
        directory.mkdir(mode=0o700, exist_ok=True)
        if directory.is_symlink() or not directory.is_dir():
            raise TaskError("INVALID_RUNTIME_ROOT")
        return directory / f"{key}{suffix}"

    def _write_private(self, path: Path, value: dict[str, Any]) -> None:
        atomic_write(path, canonical_bytes(value), mode=0o600)

    def write_attachment(self, value: dict[str, Any]) -> None:
        unsigned = dict(value)
        unsigned.pop("attachmentDigest", None)
        unsigned["attachmentDigest"] = digest_object(unsigned)
        validate_attachment(unsigned)
        key = runtime_key(unsigned["repository"], unsigned["taskId"], unsigned["taskBranch"])
        self._write_private(self._path("attachments", key), unsigned)

    def read_attachment(self, repository: str, task_id: str, task_branch: str) -> dict[str, Any]:
        key = runtime_key(repository, task_id, task_branch)
        return read_canonical_json(self._path("attachments", key), "worktree_missing", validate_attachment)

    def delete_attachment(self, repository: str, task_id: str, task_branch: str) -> None:
        unlink_file(self._path("attachments", runtime_key(repository, task_id, task_branch)))

    def write_capability(self, key: str, value: dict[str, Any]) -> None:
        validate_capability(value)
        self._write_private(self._path("capabilities", key), value)

    def read_capability(self, key: str) -> dict[str, Any]:
        return read_canonical_json(self._path("capabilities", key), "CAPABILITY_UNAVAILABLE", validate_capability)

    def delete_capability(self, key: str) -> None:
        unlink_file(self._path("capabilities", key))

    def write_envelope(self, envelope_id: str, value: dict[str, Any]) -> Path:
        validate_envelope(value)
        path = self._path("envelopes", envelope_id)
        self._write_private(path, value)
        return path

    def read_envelope(self, envelope_id: str) -> dict[str, Any]:
        return read_canonical_json(self._path("envelopes", envelope_id), "INVALID_LAUNCH_ENVELOPE", validate_envelope)

    def delete_envelope(self, envelope_id: str) -> None:
        unlink_file(self._path("envelopes", envelope_id))

    def write_claim_receipt(self, claim_id: str, value: dict[str, Any]) -> None:
        require_sha256(claim_id, "INVALID_CLAIM_RECEIPT")
        validate_claim_receipt(value)
        if value["claimId"] != claim_id:
            raise TaskError("INVALID_CLAIM_RECEIPT")
        self._write_private(self._path("claim-receipts", claim_id), value)

    def read_claim_receipt(self, claim_id: str) -> dict[str, Any]:
        require_sha256(claim_id, "INVALID_CLAIM_RECEIPT")
        return read_canonical_json(
            self._path("claim-receipts", claim_id),
            "CLAIM_RECEIPT_UNAVAILABLE",
            validate_claim_receipt,
        )

    def delete_claim_receipt(self, claim_id: str) -> None:
        require_sha256(claim_id, "INVALID_CLAIM_RECEIPT")
        unlink_file(self._path("claim-receipts", claim_id))

    def write_activation(self, value: dict[str, Any]) -> None:
        from gkd_role.activation import validate_activation

        validate_activation(value)
        self._write_private(self._path("activations", value["activationId"]), value)

    def read_activation(self, activation_id: str) -> dict[str, Any]:
        from gkd_role.activation import validate_activation

        require_sha256(activation_id, "INVALID_ACTIVATION")
        return read_canonical_json(
            self._path("activations", activation_id),
            "ACTIVATION_UNAVAILABLE",
            validate_activation,
        )

    def write_activation_receipt(self, value: dict[str, Any]) -> None:
        from gkd_role.activation import validate_activation_receipt

        validate_activation_receipt(value)
        self._write_private(
            self._path("activation-receipts", value["activationId"]), value
        )
        self._write_private(
            self._path("claim-activation-receipts", value["claimId"]), value
        )

    def read_activation_receipt(self, activation_id: str) -> dict[str, Any]:
        from gkd_role.activation import validate_activation_receipt

        require_sha256(activation_id, "INVALID_ACTIVATION_RECEIPT")
        return read_canonical_json(
            self._path("activation-receipts", activation_id),
            "ACTIVATION_RECEIPT_UNAVAILABLE",
            validate_activation_receipt,
        )

    def read_claim_activation_receipt(self, claim_id: str) -> dict[str, Any]:
        from gkd_role.activation import validate_activation_receipt

        require_sha256(claim_id, "INVALID_ACTIVATION_RECEIPT")
        return read_canonical_json(
            self._path("claim-activation-receipts", claim_id),
            "ACTIVATION_RECEIPT_UNAVAILABLE",
            validate_activation_receipt,
        )

    def delete_claim_activation_receipt(self, claim_id: str) -> None:
        require_sha256(claim_id, "INVALID_ACTIVATION_RECEIPT")
        unlink_file(self._path("claim-activation-receipts", claim_id))

    def read_journal(self, transaction_id: str) -> dict[str, Any]:
        from .transaction import validate_journal

        return read_canonical_json(
            self.journal_path(transaction_id),
            "INVALID_TRANSACTION_JOURNAL",
            validate_journal,
        )

    def committed_journals(self) -> list[dict[str, Any]]:
        from .transaction import validate_journal

        directory = self.root / "transactions"
        if not directory.exists():
            return []
        if directory.is_symlink() or not directory.is_dir():
            raise TaskError("INVALID_RUNTIME_ROOT")
        result: list[dict[str, Any]] = []
        for path in sorted(directory.iterdir()):
            if path.is_symlink() or not path.is_file() or path.suffix != ".json" or path.stem != path.stem.lower():
                raise TaskError("INVALID_RUNTIME_ROOT")
            transaction_id = path.stem
            require_sha256(transaction_id, "INVALID_RUNTIME_ROOT")
            journal = read_canonical_json(path, "INVALID_TRANSACTION_JOURNAL", validate_journal)
            if journal["status"] == "committed":
                result.append(journal)
        return result

    def delete_envelopes_for_offer(self, offer_id: str) -> None:
        require_sha256(offer_id, "INVALID_OFFER")
        directory = self.root / "envelopes"
        if not directory.exists():
            return
        if directory.is_symlink() or not directory.is_dir():
            raise TaskError("INVALID_RUNTIME_ROOT")
        for path in sorted(directory.iterdir()):
            if path.is_symlink() or not path.is_file() or path.suffix != ".json":
                raise TaskError("INVALID_RUNTIME_ROOT")
            envelope = read_canonical_json(path, "INVALID_LAUNCH_ENVELOPE", validate_envelope)
            if envelope["offerId"] == offer_id:
                unlink_file(path)

    def journal_path(self, transaction_id: str) -> Path:
        return self._path("transactions", transaction_id)

    def active_transaction_path(self, key: str) -> Path:
        return self._path("active-transactions", key)

    def doubt_path(self, key: str) -> Path:
        return self._path("transaction-doubt", key)

    @contextmanager
    def lock(self, key: str, owner_token: str, timeout_seconds: float = 5.0) -> Iterator[None]:
        require_sha256(key, "INVALID_RUNTIME_KEY")
        lock_root = self.root / "locks"
        lock_root.mkdir(mode=0o700, exist_ok=True)
        lock_path = lock_root / f"{key}.lock"
        deadline = time.monotonic() + max(0.0, timeout_seconds)
        while True:
            try:
                lock_path.mkdir(mode=0o700)
                break
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise TaskError("LOCK_TIMEOUT") from None
                time.sleep(0.025)
            except OSError:
                raise TaskError("LOCK_FAILED") from None
        owner = lock_path / "owner"
        try:
            atomic_write(owner, owner_token.encode("ascii") + b"\n", mode=0o600)
            yield
        finally:
            try:
                if owner.read_bytes() != owner_token.encode("ascii") + b"\n":
                    raise TaskError("LOCK_OWNERSHIP_LOST")
                owner.unlink()
                lock_path.rmdir()
            except FileNotFoundError:
                raise TaskError("LOCK_OWNERSHIP_LOST") from None
            except OSError:
                raise TaskError("LOCK_RELEASE_FAILED") from None
