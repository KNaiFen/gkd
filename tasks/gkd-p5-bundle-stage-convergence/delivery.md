# Trusted Main Delivery Facade

## Implementation

- Implementation head: `b644354d0e94d15cdeefe2d2827329d80c4e0a69`
- Candidate output bundle digest: `c7a517ac260f3b27187e396d9c24742c5a45d0d496d3a7208907f06f44862bdf`
- Result manifest digest: `8ff89a3c4efaa9b7dae2e1b9a3b6341221476e63d6f54798585f92632b046280`
- Verifier result digest: `6e204675891a2e91dd92d5e3bd66050a7696d7193a37d8c8655c31d889e7dacb`
- Delivery evidence digest: `03e78bdab112ad4ee34d09d7fed823720c2027e0e86f16c406ae4a87a8703aa7`

## Verification

- `scripts/gkd-verify --base-sha f13258a0a1eaab1634b397f302dc17e382d0dcf1`: exit 0, 439 tests passed.
- P5 stage facade focused tests: 2 tests passed.
- Fixed-tree automatic-delivery artifact validation: performed by `gkd-task deliver`.
- `git diff --check`: exit 0.

The executor stops at fixed-head delivery. Acceptance, merge, cleanup, and archive remain outside this execution boundary.
