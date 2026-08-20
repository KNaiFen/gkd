# GKD-M2-G Implementation Notes

## Internal Design

- Change the private task-name helper to accept validated task and offer/epoch context, normalize to host-safe ASCII, bound length and append a collision-resistant attempt digest.
- Use the same helper in `prepare` and `claim` expected-spawn reconstruction.
- Define a strict normalized terminal-result contract and a trusted bridge method that checks current implementing state/claim/offer plus exact agent/task/session/role/config/bundle/route facts before constructing one in-memory reclaim observation.
- Reuse `TaskService.reclaim` for the atomic transition and replay prevention; keep all candidate/public evidence paths unavailable.

## Execution Details

- Start with installed status/doctor and inspect bridge, activation, waiting, reclaim, rework, schemas, Skills and verifier routing.
- Add failing old-code tests for duplicate attempt names and unavailable trusted terminal reclaim before implementation.
- Cover wrong/stale/replayed/active terminal facts and byte-unchanged failures, then run the full repository verifier and two disjoint evidence generations.
- Regenerate canonical manifest/lock only through bundle tooling, maintain one PR, deliver with immutable accepted execution bundle and separate candidate output digest, then stop before acceptance, merge, cleanup, M3, production or AIO work.
