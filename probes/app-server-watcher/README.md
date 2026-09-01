# GKD-M-1C live probe

`live_probe.py` is the only evidence generator for the external watcher live
gate. It starts fresh `codex exec` parents with process-local MCP
configuration, obtains parent and child identities from Codex's MCP correlation
metadata, revalidates them through an independent `codex app-server`
connection, and calls the existing watcher through real MCP stdio. Every known
canary thread is deleted before the owning processes close.

The four fixed scenarios are `normal`, `abnormal`, `cas_reject`, and
`orchestrator_failure`. Tool input can select only one of those enums. It cannot
provide a command, path, identity, prompt, timeout, or steer text. The probe
always sends `maxWaitMs=43200000`, configures `tool_timeout_sec=43200`, and uses
the same production watcher state machine with an accelerated health interval.
This is a combined timeout contract, not a twelve-hour wall-clock soak.

Raw app-server and MCP payloads stay in process memory only long enough to
extract approved identity relationships, event enums, field names, statuses,
and counts. The evidence file stores one-way identity digests and allowlist
traces. It never stores prompts, responses, tool arguments, tool results,
remote error text, environment values, or absolute paths.

The normalized digest covers the final gate decisions, runtime contract,
M-1B contract identity, configuration/cleanup booleans, and security flags.
Timing-sensitive intermediate assertions remain in the full evidence but do
not change the digest when they lead to the same fail-closed decision.

Run the short negative tests with:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. python3 -m unittest discover -s tests/watchdog/live -p 'live_test_*.py' -t .
```

Run the live gate with:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. python3 probes/app-server-watcher/live_probe.py --output evidence/m-1-external-watcher-live-gate/live-results.json
```

The outcome is always exactly `external_watcher_supported` or `unsupported`.
Any missing live fact, ambiguous identity, unexpected frame, unsafe anomaly,
timeout, config mutation, or cleanup failure produces `unsupported`.

The historical live lane was captured against `codex-cli 0.147.0`; its
version/schema evidence remains read-only. The current local CLI baseline is
`0.152.0` with a different relevant-schema digest, recorded in
`evidence/m-1-native-d2/compatibility-baselines.json`. A new or changed CLI
must be captured and reviewed before it can be used by this legacy lane. This
compatibility record does not enable the automatic watcher or change the
manual-first default bundle.
