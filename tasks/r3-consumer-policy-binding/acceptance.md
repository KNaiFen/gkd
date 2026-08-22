# GKD-R3 Acceptance

## Fixed Candidate

- Base: `d277a8c43747853359094b0bb1538dee0d00a708`
- PR: `KNaiFen/gkd#27`
- Candidate head: `42104c47d1dd74f3d0cb7133261d8bd358c86a27`
- Squash merge: `b54d69b52c9b71d3e6ff7b3c8eb2793319ede7ba`

## Independent Checks

- `scripts/gkd-verify --base-sha d277a8c43747853359094b0bb1538dee0d00a708` passed all 424 tests at the fixed candidate head.
- The installed `gkd-ci-monitor` observed PR #27 at that exact head with required check `GKD Verify` successful and returned `ALL_REQUIRED_CHECKS_SUCCESSFUL`.
- Independent read-only review found no verified blocking issue. Its only reported schema concern was checked against the fixed head: the policy binding definition already has `additionalProperties: false`, matching the runtime validator.
- The final GitHub snapshot confirmed the same head, base `main`, open state, and clean merge state before the exact-head squash merge.

## Exception Boundary

This first-consumer policy binding task used the approved manual bootstrap exception. No automatic activation or claim was attempted, and no claim, delivery, activation, receipt, or release evidence was created or reconstructed.

## Result

The policy/origin binding chain is accepted on main. The resulting bundle is not yet released; AIO adoption must wait for a separate release upgrade and isolated project restage.
