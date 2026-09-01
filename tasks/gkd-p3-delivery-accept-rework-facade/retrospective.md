# P3 Retrospective

## Expected

The trusted-main facade derives delivery paths and digests, CI repository/policy, and acceptance/rework facts while retaining fixed-head, policy, independent-review and explicit-merge gates.

## Deviations and repairs

- The first fixed-head CI run exposed a pre-existing flaky contract test: a URL-safe capability beginning with `-` was passed to `git grep` without an option boundary and returned 129. The test now passes `--` before the pattern; the change is interpreter-independent and the full 429-test verifier passes.
- One host handoff used a non-canonical spawned task name and was rejected before claim; the offer was revoked and a fresh epoch used. A later acceptor invocation initially omitted the final SHA character and was rejected with `EXPECTED_HEAD_INVALID`; the exact 40-character head was then used without replaying the invalid attempt.
- Two executor attempts exceeded the normal wait budget. They were stopped without reusing their claims; the already committed test repair was retained, a fresh lifecycle was created, and delivery completed with a new claim and receipts.

## Result

P3 merged successfully at fixed head `2e25b8ce9d2f30b6051da5c8e1bad04acb1fcea9`. The workflow guarantees were preserved, but the host still manually supplied spawn acknowledgement and review JSON in this run; reducing those remaining hand-written surfaces is deferred to P4/P5.
