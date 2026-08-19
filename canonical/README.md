# Canonical development bundle

`canonical/` is the only bundle source root. `source.toml` is the reviewed
developer declaration; `manifest.json` and `manifest.lock.json` are generated
outputs and must never be edited by hand. The current version is deliberately a
development version and carries no release or compatibility promise.

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
delivery or trusted acceptance can proceed. Installed claim routing remains
fail-closed until a later milestone provides a trusted runtime evidence
provider; this development component does not enable automatic execution.

The M2-A payload additionally defines three fixed custom-agent role TOMLs,
minimal role context manifests, hard-rule subsets, five progressive-disclosure
workflow Skills, route and wait schemas, and a trusted-main workflow activation
provider. Candidate-facing CLI and default library claim/recovery remain
fail-closed without that provider. This is not same-user process isolation and
does not add signing, daemon, IPC, or key infrastructure. The default route is
manual; automatic routing has six explicit gates and remains manual-only until
the separate M2-B fresh-runtime wait gate proves the required one-hour tool
behavior. The authorized production-environment handshake proved one exact
`gkd_executor` child and both terminal events, so M2-A evidence is
`role_routing_core_ready` while automatic routing remains disabled.
