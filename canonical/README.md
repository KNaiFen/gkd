# Canonical development bundle

`canonical/` is the only bundle source root. `source.toml` is the reviewed
developer declaration; `manifest.json` and `manifest.lock.json` are generated
outputs and must never be edited by hand. The current `0.1.5` bundle is a stable
release candidate whose exact source, bundle, evidence, assets, and provenance
remain bound until trusted-main promotion.

The canonical CLI, project staging, and automatic runtime bridge support
Python 3.9 or newer. TOML parsing uses the standard library on Python 3.11+
and the bundled, MIT-licensed Tomli 2.0.1 compatibility parser on Python 3.9.

The content digest is SHA-256 over newline-delimited canonical JSON records,
sorted by canonical source path. Each record binds path, file type, mode and
content SHA-256. Inputs are `manifest.schema.json`, the generated
`manifest.json`, and every declared payload file. The lock is excluded from its
own digest by this rule, then binds the complete ordered input records.
Canonical metadata is required to be a regular `0644` file before generation;
installed schema, manifest, lock and install metadata are checked against their
actual type and mode during verification.

An incompatible manifest shape increments `schema_version`. Every bundle
content change regenerates the manifest and lock; release promotion only accepts
one already-built asset set bound to one exact source SHA.

The bootstrap installer has no production or user-home mode. Installation
requires an explicit existing system-temporary root and an explicit existing
target beneath it. The installed read-only `verify` and `version` surfaces are
foundation contracts, not a production doctor.

The separate `gkd-role production-migration-*` commands are the only explicit
production-home migration surface. They stage the bounded GKD roles, Skills and
managed config block, preserve a private path-relative recovery record until
terminal verification, and expose plan, apply, doctor, rollback and recovery
results without configuration contents or an absolute home path. The older
temporary `migration-*` commands remain production-forbidden.
Its doctor certifies only that bounded transaction and explicitly reports
`globalAgentsPolicy: outside_scope`; it neither reads, writes, nor certifies
the user-specific global `AGENTS.md` policy reserved for P2.

Evidence output must resolve outside the source, temporary installation and
protected roots. Temporary installs are fully removed before the final
protected-state snapshot, and the evidence file is published only after every
terminal invariant passes.

The development bundle also installs a separate `gkd-task` executable, its
standard-library `gkd_task` package, and strict task schemas. It owns canonical
task state, planning and authorization gates, portable worktree resolution,
offer/claim transactions, lifecycle doctor and trusted fixed-tree acceptance.
The foundation `gkd-bundle` command surface remains unchanged.

The repository verifier keeps its default invocation and scope list. With an
explicit `--results-dir`, it runs each scope once and writes a versioned,
path-free canonical result manifest plus one result per scope. Evidence runners
may consume that directory with `--canonical-results`; they re-check the
current fixed head, base ancestry, environment, test IDs/statuses and digests
before running their own protected-surface, temporary-root and output checks.

Trusted acceptance uses the installed `gkd-github-acceptance` executable as its
GitHub REST adapter. It returns canonical newline-delimited snapshots, maps a
merged pull request to its immutable PR head, and issues only exact-head squash
merge requests. An adapter exit status of `75` leaves reconciliation to the
trusted `gkd-task accept` path; executor self-tests never perform a real merge.

`gkd-task bootstrap` requires an explicit fetched full base SHA, canonical
repository identity, independent candidate path and reviewed three-document
planning package. Runtime attachments, one-time capabilities, envelopes, claim
receipts, locks and journals stay outside tracked task data. A claim receipt is
bound to the exact claim commit and committed transaction postimages before
delivery or trusted acceptance can proceed. `gkd-task planning-refresh` is a
planning-only CAS transition that rebinds all three reviewed document digests.
Automatic delivery places canonical verifier results, delivery evidence, and
the `tasks/<task>/result-manifest.json` sidecar in the implementation commit;
the sidecar does not contain the implementation SHA. It instead binds task
identity, base SHA, candidate bundle digest, and digests recomputed from the
fixed-tree artifact files. The immediately following commit contains only
`tasks/<task>/delivery.md`, and `gkd-task deliver` derives that implementation
head from the delivery-document parent before writing the final state commit.
Candidate-facing claim and
activation commands, and the default library path without a trusted provider,
remain fail-closed.

The M2-A payload additionally defines three fixed custom-agent role TOMLs,
minimal role context manifests, hard-rule subsets, seven progressive-disclosure
workflow Skills, route and wait schemas, and a trusted-main workflow activation
provider. This is not same-user process isolation and does not add signing,
daemon, IPC, or key infrastructure.

The M2-C payload promotes project staging to supported `gkd-role` surfaces and
the runtime bridge to the main-role-only `TrustedMainRuntimeBridge` library
interface. Public `gkd-role automatic-*` commands fail closed. `project-stage` renders the exact parent
Skill, executor role/config and executor Skills from one pinned bundle into an
explicit non-production Git project; `project-verify` checks its byte inventory
and digests before use. The bridge binds the six-gate automatic route decision
to offer, envelope, one exact direct `gkd_executor` spawn acknowledgement,
activation and claim. The acknowledgement contains only the returned exact task
name and the direct-call contract; configured model/effort/sandbox/runtime come
from the verified bundle and are not represented as host-effective observations.
A deterministic executor-attempt handle replaces raw agent/thread identity for
new attempts. The claim retains the immutable execution bundle digest, while
delivery requires a separately generated candidate output bundle digest.

The task state v2 extension adds trusted fixed-head rejection/rework without
rewriting a delivered attempt. `gkd-task rework` requires a clean synchronized
main context, an exact clean candidate and live PR snapshot, an independent
rejected review with findings, and the original claim/activation receipts. It
revokes the consumed offer, preserves the old claim, delivery, bundle and review
digests, increments the epoch, and returns to authorized planning. Executors
remain stopped after delivery and cannot reject, accept, or resume themselves.

Automatic spawn names are bounded to 128 ASCII characters and combine a
sanitized task prefix with a digest of the exact offer and epoch. The same offer
reconstructs the same name; a later automatic attempt cannot reuse it. Legacy
attempts retain trusted terminal reclaim under their recorded host-runtime
contract. New host-acknowledgement attempts do not reclaim from an unbound host
terminal event: trusted main blocks them for manual recovery. Candidate and
public CLI reclaim paths remain unavailable.

Manual remains the default. Automatic routing is operational only from a
verified project staging rooted at an accepted bundle and through the
trusted-main bridge after the accepted M2-B one-hour wait gate. This development
surface does not install production `~/.codex`, modify a consumer repository,
or imply completion of M4 or M5.

The M3-A payload adds a repository-neutral `gkd-ci-monitor`. It accepts only the
versioned `.gkd/policy.json` in an explicit Git checkout, binds its GitHub
repository and base branch to `origin`, then owns bounded read-only polling of
one explicit pull request and full expected head. Its single terminal JSON can
report success, required-check failure, head drift, timeout, or a stable error;
it never changes GitHub state or treats check success as acceptance. Repository
identity and check names remain in repository policy and workflow files, not in
the reusable payload.

The M3-C payload adds a repository-neutral review core with targeted, guided,
and recon entry points, explicit partial approval, resume, and recovery state.
The review adapter binds redacted facts for multiple repositories. The
`gkd-optimize-ci` and `gkd-review-remediation` Skills stop at recommendations
or remediation plans; they do not write runner, workflow, merge, rerun, or
repository settings state. The canonical bundle contains seven workflow
Skills, with role inventory, project staging, manifest, lock, and digests
bound to the same source declaration.

The M5 release-candidate surface provides deterministic L1 property evidence,
L2 read-only fake-GitHub subprocess evidence, and schema-bound L3 fresh-agent
forward-eval plus L4 sandbox-canary fixtures. `gkd-release canary-plan` only
emits the exact-SHA request for the release record's designated sandbox; it has
no GitHub writer. Trusted main alone runs the applicable live L3/L4 pass after
acceptance and validates the returned redacted result before promotion.
