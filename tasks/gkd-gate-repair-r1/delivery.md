# GKD-GATE-REPAIR-R1 Delivery

## Fixed Facts

- Base SHA: `9a04e3f26fba71452a65e69bd380577cb3dc47ee`
- Implementation head: `4a462b38d4cd811b34e9ec93f8c4ee4b3899e9ba`
- Result-manifest commit: `626d0c68c218fa732bf624032b9bd2d25e484a18`
- Claim ID: `c75385229f711a8048a58d15a15618db09996c15938bca0f47db31ea77f0a814`
- Execution bundle digest: `06095243b2199672243b559e0af2798fb9e051e33281775b98bc68c8b16ac48a`
- Candidate output bundle digest: `4ff46ced7a1c38cbaab198c0cb873809ef9cfbba24d912dc133b2b307224d3fd`

## Gate Repair

- Lifecycle history now records a persistent `logicalOrder`; modern states validate it as a contiguous sequence, while legacy histories without the field remain readable through their revision order.
- `gkd-task planning-refresh` is the only CAS-protected path that rebinds planning document digests. It operates only in `planning`; later phases still fail closed on document drift.
- Automatic delivery requires the canonical `result-manifest.json` bound to this task, base, implementation head, claim, execution bundle, candidate bundle, verifier scope digests, and its own manifest digest.
- The task schema expected-set, source declaration, generated manifest, and lock include `result-manifest.schema.json` before delivery.

## Verification

- `scripts/gkd-verify --base-sha 9a04e3f26fba71452a65e69bd380577cb3dc47ee --results-dir <isolated-root>/results` passed 436 tests across 11 scopes.
- Canonical verifier results digest: `cbc0829abcf9810b67962cdc14bc32322ca3eeb0cd79833e0b343348140279bb`.
- Result manifest digest/file SHA-256: `88f24408175aaf371957edebac0e04dfe47273f20fa8a68aa1658d2adf296a03` / `ed2292ab4c5dc3bcfdd64ed7f78c708a0970b79b1d207f9eccccd4edc83f2725`.

## Boundary

- No production installation, AIO change, GitHub settings or Secrets change, tag, Release, acceptance, merge, archive, or cleanup was performed.
- This document is the final pre-delivery commit. The following canonical delivery transition is the only permitted subsequent commit.
