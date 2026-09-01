# Trusted Main Delivery Facade

## Implementation

- Implementation head: `f49c76350116b40bd6b15ec71cd9597361fef6c8`
- Candidate output bundle digest: `0beb23c6f203f199adf6bc3efa82b618c3af8d5709581ae7203f015ab26fc12f`
- Result manifest digest: `53304ca593562e79b266af6ce6058cf4ba249b82d235b976874f985bf7e71366`
- Verifier result digest: `b07792fea2716ddc9863fca9b909a1c640be7d096f603a48ef42b1b5faa78d60`
- Delivery evidence digest: `1baef329de83f19b3d64572c99dc4a6d45cfded5ad881709aaba56b8998f928e`

## Verification

- `scripts/gkd-verify --base-sha b2dc172b496d1abe309af93f92e7babcd89e6244`: exit 0, 437 tests passed.
- P4 document-facts focused tests: 7 tests passed.
- Fixed-tree automatic-delivery artifact validation: performed by `gkd-task deliver`.
- `git diff --check`: exit 0.

The executor stops at fixed-head delivery. Acceptance, merge, cleanup, and archive remain outside this execution boundary.
