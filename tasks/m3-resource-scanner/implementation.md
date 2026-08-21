# GKD-M3-B Implementation

## Internal Design

Keep artifact/resource classification, runner/billing recommendation, and scanner mechanics in reusable portable modules. Repository-specific policy and fixtures must remain data inputs. Scanner output must be canonical and redacted before it leaves the boundary.

## Execution Details

Add schemas, CLI/library contracts, fake providers, positive/negative/mutation tests, deterministic evidence and manifest/lock declarations. Run only `scripts/gkd-verify --base-sha <full-base-sha>`. Commit implementation/evidence, then commit only the canonical delivery document and invoke `gkd-task deliver` with its exact digest.
