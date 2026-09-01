# Trusted Main Delivery Facade

## Implementation

- Implementation head: `718d78ddee2428ae4a8099389672f4723c4c3611`
- Candidate output bundle digest: `6ac9bf17cb6f860646787be335d61a26c3b0268ef9ce85b9c90109c1487f0cea`
- Result manifest digest: `5002966cc84a1b134d1b77047bb3208b1f489c57246c33c44251a16a90f83fa0`
- Verifier result digest: `a37e2722c85394057ab42d30f7bdc4bf067a5d4cf420687696954bb273dd5143`
- Delivery evidence digest: `b7919956edefbcd71f02739f01ac97749611ab5b108b33f2cc181cf9718bd724`

## Verification

- `scripts/gkd-verify --base-sha 6f088c819cf5c203404ad031ac2de1aec7c6d702`: exit 0, 429 tests passed (Python 3.9.6).
- `tests.task_core.test_lifecycle.LifecycleContracts.test_offer_commits_only_capability_digest`: exit 0 after repeated runs with a capability-safe `git grep` argument boundary.
- Fixed-tree automatic-delivery artifact validation: exit 0.
- `git diff --check`: exit 0.

The executor stops at fixed-head delivery. Acceptance, merge, cleanup, and archive remain outside this execution boundary.
