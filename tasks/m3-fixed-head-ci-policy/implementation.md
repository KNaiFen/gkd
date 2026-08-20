# GKD-M3-A Implementation Notes

## Internal Design

- Add a focused policy module that loads `.gkd/policy.json`, validates a shipped schema-equivalent strict contract, normalizes supported GitHub origin forms, and returns one repository/check policy record.
- Add a focused monitor module with an injected clock/sleeper and narrow GitHub observation adapter. Keep policy parsing, origin validation, observation parsing, terminal classification, and polling separately testable without introducing a service or background daemon.
- Expose one installed CLI that writes canonical terminal JSON and stable path-free errors. Update `gkd-ci-monitor` to invoke only that interface and to treat the result as terminal fact rather than hand-parsing GitHub output.
- Add one repository verifier entry shared by local verification and GitHub Actions. Keep test selection explicit and standard-library-only; do not infer package managers or add dependencies.
- Keep GKD repository identity/check names in `.gkd/policy.json`, the workflow, fixtures, and task evidence. Canonical library defaults remain repository-neutral.

## Execution Details

- Begin with installed `gkd-task status` and live `doctor`, then inspect current canonical bundle/source inventory, existing adapter/error helpers, Skill contract, and retained test runners before editing.
- Add failing policy/origin and monitor state-machine tests first, including head drift, missing/ambiguous checks, terminal failure, timeout, pagination, adapter errors, and no-write assertions.
- Add the versioned verifier and workflow only after their check contract is fixed by repository policy; ensure the workflow and policy names match byte-for-byte.
- Run the repository-approved verifier from the explicit task base SHA, generate M3-A evidence twice in disjoint temporary roots, compare bytes, verify protected surfaces, and regenerate manifest/lock only through canonical bundle tooling.
- Push one task branch, create or update one PR, observe its exact fixed-head CI through the in-scope monitor where trustworthy during execution, repair only M3-A failures, and deliver the final head with a separate candidate output bundle digest.
- Stop without accepting, merging, archiving, cleaning up, starting M3-B, changing project staging, or installing the candidate bundle into production.
