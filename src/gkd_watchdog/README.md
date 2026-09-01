# GKD external watcher core

This package is the version-bound, standard-library-only core for GKD-M-1B.
It exposes one MCP tool, `gkd_watch_agent`, through `scripts/gkd-watchdog-mcp`.

The tool accepts only the frozen structured identity, runtime digest, deadline,
and health interval. It cannot accept a command, path, shell argument, or steer
text. Before starting `codex app-server`, the production factory verifies a
versioned CLI/schema baseline. The legacy `0.147.0` baseline remains readable;
the current captured `0.152.0` baseline is recorded for compatibility work but
does not enable the historical watcher request contract. An unknown CLI version
returns `codex_version_unsupported` and requires a new capture. A registered
version with a changed schema returns `schema_digest_mismatch`, and a request
bound to a different baseline returns `runtime_baseline_mismatch` before
app-server construction. Credential-shaped identity values are rejected before
app-server construction. Health reads always set `includeTurns` to `false` and
bind both child and parent threads to the requested session.

The watcher emits no progress frame or health log. It returns once for a normal
terminal child, approved abnormal state, deadline, cancellation, protocol
failure, or orchestrator failure. The historical `0.147.0` lane can issue the
fixed `gkd_watchdog_event` steer, guarded by the request's expected parent turn;
the current `0.152.0` lane fails closed as `turn_steer_unsupported` before an
app-server session is started. This distinction is intentional: generated
schema presence does not establish runtime feature availability. An active
child is never followed by steer until its interrupt has an explicit bound
terminal confirmation. MCP stdin EOF uses bounded soft cancel and forced
session closure so app-server subprocesses are reaped before exit.

The versioned, redacted capture record is
`evidence/m-1-native-d2/compatibility-baselines.json`. It preserves the old
`0.147.0` evidence and records the local `0.152.0` protocol summary without
storing generated schemas, command output, paths, or conversation bodies.
The current `0.152.0` initialize response contains only the four required
server metadata fields and does not advertise server capabilities; the parser
records that boundary as `unsupported`. Its feature registry marks `steer` as
`removed` even though `TurnSteerParams` remains in the generated schema. The
historical `0.147.0` protocol summary is `compatibility-only`, so neither
record is a claim that a current app-server watcher is available.

This task proves hermetic core and adapter contracts only. It does not claim
that a live Codex MCP connection can remain blocked for 12 hours; that is the
separate GKD-M-1C gate. Automatic watcher behavior remains a legacy lane and
the manual-first bundle remains unchanged.
