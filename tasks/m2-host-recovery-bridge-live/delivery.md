# GKD-M2-I 交付

## 结果

- Outcome: `automatic_host_recovery_bridge_ready`
- Fixed base: `6b5d5b78a3c5f5cc98d0659167b5d3838d14f518`
- Claim head: `36338cd0d812727c7f5ae6fc35a0db8cc301becd`
- Implementation commit: `27cf3293d6cc37c4f19a0b96d934d4b6c079db01`
- `gkd-task deliver` head: `22a9275e706d4a1fc2b5b82a84a9afc58f82a320`
- Delivery revision: `5`
- PR: [KNaiFen/gkd#14](https://github.com/KNaiFen/gkd/pull/14)，Ready
- CI monitor: `CI_POLICY_UNAVAILABLE_MILESTONE_3`，本 session 未查询或重跑 CI

本交付只修复 automatic host task name 的 attempt 绑定和 trusted-main terminal
reclaim/recovery bridge。没有修改 M3-A、M2-E/F/G/H、生产 `~/.codex`、AIO、
Secrets、runner、GitHub settings、tag 或 Release；本 session 不验收、不合并、不清理。

## 实现

- `TrustedMainRuntimeBridge.prepare` 与 `claim` 共用同一确定性 helper。名称由
  sanitized task prefix 与 task/offer/epoch digest 组成，限定为最多 128 个 ASCII
  字符；同一 offer 稳定，新的 offer 或 epoch 不复用旧名称。
- trusted-main-only `reclaim_terminal` 严格校验 normalized terminal/missing result
  的 task、offer、claim、task name、agent/session、role/config/bundle/route 和
  terminal time，再以一次性内存 evidence provider 调用既有原子 reclaim 事务。
- candidate-facing `gkd-task` 与 public `gkd-role automatic-*` 入口保持
  `TRUSTED_ACTIVATION_BOUNDARY_UNAVAILABLE`；raw host result 不写入 runtime。
- 新增 bridge/reclaim positive、negative、mutation contracts、独立 deterministic
  evidence runner 与 canonical README 说明；manifest/lock 已由 bundle 工具生成。

## Digests

- Accepted execution bundle: `71c4b2d3562c2e5a6a784bf3436a7d5920cd00b3ad387f320a2563d4b5b88766`
- Candidate output bundle: `e807a31c0a32f51de6637e2b63add8088a608e8dd8900c2ffa34fffa26f4dc7b`
- Evidence digest: `719b85553548e3ae2ffff903ccde411ca6bc9ad3b1740bd6dd76837126f98ee1`
- Executor role/config/route: `880e1855cfdeb50ba890a3023c818cde377b9c6a71c230360154b79ecc16d680` /
  `10c0675808974609242280367f2e7aea07e61dd839a1ec2e244d53a9b6c74e3e` /
  `d59c534b01d1617b20b8086b0686bfb09d3ef9999982fd86910ca3402974c75d`

Execution bundle remains the immutable claim identity; candidate output bundle is the
separate digest passed to `gkd-task deliver`.

## 验证

`PATH=/opt/homebrew/bin:$PATH scripts/gkd-verify --base-sha
6b5d5b78a3c5f5cc98d0659167b5d3838d14f518` passed:

| Contract | Result |
| --- | ---: |
| Task core | 118/118 |
| Runtime bridge | 37/37 |
| Role routing | 70/70 |
| Foundation | 53/53 |
| Watchdog core | 47/47 |
| Watchdog live-negative | 15/15 |
| M2-I focused evidence generations | 3/3 + 3/3, byte-identical |
| M2-I mutation contracts | 7/7 |

No dependencies were installed, historical live probes and real one-hour waits were not
run, and protected production/AIO snapshots remained unchanged.

## 停止边界

Final delivery facts are bound to the pushed PR head after this document commit. The
executor stops before independent acceptance: no CI rerun, acceptance, merge, archive,
worktree/branch cleanup, M3 start, production installation or AIO change.
