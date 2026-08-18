# GKD-M1-A Delivery

## Outcome

- Outcome: `deterministic_task_core_ready`
- Scope: approved milestone 1 deterministic task core only
- Fixed base: `1335ac6a9a4dbb5c63570f5a02ba9e713705eebd`
- Synchronized main: `60ea9e9ef5c50290b2fa20e0b7888b59aa538599`
- Initial planning head: `b1e8b8d9f00ad53b68162c240134c3cd740d937a`
- Implementation/evidence commit: `1798b0f2c32571c803c399179c27090f94d21c0a`
- Draft PR: `KNaiFen/gkd#5`
- Development bundle version: `0.0.0-dev.0`
- Development content digest: `f29a594cd138a1b4e039b1411b953a6795f9b21a27b6086fdd540479c408faeb`
- Evidence digest: `164ab691af9fa1af9137386da2169aba3cd065793366815d53077557f69b3774`
- Evidence file SHA-256: `dcf0b28b109708a3ca134dda22883e2a2001dd046b2e2ee2d9983078bb9267fd`

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
- Added trusted fixed-tree acceptance with anchored authorization history,
  independent-review checks, synchronized-main and exact delivery-commit
  validation, repository-policy inputs, two pre-merge fact reads, one
  conditional exact-head merge call, and read-only reconciliation after an
  indeterminate response.

## Contract Matrix

| Group | Tests |
| --- | ---: |
| L1 planning and strict schema | 18 |
| L1 offer, claim and lifecycle | 17 |
| L1 transaction and recovery | 8 |
| L2 bootstrap and packaging | 13 |
| L2 concurrent subprocess claim | 1 |
| L2 fixed-head acceptance/fake GitHub | 17 |
| L2 locator and migration | 12 |
| Source mutation guards | 9 |
| **Task-core total** | **95** |

Stable contract ID digest:
`ad139dcffe775c42ebddd50d23c4f3579da7984a9b8156910313e5f5e24c0c16`.

## Validation

The task-core runner was executed twice with different clean system temporary
fixture roots and disjoint outputs:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=canonical/payload/lib:. python3 tests/task_core/run_contracts.py --output "$GKD_RUN_A_OUTPUT" --temporary-root "$GKD_RUN_A_FIXTURES" --protected-root "$GKD_PROTECTED_ROOT"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=canonical/payload/lib:. python3 tests/task_core/run_contracts.py --output "$GKD_RUN_B_OUTPUT" --temporary-root "$GKD_RUN_B_FIXTURES" --protected-root "$GKD_PROTECTED_ROOT"
cmp -s "$GKD_RUN_A_OUTPUT" "$GKD_RUN_B_OUTPUT"
```

Both runs passed 95 tests, left their fixture roots empty, and produced
byte-identical evidence with file SHA-256
`dcf0b28b109708a3ca134dda22883e2a2001dd046b2e2ee2d9983078bb9267fd`.

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

- Before the final push, PR #5 was open, Draft, mergeable, based on `main`, and
  still pointed to the planning head.
- GitHub reported no checks on the task branch and `main` returned HTTP 404 for
  branch protection. This is recorded as
  `required_checks_not_configured_bootstrap`, not CI success.
- The execution session must still push the delivery record, update the PR body,
  mark it ready, verify the exact remote 40-character head, and stop for
  independent acceptance.

## Deviations And Residual Risks

- No material plan deviation occurred.
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
