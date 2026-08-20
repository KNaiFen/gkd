# Canonical development bundle

`canonical/` is the only bundle source root. `source.toml` is the reviewed
developer declaration; `manifest.json` and `manifest.lock.json` are generated
outputs and must never be edited by hand. The current version is deliberately a
development version and carries no release or compatibility promise.

The canonical CLI, project staging, and automatic runtime bridge require
Python 3.11 or newer.

The content digest is SHA-256 over newline-delimited canonical JSON records,
sorted by canonical source path. Each record binds path, file type, mode and
content SHA-256. Inputs are `manifest.schema.json`, the generated
`manifest.json`, and every declared payload file. The lock is excluded from its
own digest by this rule, then binds the complete ordered input records.
Canonical metadata is required to be a regular `0644` file before generation;
installed schema, manifest, lock and install metadata are checked against their
actual type and mode during verification.

An incompatible manifest shape increments `schema_version`. A development
bundle content change regenerates the manifest and lock without implying a
release. Release versioning and compatibility policy belong to a later
milestone.

The bootstrap installer has no production or user-home mode. Installation
requires an explicit existing system-temporary root and an explicit existing
target beneath it. The installed read-only `verify` and `version` surfaces are
foundation contracts, not a production doctor.

Evidence output must resolve outside the source, temporary installation and
protected roots. Temporary installs are fully removed before the final
protected-state snapshot, and the evidence file is published only after every
terminal invariant passes.

The development bundle also installs a separate `gkd-task` executable, its
standard-library `gkd_task` package, and strict task schemas. It owns canonical
task state, planning and authorization gates, portable worktree resolution,
offer/claim transactions, lifecycle doctor and trusted fixed-tree acceptance.
The foundation `gkd-bundle` command surface remains unchanged.

`gkd-task bootstrap` requires an explicit fetched full base SHA, canonical
repository identity, independent candidate path and reviewed three-document
planning package. Runtime attachments, one-time capabilities, envelopes, claim
receipts, locks and journals stay outside tracked task data. A claim receipt is
bound to the exact claim commit and committed transaction postimages before
delivery or trusted acceptance can proceed. Delivery first commits exactly one
canonical `tasks/<task>/delivery.md`; `gkd-task deliver` then binds its path,
content digest and document commit to the final state commit. Candidate-facing claim and
activation commands, and the default library path without a trusted provider,
remain fail-closed.

The M2-A payload additionally defines three fixed custom-agent role TOMLs,
minimal role context manifests, hard-rule subsets, five progressive-disclosure
workflow Skills, route and wait schemas, and a trusted-main workflow activation
provider. This is not same-user process isolation and does not add signing,
daemon, IPC, or key infrastructure.

The M2-C payload promotes project staging to supported `gkd-role` surfaces and
the runtime bridge to the main-role-only `TrustedMainRuntimeBridge` library
interface. Public `gkd-role automatic-*` commands fail closed. `project-stage` renders the exact parent
Skill, executor role/config and executor Skills from one pinned bundle into an
explicit non-production Git project; `project-verify` checks its byte inventory
and digests before use. The bridge binds the six-gate automatic route decision
to offer, envelope, one exact direct `gkd_executor` spawn, activation, claim and
recovery. It never exposes the capability or raw agent/thread identity in main
output. The claim retains the immutable execution bundle digest, while delivery
requires a separately generated candidate output bundle digest.

The task state v2 extension adds trusted fixed-head rejection/rework without
rewriting a delivered attempt. `gkd-task rework` requires a clean synchronized
main context, an exact clean candidate and live PR snapshot, an independent
rejected review with findings, and the original claim/activation receipts. It
revokes the consumed offer, preserves the old claim, delivery, bundle and review
digests, increments the epoch, and returns to authorized planning. Executors
remain stopped after delivery and cannot reject, accept, or resume themselves.

Manual remains the default. Automatic routing is operational only from a
verified project staging rooted at an accepted bundle and through the
trusted-main bridge after the accepted M2-B one-hour wait gate. This development
surface does not install production `~/.codex`, modify a consumer repository,
or imply M3 completion.
