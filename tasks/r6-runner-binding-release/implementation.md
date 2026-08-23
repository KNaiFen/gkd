# GKD R6 Runner Binding Release Implementation

## Internal Design

- Version declaration drives generated metadata and existing release-core bindings.

## Execution Details

1. Update version and regenerate only required release metadata/evidence.
2. Run the versioned verifier and deliver one fixed PR head.
3. Stop before promotion.
