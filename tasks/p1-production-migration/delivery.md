# GKD-P1 Delivery

## Candidate

- Implementation commit: `38c2b71ca743ea9edbe5f06404e28e8ca87d01e3`
- Candidate output bundle: `68188dcaeb98d93902b435c98784e242090ed18828e9d96a8dee735244f7d1ef`
- Bundle version: `0.1.1`

## Verification

- `scripts/gkd-verify --base-sha f060e8342c5c74beacf4e6e429aea54207699b61` passed all 418 tests across 11 repository scopes.
- The production migration contracts cover successful plan/apply/doctor, both legacy CI reviewer filenames, injected interruption, explicit rollback and recovery, pre-existing recovery, malformed or symlinked inputs, staged-content tampering, declared-surface containment, and path-free/config-free machine output.

## Boundary

This candidate adds no production-home mutation, AIO change, tag, Release, GitHub setting, Secret, or paid-runner action. Its production doctor reports `globalAgentsPolicy: outside_scope` and does not read, write, or certify the separate P2 global `AGENTS.md` policy migration. The legacy temporary `migration-*` interfaces retain their production-root rejection behavior.
