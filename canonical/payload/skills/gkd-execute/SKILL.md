---
name: gkd-execute
description: Execute one activated and claimed canonical GKD task in its registered worktree through fixed-head delivery; never accept or merge it.
---

# GKD Execute

1. Require the exact worktree, task path, envelope, trusted activation, claim, route-decision digest, execution bundle/role/config digests, and `executionContext` supplied by main.
2. Before editing, execute `executionContext.statusArgv` and `executionContext.doctorArgv` exactly. Do not infer a candidate root, task path, runtime root, or CLI from the current working directory; stop on any mismatch and do not repair coordination records by hand.
3. Implement only the approved requirements and plan. Preserve unrelated changes and external authorization boundaries.
4. Use the repository's declared verification contract. Keep generated evidence bound to the exact implementation head and free of capabilities, runtime identities, prompts, transcripts, credentials, and machine paths.
5. Generate the candidate output bundle and report its digest separately; never replace the execution bundle digest of the in-flight claim. For automatic delivery, put canonical verifier results, delivery evidence, and `tasks/<task>/result-manifest.json` in the implementation commit; the sidecar must not contain an implementation SHA. Commit `tasks/<task>/delivery.md` alone immediately after it, then invoke `gkd-task deliver` with that document head, paths/digest, candidate-output bundle digest, verifier-results path, and evidence path. The CLI derives the fixed implementation tree and alone creates the final state commit.
6. The delivery transition creates the final coordination commit and must be the only commit after the delivery document. Commit and push the task branch, update its existing PR when authorized, record the final fixed head, and stop. Delivery is writerless and frozen; any later rejection requires trusted rework plus a new offer, activation, and claim before implementation may resume.

Do not accept, merge, archive, clean up, start another task, enable automatic routing, or delegate an implementation chain.
