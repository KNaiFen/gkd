# GKD O8 Release Upgrade Compatibility Acceptance

## Fixed Head

- PR: `#53`
- Candidate fixed head: `a0a776f1e1cadbed90b553406ca49d615a10b97d`
- Canonical merge: `2dd8a433ac83721cd7b980a024e1e17950f1f52c`
- Review digest: `d918b83c6342efa36da2507773ac71bf1b9cd3e5a454939ccf6dd2a97513ef8c`
- Reviewer digest: `0eee701941359764846ccaac796f75d1ac90ba9dd4221c48c1516c54ee496a04`

## Result

Independent acceptance passed with no findings. `GKD Verify` completed successfully against the fixed head using relative `.gkd/policy.json`. Python 3.9.6 and Python 3.14.6 each passed the default/core verifier with 8 scopes and 408 tests, the historical watcher lane with 47 tests, and the release-upgrade matrix with 11 tests twice with byte-identical result and evidence. Candidate and squash merge tree are both `ab4342e7546618b4e00e3e8b78bedf010dc01251`.

The versioned catalog binds ten public legacy formats to one core read test, one core reject-or-restore test and their extended matrix cases. `release-upgrade/matrix` has its own strict canonical-result binding and remains outside default/core and historical/watcher. ADR-001 preserves the two release engines, their public CLI and record schemas; no engine extraction or merge occurred.

## Boundary

No production installation, AIO, GitHub settings/Secrets, runner, tag, Release, or published asset changed.
