# GKD O6 Delivery Pack Compatibility Delivery

## Implementation

- Implementation head: `88e291cf3734247247539e8b0dad2f62313108be`.
- The current producer remains schema-v1 and full-install. Its source bundle has content digest `fe1098fd1be01e8b59dd268b0ed45cc7b44217063e00e0a20afd0bf1c9b1014c`, 107 payload files, and 111 installed files.
- The default/core verifier remains the ten-scope contract, including resource scanner and review core.
- The trusted consumer strictly validates schema-v2 pack ownership, core and optional pack digests, the eight-scope core contract, `optional-ci-advice`, `optional-review-remediation`, and the combined optional profile. Unknown ownership, structural changes, content drift, and symbolic-link drift are rejected.

## Verification

- Python 3.9.6 full verifier: 411 tests, canonical results digest `af358dab82f82b7d3e2cedb56c5e857e30168d9a330b03e1b3ab8b4d796a35c3`.
- Python 3.14.6 full verifier: 411 tests, canonical results digest `3dc5c938d28181aacbe47638e67df8dfd7e7975a7ae6d88b7ac314753541df80`.
- Both interpreters completed bundle install and installed-bundle verification with the schema-v1 107/111 surface.
- The future consumer probe passed 9 contracts on each interpreter, covering v2 core, both optional lanes, their combined profile, and strict negative cases.

## Bound Artifacts

- Verifier result digest: `8fdb08dcdc1f94bcff250fb4a6dae0f4feecd4f9998e3b0b1b723e4a542745ff`.
- Delivery evidence digest: `cbf05b86bdf4694fa5bf4f16253091d5c92c39504138e523b0a416538ad945af`.
- Result manifest digest: `a4b48047563a4216653a8423cee223382df5a4fada6dee9bece47dddfa7eb29a`.

## Scope

No production installation, settings, credentials, runner configuration, release, or acceptance action was performed.
