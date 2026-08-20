# GKD-M2-D Implementation Notes

## Internal Design

- Factor the read-only fixed candidate and receipt checks shared by acceptance/rework without changing acceptance semantics.
- Represent each rejected attempt with exact task/repository/PR/head, review/finding digests, prior offer/claim/delivery/route/bundle fields, epoch and timestamp. Validate the complete phase matrix and history relationships.
- Perform rejection through the existing task lock/CAS/journal machinery. Revoke the tracked offer, retire the active attempt, increment epoch and return to authorized planning in one transaction.
- Expose the operation only through trusted-main fixed-tree inputs and an actor-role gate; candidate/default execution paths remain fail-closed in normal workflow usage.
- Add a standard-library verifier that explicitly enumerates current short contract scopes and can be extended by M3-A.

## Execution Details

- Start with installed task status/doctor and inspect exact acceptance, service/model/runtime/transaction code and schemas before editing.
- Add failing tests for all rejection gates, concurrent/replay behavior, recovery, old receipt/capability reuse, new automatic claim/redelivery and normal acceptance after repair.
- Run the versioned verifier from fixed base, generate evidence twice in disjoint system-temporary roots, compare bytes, verify protected surfaces, and regenerate manifest/lock only with canonical tooling.
- Push one task PR and deliver its exact head with a separate candidate output bundle digest. Do not edit PR #8, accept/merge, clean up, stage/install the candidate, or start M3-A repair.
