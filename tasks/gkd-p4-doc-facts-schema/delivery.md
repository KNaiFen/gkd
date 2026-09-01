# Trusted Main Delivery Facade

## Implementation

- Implementation head: `a381088db2cc3a681b7992eade71e8459ccbf5ed`
- Candidate output bundle digest: `6756ec25479ea14500f99239291431baa2d940db95585c35172c3a0fc6ab90c4`
- Result manifest digest: `590d43c863b69a6015866d91b8c4718d312030993632aeacc2524632a1167a92`
- Verifier result digest: `8329735f5289bd5b498bd329dd5cac7653c3a1b4530f8ee402273771f5057fca`
- Delivery evidence digest: `99467333e2f872e9f78fb51f2ce903f5063c3ea6ade9fc505d2c5b20623d2504`

## Verification

- `scripts/gkd-verify --base-sha b2dc172b496d1abe309af93f92e7babcd89e6244`: exit 0, 434 tests passed.
- P4 document-facts focused tests: 5 tests passed.
- Fixed-tree automatic-delivery artifact validation: performed by `gkd-task deliver`.
- `git diff --check`: exit 0.

The executor stops at fixed-head delivery. Acceptance, merge, cleanup, and archive remain outside this execution boundary.
