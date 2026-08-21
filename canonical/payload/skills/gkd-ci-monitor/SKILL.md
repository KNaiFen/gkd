---
name: gkd-ci-monitor
description: Monitor one GitHub pull request at an explicit full head through the canonical repository policy and return one terminal machine result.
---

# GKD CI Monitor

Require an explicit repository identity, PR number, lowercase full expected head SHA, and versioned repository CI policy that matches the checkout origin.

Invoke installed `gkd-ci-monitor` once with the explicit checkout, repository, PR, expected head, `.gkd/policy.json`, timeout, and polling interval. The runner validates policy/origin/base consistency before each read-only GitHub observation, owns bounded polling, and returns exactly one versioned terminal JSON result.

Trust only that terminal result. Stop on `head_drift`, `failure`, `timeout`, or `error`; a `success` result proves only the policy-required checks at the exact head and is not acceptance. Do not hand-poll, rerun, dispatch, cancel, change PR metadata, accept, or merge.
