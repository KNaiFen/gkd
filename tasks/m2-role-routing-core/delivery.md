# GKD-M2-A Delivery

## Outcome

- Outcome: `blocked`
- Scope: fixed custom roles, role context, activation/claim binding, manual-default routing, wait-state contract, canonical Skills, and temporary-home migration only
- Fixed base: `839974fbcd9114e5a5ad3b8fa1d4c58e68cb90ea`
- Synchronized main registration: `9cb03736c0a904014443d5d37167e66ba4baa0f6`
- Registration merge commit: `79f17208da2a70bafa0d2216d84b8919dc7c8291`
- Initial planning head: `51fee63a8b600df4f94aa042ea42ef09e3b73986`
- Implementation/evidence commit: `79e576b92f72b40f109f3fbd3f79e0380efa2cad`
- PR: [KNaiFen/gkd#6](https://github.com/KNaiFen/gkd/pull/6)
- Bundle version: `0.0.0-dev.0`
- Bundle content digest: `943301005912c05bb137d6c44a597e4569e05e9f0e738adaec4a8b675f654649`
- M2 evidence digest: `efe08577c4eabfb91938d2d93473ed142ded4bbe4f651c591a8d830624fbec8c`
- Evidence file SHA-256: `8cae003ad6179e0e28dec396524a5bf6d5de7288444d62fa7b251b0055de9c75`

The implementation is complete for the approved M2-A surface, but the
allowed short host handshake did not establish trusted custom-role activation.
The result is therefore deliberately `blocked`, not `role_routing_core_ready`.

## Fixed Role And Migration Facts

- Roles: `gkd_executor`, `gkd_acceptor`, `gkd_ci_reviewer`.
- Role source digest: `ccc0d756780bd4091797b63c5e1d09ecf7a51aacc55b8d902a790e435138aed5`.
- Hard-rule digest: `7ec55402138ea389afeaa26be68e724384d2a320f64b36e3369089b04ecd2a87`.
- Role digests: executor `7eeca24f18113f1c58d8cf7a712d431e790f721d5dba8cd0706cdfefe1033d16`, acceptor `b2392f4a78ae9774920a100cc4d5fbdca0424c906c194a7f8545156b15481532`, CI reviewer `8f3dfbe5b8b3cc1e596acd38dd0a9016f222858b5a585e50b4f8825e39785177`.
- Config digests: executor `10c0675808974609242280367f2e7aea07e61dd839a1ec2e244d53a9b6c74e3e`, acceptor `75f0326e0e8f07ba54655fbb90130b5497814c30f6a0307457772d8d7432b57f`, CI reviewer `e0acef621cfdc01cd64e1df3a85d695b8f5fbcb752e62c667ab4bc41501dd8b6`.
- Skill digests: `gkd-accept` `656d2fa58bc681767c6a2cab147b6184b33864e7c8cacd4a909fc702ef5c45e3`; `gkd-ci-monitor` `45589e31a888437774b67c9c20be2ab4075c48bbb9de918f8ad7c068c82dc7a0`; `gkd-execute` `d7d61e528d5d32f67ea69152193ecaaef7a2aaa6ac4ff12972c866f312806524`; `gkd-local-verify` `3ec80b83782c7e1ff69d7fb72e6fb1665c6a5add66d97c19dd235908c33d6ad3`; `gkd-main` `7c24cd74a1b572b7677f255580f4df2ec3221a39aa2310a4dbef6f3dc1e1d14e`.
- Context digests: executor `64b701cd7ac23a42082ad6aecccc3d7114df73a1b15044d9d49be2e90e16b6df`, acceptor `01f16b8188b3617830afaebb63317ad7dc4cb399f9e10c95a0f2aa32fc67cc25`, CI reviewer `cc5e44abc2fa172e5c4eeb5c681a76d593b3090b7227263909f0adafa18d237c`.
- Two isolated installs matched: 49 files, migration plan digest `bb7ecbc47a5f16063b6a6a29d5c3985a4fd1be8c081318a0c4d1e362b6821496`, inventory digest `67f6b438a883675abe8bf39ba4a39328c4edfc05a620caba7c24e6d6dc0e5dd2`, and migration surface digest `cd740202a620e1997f124d9d4ef9faad2f40a46cd9946695d627f0ba78159205`.

## Verification

| Contract | Result |
| --- | ---: |
| M2-A role/routing suite | 51/51 |
| M1 task-core | 104/104 |
| Foundation | 53/53 |
| Watcher core | 47/47 |
| Watcher live-negative | 15/15 |

The two M2 evidence generations were byte-identical. The historical
four-scenario live probe was not run. No dependency was installed, no large
build was run, and no real one-hour wait was run.

Production protected surface: 2289 entries, digest
`1fd465b9f0a65d9542e922dddab7df75595caf4530d4988c6db26f12f40d0117`, unchanged
before/after. AIO planning surface: 8 entries, digest
`21c4d0c64f9ceacfc0e18a38084422982bb6f2134ce57b316e5f2cb9d1f26b58`, unchanged
before/after. No production `~/.codex`, AIO, global AGENTS, settings, Secrets,
runner, tag, Release, or consumer-repository write occurred.

## Handshake Boundary

The one permitted isolated attempt exited 0 and observed only
`thread.started`, `turn.started`, `item.completed`, and `turn.completed`, with
one agent identity and no child or parent terminal observation. It observed a
custom-role reference but did not prove custom-role activation. The minimized
machine evidence is `evidence/m2-role-routing-core/role-handshake.json` with
digest `6f83e0ddb724aacb386eb9f072389ca3430fd35b6bf1053f9802d76c0cfca7b5`.
Agent self-report, candidate files, fixture output, and conversation text were
not promoted to trusted role evidence.

Automatic route evidence remains `manual_only` with refusal
`AUTOMATIC_ROUTE_GATES_INCOMPLETE` and failed gate `waitGateReady`. M2-B,
production installation, automatic routing, milestone 3, acceptance, and
merge remain outside this delivery.

## GitHub Facts

At the time of implementation delivery, PR #6 was open, Draft, based on
`main`, with head `79e576b92f72b40f109f3fbd3f79e0380efa2cad`. Its check list was
empty (`required_checks_not_configured_bootstrap`); no CI success is claimed.
The final fixed head is the delivery commit pushed by this task and is reported
from both local `HEAD` and `origin/task/m2-role-routing-core` in the handoff.
