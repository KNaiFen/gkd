# GKD-M2-C Implementation Notes

## Internal Design

- Factor project materialization from the handshake fixture into canonical role code that renders exact config/role/Skill bytes from the fixed catalog, records owned-file preimages, and verifies/removes only owned output.
- Put trusted startup orchestration in the gkd-main context, not the executor context. It should validate a small direct spawn-result schema, create one activation through `TrustedMainActivationAuthority`, inject its one-time provider into `TaskService.claim`, and return only canonical claim/handoff facts.
- Extend automatic offer records so the route decision digest, six gates, execution bundle, role and config remain fixed through activation, claim, wait and delivery. Keep candidate output digest separate.
- Reuse existing transaction, lock, CAS, journal and recovery paths. Do not introduce a second task state authority or ad hoc JSON writer.
- Preserve public candidate fail-closed behavior and the simplified same-user threat model.

## Execution Details

- Start from the fixed main base recorded by bootstrap and establish clean baseline task-core, role-routing, foundation, watcher-core and live-negative results without historical live probes.
- Read the exact staging fixture, role catalog, activation authority, service claim/delivery code, schemas and canonical source inventory before editing. Check current official Codex project custom-agent/Skill configuration only where format stability matters.
- Implement failing L1/L2 tests first for project conflicts, candidate cleanliness, exact spawn binding, route decision bypass, execution/candidate digest separation, replay, expiry, CAS, recovery and candidate-facing denial.
- Generate canonical evidence twice in disjoint temporary roots with fixed clock/nonce and verify byte equality, cleanup and protected production/AIO digests.
- Regenerate manifest/lock only with repository bundle tooling. Do not hand-edit generated JSON.
- Deliver `automatic_runtime_bridge_ready` or `blocked`, with exact base/head, bundle and evidence digests, test totals, PR/check facts and remaining conditions. Stop before acceptance, merge, staging a real fresh main, or starting M3.
