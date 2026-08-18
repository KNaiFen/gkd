# GKD-M1-A Delivery

## Outcome

- Outcome: `deterministic_task_core_ready`
- Scope: approved milestone 1 deterministic task core only
- Fixed base: `1335ac6a9a4dbb5c63570f5a02ba9e713705eebd`
- Synchronized main: `60ea9e9ef5c50290b2fa20e0b7888b59aa538599`
- Initial planning head: `b1e8b8d9f00ad53b68162c240134c3cd740d937a`
- Implementation/evidence commit: `0548eb52ead7191733c32129241168c2e7035a9f`
- PR: `KNaiFen/gkd#5`
- Development bundle version: `0.0.0-dev.0`
- Development content digest: `fc96a10cb82b628bd14280e4e878417a3fbc7a1d560fac5a61bb7abe7f3c3024`
- Evidence digest: `3f119831c41a18536318b621f21f13d8d18d115fce77e3fb97870a0148395569`
- Evidence file SHA-256: `7df2d35021ba32eb93d1ebd84d3920e7ac4ee281a68e7c4da935cfcfa306bb65`

This bootstrap task did not create or hand-edit a task `task.json`, offer,
claim, authorization, journal, or evidence result for itself. It did not use
the candidate `gkd-task` to claim, deliver, accept, or merge PR #5.

## Delivered Behavior

- Added a separately installed `gkd-task` executable, standard-library
  `gkd_task` package, and strict task/offer/authorization/runtime schemas while
  preserving the existing `gkd-bundle` command surface.
- Added reviewed-package parsing, separate requirements/plan/implementation
  facts, material versus full-document digests, explicit approval and
  implementation/action authorization, and material-change invalidation.
- Added explicit fetched-base bootstrap, candidate-only active truth, verified
  Git identity, four-layer portable locator, machine-local attachment, static,
  live and historical doctor, and idempotent active/archive v1 migration.
- Added exact head/revision CAS, bounded non-stale lock acquisition, prepared
  preimage/postimage journals, exact-file staging and recovery, and fail-closed
  `transaction_in_doubt` freeze evidence.
- Added one-time hash-only offer capability, 0600 runtime envelopes, first-writer
  claim, epoch fencing, revoke/reclaim, block/resume and delivery. Installed
  claim remains fail-closed until milestone 2 supplies a trusted runtime
  evidence provider.
- Added a machine-local claim receipt bound to the exact claim commit, committed
  transaction journal and task/offer postimages. Delivery repairs a missing
  receipt only from that committed journal; trusted acceptance refuses a
  candidate-history-only claim before any GitHub call.
- Made offer capability and v1 attachment publication recoverable with tracked
  state: runtime writes fail before commit, migration attachment changes occur
  only inside the locked builder after exact head/revision CAS, pre-commit
  failures restore prior runtime bytes, and post-commit recovery retains only
  runtime state proven to match the committed offer/migration.
- Enforced the full lifecycle field matrix, cross-record IDs/epochs and history
  relationships, and rejected explicit symlink candidate roots before path
  resolution in locator, service and acceptance paths.
- Added trusted fixed-tree acceptance with anchored authorization history,
  independent-review checks, synchronized-main and exact delivery-commit
  validation, repository-policy inputs, two pre-merge fact reads, one
  conditional exact-head merge call, and read-only reconciliation after an
  indeterminate response.

## Contract Matrix

| Group | Tests |
| --- | ---: |
| L1 planning and strict schema | 19 |
| L1 offer, claim and lifecycle | 20 |
| L1 transaction and recovery | 8 |
| L2 bootstrap and packaging | 13 |
| L2 concurrent subprocess claim | 1 |
| L2 fixed-head acceptance/fake GitHub | 19 |
| L2 locator and migration | 15 |
| Source mutation guards | 9 |
| **Task-core total** | **104** |

Stable contract ID digest:
`14ceed6137a1aef32cc2e2704552320500f4f28996a8ec75f2e7a3aea626c9f4`.

## Validation

The task-core runner was executed twice with different clean system temporary
fixture roots and disjoint outputs:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=canonical/payload/lib:. python3 tests/task_core/run_contracts.py --output "$GKD_RUN_A_OUTPUT" --temporary-root "$GKD_RUN_A_FIXTURES" --protected-root "$GKD_PROTECTED_ROOT"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=canonical/payload/lib:. python3 tests/task_core/run_contracts.py --output "$GKD_RUN_B_OUTPUT" --temporary-root "$GKD_RUN_B_FIXTURES" --protected-root "$GKD_PROTECTED_ROOT"
cmp -s "$GKD_RUN_A_OUTPUT" "$GKD_RUN_B_OUTPUT"
```

Both runs passed 104 tests, left their fixture roots empty, and produced
byte-identical evidence with file SHA-256
`7df2d35021ba32eb93d1ebd84d3920e7ac4ee281a68e7c4da935cfcfa306bb65`.

Retained regressions and repository checks:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=canonical/payload/lib:. python3 tests/foundation/run_contracts.py --output "$GKD_REGRESSION_ROOT/foundation.json"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /opt/homebrew/bin/python3 tests/watchdog/run_contracts.py --output "$GKD_REGRESSION_ROOT/watcher-core.json"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /opt/homebrew/bin/python3 -m unittest discover -s tests/watchdog/live -p 'live_test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 canonical/payload/bin/gkd-bundle generate --source-root canonical
git diff --check
```

Results: foundation 53/53, watcher core 47/47, watcher live-negative 15/15.
The four-scenario live probe was not run. No dependency installation, large
build, production-home write, sandbox action, paid API or consumer-repository
change occurred.

## Packaging And Protection

- The generated manifest declares 20 payload files across the foundation CLI,
  foundation library, task CLI, task library and task schemas.
- Two independent temporary installs produced the same version, content digest
  and 24-file installed inventory, and exercised the installed `gkd-task`.
- The path-free protected-surface snapshot was identical before implementation,
  during both evidence runs and after final regression: digest
  `5b4fa82c2594782ca332dfc587e277e909e099b78b6719ba3292791fadb17b46`,
  2287 entries.
- Source, installed payload, task-core evidence and tracked task records were
  scanned for machine paths, plaintext capabilities, credential-shaped values,
  secrets, undeclared payload and consumer-specific policy; no violation was
  found.

## GitHub Reality

- Independent acceptance of ready PR #5 at
  `c35ac55fd299196a463bc31e8ff0f98ef37c3858` did not pass. No merge occurred;
  the four blocking findings covered missing external claim receipt,
  runtime/tracked transaction ordering, lifecycle invariants and explicit
  symlink candidate handling. This delivery contains their remediation and
  requires a new fixed-head independent acceptance.
- Independent acceptance of the renewed ready head
  `f34152ddbe79c3b9ff12c6e2e97121c34fd8fffa` also did not pass and did not
  merge. It confirmed the other three findings closed but found stale migration
  CAS could leave a newly written attachment. The attachment mutation now runs
  only after manager CAS, with stale-head/stale-revision byte-preservation
  regression coverage.
- GitHub reported no checks on the task branch and `main` returned HTTP 404 for
  branch protection. This is recorded as
  `required_checks_not_configured_bootstrap`, not CI success.
- PR #5 is Ready. The execution session stops after publishing this delivery
  record and verifying the exact remote 40-character head; independent
  acceptance and merge remain external to this session.

## Deviations And Residual Risks

- No material plan deviation occurred. The first delivered head was rejected by
  independent acceptance and the four blocking security findings were repaired
  in `fee072bf6849d87ffd6a6323ea75a81af3504831` before this renewed handoff.
- The renewed head was rejected for the remaining migration CAS/runtime ordering
  case. It was repaired and re-evidenced in
  `0548eb52ead7191733c32129241168c2e7035a9f` before this handoff.
- Runtime/session role evidence is intentionally a provider seam with an
  internal fixture provider; the installed CLI refuses claim without a later
  trusted provider. This preserves the milestone 2 boundary.
- GitHub behavior was proven with fake adapters only; this task did not perform
  a live merge and cannot accept or merge itself.
- Repository required checks and branch protection are not configured. The
  independent acceptor must preserve that bootstrap fact and must not describe
  it as a passing CI gate.
- Automatic routing, role readiness, one-hour waiting, CI monitor readiness,
  production installation, release readiness and consumer adoption remain
  unproven and out of scope.
