# GKD-O3 Retrospective

## What Worked

- A canonical result schema and consumer removed repeated execution while preserving complete test-ID binding and fail-closed behavior.
- The automatic bridge held fixed bundle/route/claim/delivery boundaries; executor, acceptor and trusted main remained separate.
- Independent acceptance reproduced the full verifier, negative cases, dual evidence and fixed-head CI before merge.

## Workflow Friction

- The first delivery had five implementation defects: EOF whitespace, missing `PYTHONPATH`, a missing `sys` import, a wrong rework variable name and incomplete test-ID binding. A second delivery exposed an undefined watchdog helper. Each was rejected at fixed head and repaired through a new canonical epoch.
- The initial full verifier invocation exceeded the single tool command window after seven scopes; later evidence used the repository runner and complete 433/433 summary rather than treating a partial command as proof.
- One executor first presented the retired epoch claim and received `CLAIM_MISMATCH`; the current epoch claim was required before delivery.
- The executor did not create the PR, so trusted main pushed the fixed candidate head to the existing task branch before acceptance.

## Follow-up

- O4 should move watcher/probe execution out of the default verifier while retaining an explicit historical lane and regression coverage.
- Add preflight checks for imports, result-ID completeness and command/runtime limits before executor delivery; keep all rework as new epochs.

