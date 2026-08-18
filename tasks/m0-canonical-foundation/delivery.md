# GKD-M0-A Delivery

## Outcome

- Outcome: `canonical_foundation_ready`
- Implementation/evidence commit: `3bab17697735adcf85e1214d6580966a7e896f47`
- Pull request: `KNaiFen/gkd#4`
- Fixed base: `88325398c7bb0b6559927a707634e39016726695`
- Synced main for rework: `6902829c5be6683bdd39787a226bcab4b40f6a20`
- Superseded rejected head: `0f69a4ad34d095d70f6d5e5ed93569193ad75578`
- Required checks: `required_checks_not_configured_bootstrap`

This outcome establishes only the milestone 0 bootstrap foundation. It is not
production-ready, release-ready, auto-ready, or evidence that D2 is supported.

## Delivered behavior

- `canonical/` is the single development bundle source root. `source.toml` is
  the reviewed declaration; the CLI deterministically generates the manifest
  and lock.
- The digest binds canonical source path, type, mode and content. The lock is
  excluded from its own digest by an explicit rule and binds the ordered input
  records. Source schema, manifest and lock must be regular `0644` files;
  installed schema, manifest, lock and install record are checked using their
  actual type and mode.
- The installer has no default target or production mode. It requires an
  explicit existing system-temporary root and a separate existing target below
  it, then rejects traversal, symlinks, undeclared or missing source files,
  digest drift and unknown target ownership.
- Read-only `verify` and `version` surfaces detect installed content, mode,
  type, missing, extra, symlink and directory drift. Repeat installation of an
  intact matching bundle is idempotent.
- Evidence output resolves outside source, temporary installation and protected
  roots, including through symlinks. Temporary installs and staging residue
  must be gone before the final protected snapshot; only then can evidence be
  published.
- Generic contamination checks match complete absolute machine paths, not bare
  usernames or unrelated substrings. Repository-specific product phrases and
  path segments are enforced only by the final repository/evidence boundary.
- Root `VISION.md` is the single long-term authority with exactly seven
  required sections. README and AGENTS link it without copying its content.
- Governance documentation separates VISION, decision, ADR, AGENTS,
  Skill/reference and repo policy. The Vision Alignment template is generated
  by the foundation CLI and explicitly cannot expand authorization.

## Machine evidence

- Development version: `0.0.0-dev.0`
- Content digest: `0b8b2487640ff2c78360a18e7f24304f72a8e8c8b5cbd1317ef833c323726228`
- Manifest SHA-256: `44fcf1c1b50fe032a0e89fee1686c60dd98daf811cb6abcd739275b573a4e497`
- Foundation evidence digest: `ac463b216718f4a49a7d2dd89198fc83403afd2ecd4f83a690622d2f517fd494`
- Foundation evidence file SHA-256: `2f3785c8e47011b3e797f772bc0bb30412f37cd0cf75dfbba419f322302fd0af`
- Foundation test-ID digest: `f7dc7ae7f415e151266978d8fb031fe0879ac626581b40b4b6329116a35ba6f5`
- Two independent clean evidence generations were byte-identical.
- Protected production-home snapshot: 2,287 entries; before and after digest
  both `5b4fa82c2594782ca332dfc587e277e909e099b78b6719ba3292791fadb17b46`.
- Evidence: `evidence/m0-canonical-foundation/foundation-evidence.json` and
  `evidence/m0-canonical-foundation/foundation-contracts.json`.

## Contract matrix

| Contract | Result | Evidence |
| --- | --- | --- |
| Manifest/lock schema, ordering, repeat generation | pass | Foundation contracts |
| Content, path and payload/metadata mode digest behavior | pass | Positive and mutation contracts |
| Missing, extra, traversal and source symlink rejection | pass | Negative contracts |
| Two temporary installs and repeat idempotence | pass | Machine evidence and contracts |
| Target content, payload/metadata mode, type, missing, extra and symlink drift | pass | Negative contracts |
| Production target default absent and temporary boundary enforced | pass | Mutation contract and machine evidence |
| Machine paths rejected without username/substring false positives | pass | Cross-machine mutation contracts |
| Repository-specific product path/phrase rejection | pass | Evidence-boundary contracts and final scan |
| Output/protected/source/temp disjointness and symlink resolution | pass | Negative contracts |
| Cleanup before final protected snapshot and publication | pass | Mutation and ordering contracts |
| VISION seven sections and volatile-detail rejection | pass | Governance mutation contracts |
| README/AGENTS links and documentation layering | pass | Governance contracts |
| M-1B regression | 47/47 pass | Hermetic/subprocess contracts |
| M-1C regression | 15/15 pass | Negative tests only |

Total short tests: 115 (`53 + 47 + 15`). The four-scenario M-1C live probe was
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
- The first delivered head failed independent acceptance on three newly added
  counterexamples. The rework evidence includes those exact negative cases;
  the new PR head still requires a fresh independent acceptance pass.
- D2 remains `unsupported`; automatic execution remains disabled.
- The next task may be planned only after main completes independent fixed-head
  acceptance and merge. This execution session must not start M0-B or milestone
  1.
