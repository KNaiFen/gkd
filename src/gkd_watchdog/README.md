# GKD external watcher core

This package is the version-bound, standard-library-only core for GKD-M-1B.
It exposes one MCP tool, `gkd_watch_agent`, through `scripts/gkd-watchdog-mcp`.

The tool accepts only the frozen structured identity, runtime digest, deadline,
and health interval. It cannot accept a command, path, shell argument, or steer
text. Before starting `codex app-server`, the production factory verifies
`codex-cli 0.147.0` and the frozen relevant-schema digest. The request digest
must equal that approved evidence, and credential-shaped identity values are
rejected before app-server construction. Health reads always set `includeTurns`
to `false` and bind both child and parent threads to the requested session.

The watcher emits no progress frame or health log. It returns once for a normal
terminal child, approved abnormal state, deadline, cancellation, protocol
failure, or orchestrator failure. Only an abnormal child can cause the fixed
`gkd_watchdog_event` steer, and the steer is guarded by the request's expected
parent turn. An active child is never followed by steer until its interrupt has
an explicit bound terminal confirmation. MCP stdin EOF uses bounded soft cancel
and forced session closure so app-server subprocesses are reaped before exit.

This task proves hermetic core and adapter contracts only. It does not claim
that a live Codex MCP connection can remain blocked for 12 hours; that is the
separate GKD-M-1C gate.
