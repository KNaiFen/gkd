# GKD-M5-B Delivery

## Result

- Outcome: `post_merge_final_gate_ready`
- Fixed base: `3f0a60feaa724e37163d207678917f140312cfdc`
- Claim base head: `ab9b4061ece9848ea4270e91f7ccfeaddafdfe2a`
- Offer: `b72917fcfd6a665fee1102312d32fa266edddcdc2172fd3963cd75b549afe129`
- Envelope: `4de6496ab83ba2d6df82d062e6dcc7ef0c2129932de944147fb811fb9a96ef3e`
- Implementation/evidence commit: `670585505cd295c47153df60071a925f8d2db46b`
- Accepted execution bundle: `27470fc60cfa005a2784ac81f0aba07c4e50e2381bf057fe9b38aa8d016e1912`
- Candidate output bundle: `a312dedf754c8f027542e78e057f34f394ab18874b609c2701223874a080035b`
- Evidence digest: `299104db3cb30cbf9e8318aee104ba403d1a6b1f932acacd5236a49543353779`
- Evidence file SHA-256: `cbe9b0656f355f9fa2b1ef2623db41269302ee7bd481c8d348037235891eb455`

## Implementation

- `gkd_release` now provides a trusted-main post-merge boundary that derives a
  canonical, redacted L3 forward-evaluation record from one expected source SHA.
- The same boundary derives the L4 sandbox request, reads one exact `GKD Canary`
  result through the existing read-only GitHub adapter, and records only canonical
  source, branch, check, request, and digest facts.
- The final release record cross-binds the release candidate, L3 record, L4 request,
  observed check, and prebuilt asset provenance to one source SHA. The promotion
  input uses that same SHA for both tag and GitHub Release, without rebuilding assets.
- Deterministic contracts use the approved `github.com/KNaiFen/gkd-sandbox` input and
  a fake GitHub adapter. They reject substituted L3, L4, and asset source SHAs.

## Verification

Only the versioned verifier was used:

`scripts/gkd-verify --base-sha 3f0a60feaa724e37163d207678917f140312cfdc`

It passed `412/412`: M5 release candidate `13`, M4 finalization `9`, M3 CI policy
`29`, M3 resource scanner `14`, M3 review core `11`, task core `129`, role routing
`70`, runtime bridge `37`, foundation `53`, and watcher/live-negative `47`.

The M5-B evidence generator passed twice with the identical candidate bundle and
evidence digests above. It records no machine paths and did not run live L3/L4.

## Stop Boundary

This executor stops at fixed-head delivery. It did not run a real L3 forward eval or
L4 sandbox canary, create a tag or GitHub Release, accept, merge, archive, or clean
up. Production `/Users/knaifen/.codex`, AIO, Secrets, paid runners, and GitHub
settings were not modified.
