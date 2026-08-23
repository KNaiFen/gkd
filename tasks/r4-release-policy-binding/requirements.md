# GKD-R4 Policy Binding Release Requirements

## Goal

Publish the accepted R3 consumer-policy binding as stable `v0.1.3`, then make its exact released bundle available for isolated project restage before any AIO adoption work.

## User Decisions

- The user explicitly authorized continuation after R3 closeout.
- `v0.1.2` is the latest published bundle and is used only as the accepted bootstrap runtime. R3 changed the policy-bound task contract, so its own release candidate must use the documented manual bootstrap exception rather than fabricate automatic lifecycle evidence.
- This is a stable patch release `0.1.3`; AIO must continue to consume only a verified published asset.

## Scope

- Update the canonical source declaration from `0.1.2` to `0.1.3` and regenerate canonical manifest and lock metadata.
- Update only the release-candidate fixtures, evidence, and tests required to bind the R3 source as a `0.1.3` candidate.
- Produce deterministic candidate evidence and run the complete repository verifier from the registered base.
- Deliver one GKD PR for independent fixed-head acceptance. Trusted main may perform the separately verified post-merge release, tag, Release asset, and isolated project restage only after acceptance.

## Non-Goals

- No change to R3 policy semantics, route gates, host facts, task lifecycle, production installation, AIO code, AIO workflows, GitHub settings, Secrets, or paid runners.
- No tag, GitHub Release, live sandbox canary, production mutation, or AIO write during candidate execution.
- No rewrite of historical release records, tags, Releases, assets, task runtime state, claims, deliveries, activations, or receipts.

## Acceptance Criteria

1. Canonical `0.1.3` source, manifest, lock, release-candidate record, and derived `v0.1.3` tag input are internally consistent and distinct from `v0.1.2`.
2. Existing stable-version validation, post-merge L3/L4 bindings, and historical `v0.1.0` through `v0.1.2` records remain compatible.
3. Focused release contracts and the complete repository verifier pass; evidence generated from two clean temporary roots is byte-identical.
4. Candidate execution stops at one fixed PR head with no fabricated automatic lifecycle state and no tag, Release, production, or AIO side effect.
5. After independent fixed-head acceptance, trusted main can run the existing release gates and restage only the exact published `v0.1.3` asset before AIO inventory begins.
