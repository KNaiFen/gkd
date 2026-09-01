# Trusted Main Delivery Facade

## Implementation

- Implementation head: `bdef49c35f7bd8c892386c6bc8d2703beec22892`
- Candidate output bundle digest: `6ac9bf17cb6f860646787be335d61a26c3b0268ef9ce85b9c90109c1487f0cea`
- Result manifest digest: `3a91289dc648d0f178e7b3ec9cca7d3324f7a308c1b557ea12b564a45e3da1ed`
- Verifier result digest: `4d763b3781829628ef9f1b623cbe611349e3e464810fc4e654d47e45776dcec5`
- Delivery evidence digest: `16776ff72b41399466d0b877497026ca804d4207f5c8eadca0158e398b9a6367`

## Verification

- `scripts/gkd-verify --base-sha 6f088c819cf5c203404ad031ac2de1aec7c6d702`: exit 0, 429 tests passed.
- `/usr/bin/python3 -B scripts/gkd-verify --base-sha 6f088c819cf5c203404ad031ac2de1aec7c6d702`: exit 0, 429 tests passed (Python 3.9.6).
- `/opt/homebrew/bin/python3.14 -B scripts/gkd-verify --base-sha 6f088c819cf5c203404ad031ac2de1aec7c6d702`: exit 0, 429 tests passed (Python 3.14.6).
- Fixed-tree automatic-delivery artifact validation: exit 0.
- `git diff --check`: exit 0.

The executor stops at fixed-head delivery. Acceptance, merge, cleanup, and archive remain outside this execution boundary.
