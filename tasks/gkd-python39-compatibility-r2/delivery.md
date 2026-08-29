# GKD Python 3.9 Compatibility R2 Delivery

## Result

- Outcome: `python39_compatibility_ready`
- Fixed base: `f4bdab2ecad412dc42b6b85e8fc18c5162369d4c`
- Claim: `90d4c2ab1ee63b734485f0d49ea9593031be31a9e4f17fd2a3ae7a155330427d`
- Implementation head: `0f5b161ae010499388cde3fd362d56494e1ee873`
- Execution bundle digest: `06095243b2199672243b559e0af2798fb9e051e33281775b98bc68c8b16ac48a`
- Candidate output bundle digest: `d9ea5f423987812bc4dd259d0bd90c485bbf0e8fdfda6c6a0d31f3f5a4a3aaf7`
- Route decision digest: `c0f7bac431d1a84fb1d4d5c537ffb58e043ed0c5127bd3f4ec9363a2cb59f782`
- Python 3.9 canonical results digest: `5ccb3773cddc33595d9fa09433e7ea7058114d97966f22afea6ea7895c1299f9`

## Implementation

- Added an internal TOML facade that uses the standard library on Python
  3.11+ and the bundled, MIT-licensed Tomli 2.0.1 parser on Python 3.9.
- Replaced reachable strict `zip` and dataclass `slots` usage with Python 3.9
  compatible implementations while retaining unequal-length rejection.
- Updated payload imports, watcher/probe surfaces, CLI error classification,
  source manifest/lock, package inventory, tests, and minimum-version docs.
- Added fresh trusted bridge claim-to-CLI-deliver contracts. The positive path
  consumes canonical claim and activation receipts; claim receipt drift returns
  `CLAIM_RECEIPT_UNAVAILABLE` without a final lifecycle state.

## Verification

- System Python 3.9.6: complete fixed-head verifier passed 439 tests across 11
  scopes; canonical results are bound to the implementation head above.
- Development Python 3.14.6: the same complete verifier passed 439 tests.
- System Python 3.9 bundle generate/install/verify/version passed for 109 source
  files and 113 installed files. Development Python regenerated identical
  manifest and lock bytes.
- An isolated Git project passed system Python 3.9 `project-stage` and
  `project-verify`; its inventory digest was
  `ff9888ac55802944e72fa07da11a68ba7ac94bb47ab1f9bb4b438355f24c44af`.
- The applicable native probe ran under system Python 3.9 and retained the
  expected historical `native_insufficient` conclusion; output SHA-256 was
  `2c14f828c57927743bf2bdf1d1768bccfa64e36365eb6f5e8d402118f2463c7e`.
- `gkd-task status`, live `doctor`, and `git diff --check` passed. No dependency
  was installed and no production, AIO, GitHub settings, Secrets, runner, tag,
  Release, or published asset state changed.

## Stop Boundary

This document is committed alone before `gkd-task deliver`. The delivery
transition creates the only following coordination commit. The executor stops
at that fixed head and does not accept, merge, archive, clean up, or start a new
task.
