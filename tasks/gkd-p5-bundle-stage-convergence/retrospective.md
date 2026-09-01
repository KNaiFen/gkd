# P5 Retrospective

P5 added a trusted-main stage facade and a `gkd-main stage` CLI transition. The facade derives the verified bundle digest, owned target layout, inventory, and project policy, while retaining low-level bundle/project commands for diagnostics and legacy callers. The normal path now needs only an explicit non-production production-root and an optional `--refresh`; it no longer requires agents to hand-enter bundle digests, target file lists, or inventory JSON.

The implementation was delivered after an executor timeout path had already produced the implementation and delivery commits. Trusted main preserved the delivered fixed tree, independently verified it, and accepted it only after the exact-head CI result and independent review were available. This exposed an operational gap: automatic execution still depends on a host acknowledgement/sealed-argv handoff, so a missing host terminal binding must fail closed and requires a fresh lifecycle rather than retrying the old attempt.

The project stage was refreshed manually before execution because the accepted P4 bundle was not yet staged in the development project. This remains an explicit prerequisite for automatic routing, but the refresh itself is now CLI-derived and idempotent. Production and AIO boundaries were left untouched.
