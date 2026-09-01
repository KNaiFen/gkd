"""Silent long-blocking watcher state machine."""

from __future__ import annotations

import hashlib
import math
import threading
import time
from typing import Any, Callable, Mapping, Protocol

from .constants import (
    FEATURE_REMOVED,
    EXPECTED_SCHEMA_DIGEST,
    INTERRUPT_CONFIRM_TIMEOUT_MS,
    RPC_TIMEOUT_MS,
    SCHEMA_VERSION,
    STEER_FEATURE,
)
from .jsonrpc import AppServerError, AppServerRemoteError, AppServerStartError
from .model import WatchRequest, WatchResult, canonical_json
from .runtime import RuntimeVerificationError, runtime_feature_status


class AppServerSession(Protocol):
    @property
    def transcript(self) -> tuple[dict[str, Any], ...]: ...

    def transcript_digest(self) -> str: ...

    def request(
        self, method: str, params: Mapping[str, Any], *, timeout_ms: int
    ) -> Any: ...

    def next_notification(self, timeout_ms: int) -> dict[str, Any] | None: ...

    def close(self) -> None: ...


class WatchProtocolError(AppServerError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class CancellationToken:
    def __init__(self) -> None:
        self._event = threading.Event()
        self._lock = threading.Lock()
        self._close_callbacks: set[Callable[[], None]] = set()
        self._force_closed = False

    def cancel(self) -> None:
        self._event.set()

    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def register_close(self, callback: Callable[[], None]) -> None:
        with self._lock:
            if self._force_closed:
                close_now = True
            else:
                self._close_callbacks.add(callback)
                close_now = False
        if close_now:
            callback()

    def unregister_close(self, callback: Callable[[], None]) -> None:
        with self._lock:
            self._close_callbacks.discard(callback)

    def force_close(self) -> None:
        with self._lock:
            self._force_closed = True
            callbacks = tuple(self._close_callbacks)
        for callback in callbacks:
            try:
                callback()
            except (OSError, RuntimeError, ValueError):
                pass


class WatchService:
    def __init__(
        self,
        session_factory: Callable[[WatchRequest, CancellationToken], AppServerSession],
        *,
        clock: Callable[[], float] = time.monotonic,
        cancel_poll_ms: int = 1_000,
        interrupt_confirm_timeout_ms: int = INTERRUPT_CONFIRM_TIMEOUT_MS,
    ) -> None:
        if cancel_poll_ms <= 0 or interrupt_confirm_timeout_ms <= 0:
            raise ValueError("watcher timeouts must be positive")
        self._session_factory = session_factory
        self._clock = clock
        self._cancel_poll_ms = cancel_poll_ms
        self._interrupt_confirm_timeout_ms = interrupt_confirm_timeout_ms

    def watch(
        self,
        request: WatchRequest,
        cancellation: CancellationToken | None = None,
    ) -> WatchResult:
        cancellation = cancellation or CancellationToken()
        started = self._clock()
        session: AppServerSession | None = None
        close_callback: Callable[[], None] | None = None
        health_checks = 0
        child_active = False
        if request.runtime_evidence_digest != EXPECTED_SCHEMA_DIGEST:
            reason = (
                "turn_steer_unsupported"
                if runtime_feature_status(request.runtime_evidence_digest, STEER_FEATURE)
                == FEATURE_REMOVED
                else "runtime_evidence_mismatch"
            )
            return self._result_without_session(
                request,
                "protocol_error",
                reason,
                health_checks,
                started,
            )
        try:
            session = self._session_factory(request, cancellation)
            close_callback = session.close
            cancellation.register_close(close_callback)
            decision = self._health_check(session, request)
            health_checks += 1
            if decision == "active":
                child_active = True
            elif decision == "systemError":
                return self._abnormal(
                    session,
                    request,
                    reason="thread_system_error",
                    interrupt_child=True,
                    health_checks=health_checks,
                    started=started,
                )
            else:
                return self._protocol_result(
                    session, request, "thread_status_unknown", health_checks, started
                )

            deadline = started + request.max_wait_ms / 1000
            next_health = started + request.health_interval_ms / 1000
            while True:
                if cancellation.is_cancelled():
                    if child_active:
                        self._cancel_bound_child(session, request, started)
                    return self._result(
                        session,
                        request,
                        "cancelled",
                        "caller_cancelled",
                        health_checks,
                        started,
                    )

                now = self._clock()
                if now >= deadline:
                    return self._result(
                        session,
                        request,
                        "deadline",
                        "deadline_elapsed",
                        health_checks,
                        started,
                    )

                target = min(next_health, deadline)
                wait_ms = max(0, int(round((target - now) * 1000)))
                wait_ms = min(wait_ms, self._cancel_poll_ms)
                notification = session.next_notification(wait_ms)
                if notification is not None:
                    terminal = self._handle_notification(
                        session,
                        request,
                        notification,
                        health_checks,
                        started,
                    )
                    if terminal is not None:
                        return terminal
                    continue

                now = self._clock()
                if now >= deadline:
                    return self._result(
                        session,
                        request,
                        "deadline",
                        "deadline_elapsed",
                        health_checks,
                        started,
                    )
                if now >= next_health:
                    decision = self._health_check(session, request)
                    health_checks += 1
                    if decision == "systemError":
                        return self._abnormal(
                            session,
                            request,
                            reason="thread_system_error",
                            interrupt_child=True,
                            health_checks=health_checks,
                            started=started,
                        )
                    if decision != "active":
                        return self._protocol_result(
                            session,
                            request,
                            "thread_status_unknown",
                            health_checks,
                            started,
                        )
                    next_health += request.health_interval_ms / 1000
        except RuntimeVerificationError as exc:
            return self._result_without_session(
                request, "protocol_error", exc.reason, health_checks, started
            )
        except AppServerStartError:
            return self._result_without_session(
                request,
                "orchestrator_error",
                "app_server_start_failed",
                health_checks,
                started,
            )
        except AppServerRemoteError as exc:
            abnormal_reasons = {
                "notFound": "thread_not_found",
                "errored": "child_errored",
                "interrupted": "child_interrupted",
                "systemError": "thread_system_error",
            }
            if session is not None and exc.classification in abnormal_reasons:
                return self._result(
                    session,
                    request,
                    "abnormal_child",
                    abnormal_reasons[exc.classification],
                    health_checks,
                    started,
                )
            reason = self._remote_reason("app_server", exc.classification)
            return self._protocol_result(
                session, request, reason, health_checks, started
            )
        except AppServerError as exc:
            return self._protocol_result(
                session, request, exc.reason, health_checks, started
            )
        except (OSError, RuntimeError):
            return self._result_without_session(
                request,
                "orchestrator_error",
                "app_server_start_failed",
                health_checks,
                started,
            )
        finally:
            if session is not None:
                if close_callback is not None:
                    cancellation.unregister_close(close_callback)
                session.close()

    def _health_check(self, session: AppServerSession, request: WatchRequest) -> str:
        child, status_type = self._read_thread(
            session, request.child_thread_id
        )
        if (
            child.get("sessionId") != request.session_id
            or child.get("parentThreadId") != request.parent_thread_id
        ):
            raise WatchProtocolError("child_thread_ownership_mismatch")
        self._verify_parent_thread(session, request)
        return status_type

    @staticmethod
    def _read_thread(
        session: AppServerSession, thread_id: str
    ) -> tuple[Mapping[str, Any], str]:
        response = session.request(
            "thread/read",
            {"threadId": thread_id, "includeTurns": False},
            timeout_ms=RPC_TIMEOUT_MS,
        )
        if not isinstance(response, Mapping):
            raise AppServerError()
        thread = response.get("thread")
        if not isinstance(thread, Mapping) or thread.get("id") != thread_id:
            raise AppServerError()
        turns = thread.get("turns")
        if not isinstance(turns, list) or turns:
            raise AppServerError()
        status = thread.get("status")
        if not isinstance(status, Mapping):
            raise AppServerError()
        status_type = status.get("type")
        if status_type not in {"active", "systemError", "idle", "notLoaded"}:
            raise AppServerError()
        return thread, status_type

    def _verify_parent_thread(
        self, session: AppServerSession, request: WatchRequest
    ) -> str:
        try:
            parent, status_type = self._read_thread(
                session, request.parent_thread_id
            )
        except AppServerRemoteError as exc:
            raise WatchProtocolError(
                self._remote_reason("parent_thread_read", exc.classification)
            ) from exc
        if parent.get("sessionId") != request.session_id:
            raise WatchProtocolError("parent_thread_ownership_mismatch")
        return status_type

    def _verify_control_scope(
        self, session: AppServerSession, request: WatchRequest
    ) -> str:
        try:
            child, status_type = self._read_thread(
                session, request.child_thread_id
            )
        except AppServerRemoteError as exc:
            raise WatchProtocolError(
                self._remote_reason("child_thread_read", exc.classification)
            ) from exc
        if (
            child.get("sessionId") != request.session_id
            or child.get("parentThreadId") != request.parent_thread_id
        ):
            raise WatchProtocolError("child_thread_ownership_mismatch")
        self._verify_parent_thread(session, request)
        return status_type

    def _handle_notification(
        self,
        session: AppServerSession,
        request: WatchRequest,
        notification: Mapping[str, Any],
        health_checks: int,
        started: float,
    ) -> WatchResult | None:
        method = notification.get("method")
        params = notification.get("params")
        if not isinstance(method, str) or not isinstance(params, Mapping):
            raise AppServerError()

        if method == "turn/completed":
            if params.get("threadId") != request.child_thread_id:
                return None
            turn = params.get("turn")
            if not isinstance(turn, Mapping) or turn.get("id") != request.child_turn_id:
                return None
            status = turn.get("status")
            if status == "completed":
                return self._result(
                    session,
                    request,
                    "normal_terminal",
                    "child_completed",
                    health_checks,
                    started,
                )
            if status in {"failed", "interrupted"}:
                return self._abnormal(
                    session,
                    request,
                    reason="child_failed" if status == "failed" else "child_interrupted",
                    interrupt_child=False,
                    health_checks=health_checks,
                    started=started,
                )
            raise AppServerError()

        if method == "thread/status/changed":
            if params.get("threadId") != request.child_thread_id:
                return None
            status = params.get("status")
            status_type = status.get("type") if isinstance(status, Mapping) else None
            if status_type == "active":
                return None
            if status_type == "systemError":
                return self._abnormal(
                    session,
                    request,
                    reason="thread_system_error",
                    interrupt_child=True,
                    health_checks=health_checks,
                    started=started,
                )
            if status_type in {"idle", "notLoaded"}:
                return self._protocol_result(
                    session,
                    request,
                    "thread_status_unknown",
                    health_checks,
                    started,
                )
            raise AppServerError()

        return None

    def _abnormal(
        self,
        session: AppServerSession,
        request: WatchRequest,
        *,
        reason: str,
        interrupt_child: bool,
        health_checks: int,
        started: float,
    ) -> WatchResult:
        if interrupt_child:
            child_status = self._verify_control_scope(session, request)
            if child_status not in {"active", "systemError"}:
                raise WatchProtocolError("child_interrupt_not_active")
            child_readable = self._interrupt_and_confirm(session, request, started)
            if child_readable:
                self._verify_control_scope(session, request)
            else:
                self._verify_parent_thread(session, request)
        else:
            self._verify_control_scope(session, request)

        event = canonical_json(
            {
                "schemaVersion": SCHEMA_VERSION,
                "type": "gkd_watchdog_event",
                "reason": reason,
                "taskId": request.task_id,
                "offerId": request.offer_id,
                "sessionId": request.session_id,
                "runtimeEvidenceDigest": request.runtime_evidence_digest,
            }
        )
        try:
            response = session.request(
                "turn/steer",
                {
                    "threadId": request.parent_thread_id,
                    "expectedTurnId": request.expected_parent_turn_id,
                    "input": [{"type": "text", "text": event, "text_elements": []}],
                },
                timeout_ms=RPC_TIMEOUT_MS,
            )
        except AppServerRemoteError as exc:
            if exc.classification != "expectedTurnMismatch":
                raise WatchProtocolError(
                    self._remote_reason("parent_steer", exc.classification)
                ) from exc
            return self._result(
                session,
                request,
                "parent_steer_rejected",
                "parent_expected_turn_rejected",
                health_checks,
                started,
            )
        if (
            not isinstance(response, Mapping)
            or response.get("turnId") != request.expected_parent_turn_id
        ):
            raise AppServerError()
        return self._result(
            session,
            request,
            "abnormal_child",
            reason,
            health_checks,
            started,
        )

    def _interrupt_and_confirm(
        self,
        session: AppServerSession,
        request: WatchRequest,
        started: float,
    ) -> bool:
        try:
            response = session.request(
                "turn/interrupt",
                {
                    "threadId": request.child_thread_id,
                    "turnId": request.child_turn_id,
                },
                timeout_ms=RPC_TIMEOUT_MS,
            )
        except AppServerRemoteError as exc:
            if exc.classification in {"notFound", "interrupted", "errored"}:
                return False
            raise WatchProtocolError(
                self._remote_reason("child_interrupt", exc.classification)
            ) from exc
        if not isinstance(response, Mapping):
            raise AppServerError()

        remaining_budget_ms = max(
            0,
            request.max_wait_ms
            - int(round((self._clock() - started) * 1000)),
        )
        timeout_ms = min(self._interrupt_confirm_timeout_ms, remaining_budget_ms)
        if timeout_ms <= 0:
            raise WatchProtocolError("child_interrupt_unconfirmed")
        deadline = self._clock() + timeout_ms / 1000
        while True:
            remaining = deadline - self._clock()
            if remaining <= 0:
                raise WatchProtocolError("child_interrupt_unconfirmed")
            notification = session.next_notification(math.ceil(remaining * 1000))
            if notification is None:
                raise WatchProtocolError("child_interrupt_unconfirmed")
            method = notification.get("method")
            params = notification.get("params")
            if method != "turn/completed" or not isinstance(params, Mapping):
                continue
            if params.get("threadId") != request.child_thread_id:
                continue
            turn = params.get("turn")
            if not isinstance(turn, Mapping) or turn.get("id") != request.child_turn_id:
                continue
            if turn.get("status") not in {"completed", "failed", "interrupted"}:
                raise WatchProtocolError("child_interrupt_unconfirmed")
            return True

    def _cancel_bound_child(
        self,
        session: AppServerSession,
        request: WatchRequest,
        started: float,
    ) -> None:
        child_status = self._verify_control_scope(session, request)
        if child_status not in {"active", "systemError"}:
            raise WatchProtocolError("cancel_child_not_active")
        self._interrupt_and_confirm(session, request, started)

    @staticmethod
    def _remote_reason(prefix: str, classification: str) -> str:
        suffixes = {
            "notFound": "not_found",
            "systemError": "system_error",
            "errored": "errored",
            "interrupted": "interrupted",
            "expectedTurnMismatch": "expected_turn_mismatch",
            "invalidParams": "invalid_params",
            "remoteError": "remote_error",
        }
        return f"{prefix}_{suffixes.get(classification, 'remote_error')}"

    def _protocol_result(
        self,
        session: AppServerSession | None,
        request: WatchRequest,
        reason: str,
        health_checks: int,
        started: float,
    ) -> WatchResult:
        if session is None:
            return self._result_without_session(
                request, "protocol_error", reason, health_checks, started
            )
        return self._result(
            session,
            request,
            "protocol_error",
            reason,
            health_checks,
            started,
        )

    def _result(
        self,
        session: AppServerSession,
        request: WatchRequest,
        outcome: str,
        reason: str,
        health_checks: int,
        started: float,
    ) -> WatchResult:
        return WatchResult(
            request=request,
            outcome=outcome,
            reason=reason,
            health_checks=health_checks,
            elapsed_ms=max(0, int(round((self._clock() - started) * 1000))),
            transcript_digest=session.transcript_digest(),
        )

    def _result_without_session(
        self,
        request: WatchRequest,
        outcome: str,
        reason: str,
        health_checks: int,
        started: float,
    ) -> WatchResult:
        empty_digest = hashlib.sha256(canonical_json([]).encode("utf-8")).hexdigest()
        return WatchResult(
            request=request,
            outcome=outcome,
            reason=reason,
            health_checks=health_checks,
            elapsed_ms=max(0, int(round((self._clock() - started) * 1000))),
            transcript_digest=empty_digest,
        )
