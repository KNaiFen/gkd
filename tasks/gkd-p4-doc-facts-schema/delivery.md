# Trusted Main Delivery Facade

## Implementation

- Implementation head: `d0fa656`
- Candidate output bundle digest: `6756ec25479ea14500f99239291431baa2d940db95585c35172c3a0fc6ab90c4`
- Result manifest digest: `07a802addb15a3ead7300f08c89fe71c5bc29ad095bfb6427014419c8352dbd9`
- Verifier result digest: `8329735f5289bd5b498bd329dd5cac7653c3a1b4530f8ee402273771f5057fca`
- Delivery evidence digest: `31934a16960affa5c23e9016aa3bdfd8680a10ad8862d5eeb91cce76029d4ab2`

## Verification

- `scripts/gkd-verify --base-sha b2dc172b496d1abe309af93f92e7babcd89e6244`: exit 0, 434 tests passed.
- P4 document-facts focused tests: 5 tests passed.
- Fixed-tree automatic-delivery artifact validation: pending `gkd-task deliver` fixed-tree check.
- `git diff --check`: exit 0.

The executor stops at fixed-head delivery. Acceptance, merge, cleanup, and archive remain outside this execution boundary.
