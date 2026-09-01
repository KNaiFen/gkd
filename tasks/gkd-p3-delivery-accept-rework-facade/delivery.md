# Trusted Main Delivery Facade

## Implementation

- Implementation head: `9390508da2da6b0d74146c1e285a7c607469f53f`
- Candidate output bundle digest: `6ac9bf17cb6f860646787be335d61a26c3b0268ef9ce85b9c90109c1487f0cea`
- Result manifest digest: `f682206b32bf77c1210c51613bcc75180efde98488b4e16ffc24011b9366f9ba`
- Verifier result digest: `4acbb1179e96e926e69a1a15abbf75e40496d2d78afe06923ebb103178bba7e3`
- Delivery evidence digest: `6ac4ccad2bfcd6af7dd45c75c4d1ef06ac36bb9089d19492679751c76fa09874`

## Verification

- `scripts/gkd-verify --base-sha 6f088c819cf5c203404ad031ac2de1aec7c6d702`: exit 0, 429 tests passed (Python 3.9.6).
- `tests.task_core.test_lifecycle.LifecycleContracts.test_offer_commits_only_capability_digest`: exit 0 after repeated runs with a capability-safe `git grep` argument boundary.
- Fixed-tree automatic-delivery artifact validation: exit 0.
- `git diff --check`: exit 0.

The executor stops at fixed-head delivery. Acceptance, merge, cleanup, and archive remain outside this execution boundary.
