---
name: gkd-local-verify
description: Run the repository-approved local verification contract for one GKD change from an explicit full base SHA without inventing extra checks.
---

# GKD Local Verify

1. Read the repository `AGENTS.md` and task execution contract.
2. Require the recorded lowercase full base SHA and verify it is an ancestor of the current head.
3. Run only the repository's versioned local verification entry, `scripts/gkd-verify --base-sha <full-sha>`. Do not infer a package manager, dependency install, build, server, or large artifact command.
4. Report the exact commands, exit status, checked scope, and tests. Keep cloud-owned or unrun gates explicit.
5. Stop if the declared verifier is missing or insufficient; change the repository contract through an approved task instead of bypassing it.
