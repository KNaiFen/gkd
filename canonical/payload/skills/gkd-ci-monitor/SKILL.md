---
name: gkd-ci-monitor
description: Monitor one GitHub pull request at an explicit full head through the canonical repository policy; fail closed while milestone 3 policy support is unavailable.
---

# GKD CI Monitor

Require an explicit repository identity, PR number, lowercase full expected head SHA, and versioned repository CI policy that matches the checkout origin.

The milestone 2 bundle does not yet implement generic GitHub policy discovery or fixed-head monitoring. Return `CI_POLICY_UNAVAILABLE_MILESTONE_3` without querying GitHub when that policy surface is absent. Do not reuse consumer-specific repositories, check names, scripts, or workflow paths.

When a later bundle supplies the policy-backed runner, trust its single terminal result. Do not hand-poll, rerun, dispatch, cancel, change PR metadata, merge, or treat CI success as acceptance.
