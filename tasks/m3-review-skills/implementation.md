# GKD-M3-C Implementation

## Internal Design

Keep review state and recommendation logic in reusable portable modules. Repository-specific policy, adapter inputs and fixtures remain data. All externally visible findings are canonical and redacted.

## Execution Details

- Implement only the approved M3-C requirements and plan in the registered worktree.
- Keep the bundle generic and repository-neutral; do not add AIO-specific adapters.
- Use the installed `gkd-execute` and `gkd-local-verify` contracts from the accepted bundle.
- Deliver a clean fixed head, PR, CI result, evidence, and delivery document; stop for trusted-main acceptance.
