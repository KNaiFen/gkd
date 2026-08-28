# GKD-O4 Acceptance

## Result

- Outcome: `blocked`
- Initial PR: `#37`, fixed head `6ebf189ee2189a722c3e389b25a09f27c9360698`
- Retry PR: `#38`, fixed head `c3e492d736b089b1d10340269fd466e5cefe950c`
- Accepted merge: none

## Evidence

- Both candidates implemented the intended split: default verifier 386 tests/10 core scopes; historical lane 47 tests/1 scope; watcher/native coverage and host `HOST_CAPABILITY_UNAVAILABLE` remained fail-closed.
- Initial acceptance rejected EOF/document digest and result-manifest declaration drift. Canonical rework then exposed an implementing-state document digest deadlock; the old task was blocked with `immutable_requirements_document_digest`.
- Retry acceptance rejected lifecycle history timestamp regression (`claimedAt` `2026-08-29T00:00:00Z` after `deliveredAt` `2026-08-28T22:50:50Z`), causing trusted `status`/`doctor` and canonical rework to return `INVALID_TASK_STATE`. PR #38 `GKD Verify` ended in `REQUIRED_CHECK_FAILED`.

## Authority

Independent acceptors wrote canonical rejected reviews and did not merge either PR. Both task branches, candidate worktrees and runtimes were cleaned; no production, AIO, settings, Secrets, runner, tag or Release changed.
