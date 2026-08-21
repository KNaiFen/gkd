---
name: gkd-optimize-ci
description: Recommend a resource-aware CI plan from explicit repository facts without writing runner or workflow state.
---

# GKD Optimize CI

1. Require explicit repository, visibility, runner, policy, billing, and resource facts. Treat unknown or unverified facts as unknown.
2. Use the shared CI recommendation interface with `speed-first`, `balanced`, or `cost-aware`; keep the recommendation bound to the supplied facts and digest.
3. Prefer the resource-constrained preset when facts are incomplete. Peak-disk violations and unknown build bounds remain blocked; cleanup does not change that result.
4. Treat runtime prices as unverified unless the source, currency, value, and check time are explicitly verified. Do not invent prices or billing claims.
5. Stop at a plan or recommendation. Do not dispatch, rerun, merge, change workflow settings, install dependencies, or create large local artifacts.
