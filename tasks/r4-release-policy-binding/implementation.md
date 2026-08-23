# GKD-R4 Policy Binding Release Implementation

## Internal Design

Treat the version declaration as the sole new release input. Existing release-core validation already derives the tag from a strict stable semantic version, so the implementation should update that declaration, regenerate generated metadata, and refresh only release evidence/fixtures that bind the candidate source and content digest.

## Execution Details

Work only in the registered candidate worktree. Run the repository-approved verifier from the exact base, commit the implementation and delivery document, push one PR, and stop at its full fixed head. Do not create tags, Releases, sandbox canaries, production or AIO changes, or manual substitutes for automatic lifecycle facts.
