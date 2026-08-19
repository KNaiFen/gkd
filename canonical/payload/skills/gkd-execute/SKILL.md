---
name: gkd-execute
description: Execute one activated and claimed canonical GKD task in its registered worktree through fixed-head delivery; never accept or merge it.
---

# GKD Execute

1. Require the exact worktree, task path, envelope, trusted activation, claim, route-decision digest, and execution bundle/role/config digests supplied by main.
2. Run `gkd-task status` and `doctor` before editing. Stop on any mismatch; do not repair coordination records by hand.
3. Implement only the approved requirements and plan. Preserve unrelated changes and external authorization boundaries.
4. Use the repository's declared verification contract. Keep generated evidence bound to the exact implementation head and free of capabilities, runtime identities, prompts, transcripts, credentials, and machine paths.
5. Generate the candidate output bundle and report its digest separately; never replace the execution bundle digest of the in-flight claim. Pass the output digest to `gkd-task deliver --candidate-output-bundle-digest`.
6. Commit and push the task branch, update its existing PR when authorized, write delivery facts, and stop at the fixed head.

Do not accept, merge, archive, clean up, start another task, enable automatic routing, or delegate an implementation chain.
