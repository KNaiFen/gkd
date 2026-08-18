# GKD-M0-A Delivery

## Outcome

- Outcome: `canonical_foundation_ready`
- Implementation/evidence commit: `f2cf2b7ab2706c41a3e80dfaf191e8fdac7a28cd`
- Pull request: `KNaiFen/gkd#4`
- Fixed base: `88325398c7bb0b6559927a707634e39016726695`
- Synced main at execution start: `c18534a72e8c56922edbfd7fe410ec2eb7a6824d`
- Required checks: `required_checks_not_configured_bootstrap`

This outcome establishes only the milestone 0 bootstrap foundation. It is not
production-ready, release-ready, auto-ready, or evidence that D2 is supported.

## Delivered behavior

- `canonical/` is the single development bundle source root. `source.toml` is
  the reviewed declaration; the CLI deterministically generates the manifest
  and lock.
- The digest binds canonical source path, type, mode and content. The lock is
  excluded from its own digest by an explicit rule and binds the ordered input
  records.
- The installer has no default target or production mode. It requires an
  explicit existing system-temporary root and a separate existing target below
  it, then rejects traversal, symlinks, undeclared or missing source files,
  digest drift and unknown target ownership.
- Read-only `verify` and `version` surfaces detect installed content, mode,
  type, missing, extra, symlink and directory drift. Repeat installation of an
  intact matching bundle is idempotent.
- Root `VISION.md` is the single long-term authority with exactly seven
  required sections. README and AGENTS link it without copying its content.
- Governance documentation separates VISION, decision, ADR, AGENTS,
  Skill/reference and repo policy. The Vision Alignment template is generated
  by the foundation CLI and explicitly cannot expand authorization.

## Machine evidence

- Development version: `0.0.0-dev.0`
- Content digest: `9be34162a4e4125f2f56d4d8148140e022f24cba46abbc56512ea0e8afb2a30f`
- Manifest SHA-256: `44fcf1c1b50fe032a0e89fee1686c60dd98daf811cb6abcd739275b573a4e497`
- Foundation evidence digest: `a4a458445be0b404891e84690fb9ec03c0c8a4616eec684f30b5cc6b54b8ac79`
- Foundation evidence file SHA-256: `ebcf229bb9aa2ed571330647de0c3ad46274ef343a08a67da26ce1340ede70ea`
- Foundation test-ID digest: `a260eb2770112a7d6f2a9ae409618318ee91510192e0a3df26f4dc3b625557af`
- Two independent clean evidence generations were byte-identical.
- Protected production-home snapshot: 2,287 entries; before and after digest
  both `5b4fa82c2594782ca332dfc587e277e909e099b78b6719ba3292791fadb17b46`.
- Evidence: `evidence/m0-canonical-foundation/foundation-evidence.json` and
  `evidence/m0-canonical-foundation/foundation-contracts.json`.

## Contract matrix

| Contract | Result | Evidence |
| --- | --- | --- |
| Manifest/lock schema, ordering, repeat generation | pass | Foundation contracts |
| Content, path and mode digest behavior | pass | Positive and mutation contracts |
| Missing, extra, traversal and source symlink rejection | pass | Negative contracts |
| Two temporary installs and repeat idempotence | pass | Machine evidence and contracts |
| Target content, mode, type, missing, extra and symlink drift | pass | Negative contracts |
| Production target default absent and temporary boundary enforced | pass | Mutation contract and machine evidence |
| Machine/path/project contamination rejection | pass | Negative contracts and final scan |
| VISION seven sections and volatile-detail rejection | pass | Governance mutation contracts |
| README/AGENTS links and documentation layering | pass | Governance contracts |
| M-1B regression | 47/47 pass | Hermetic/subprocess contracts |
| M-1C regression | 15/15 pass | Negative tests only |

Total short tests: 106 (`44 + 47 + 15`). The four-scenario M-1C live probe was
not run.

## Commands

```text
PYTHONDONTWRITEBYTECODE=1 python3 canonical/payload/bin/gkd-bundle generate --source-root canonical
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=canonical/payload/lib:. python3 tests/foundation/run_contracts.py --output evidence/m0-canonical-foundation/foundation-contracts.json
PYTHONDONTWRITEBYTECODE=1 python3 canonical/payload/bin/gkd-bundle evidence --source-root canonical --temporary-root <clean-system-temp-root> --protected-root <production-codex-home> --output <evidence-output>
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /opt/homebrew/bin/python3 tests/watchdog/run_contracts.py --output <temporary-output>
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /opt/homebrew/bin/python3 -m unittest discover -s tests/watchdog/live -p 'live_test_*.py' -v
git diff --check
```

The AIO-specific `gkd-local-verify` runner and task state CLI are absent from
this bootstrap repository, so they were not applicable and were not imitated.
The frozen task verification contract above was used directly. No dependency
installation, package-manager command, build, live canary, paid API, Rust,
Tauri, production installation, tag or release was run.

## Deviations and residual risks

- The current bundle deliberately contains only two real bootstrap components:
  the foundation CLI and library. Future Skills, roles and milestone components
  are neither declared nor claimed.
- GitHub required checks are not configured during bootstrap; the PR must not
  represent their absence as CI success.
- The temporary-only installer and verifier are not a production installer or
  full doctor. Production installation remains separately unauthorized.
- D2 remains `unsupported`; automatic execution remains disabled.
- The next task may be planned only after main completes independent fixed-head
  acceptance and merge. This execution session must not start M0-B or milestone
  1.
