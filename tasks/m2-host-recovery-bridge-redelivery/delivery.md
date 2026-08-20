# GKD-M2-I-R 交付

## 结果

- Outcome: `automatic_host_recovery_bridge_ready`
- Fixed base: `c2ae190f96ca321b1b5fe83035f8c67b4c20a42c`
- Claim head: `4e2b890f827bf0f326c40b685e205dd4a4d3562b`
- Claim ID: `27b5371609496bb21b60d42d9668bae6a2d86797c3d4ed0aaae6e1c5ced577d7`
- Implementation commit: `81970e92fc83ea03e491785577f9260aabf9847e`
- Evidence commit: `3ab88e4bd8ddd2a389c72b42001aa4ae5e48eae7`
- PR: [KNaiFen/gkd#16](https://github.com/KNaiFen/gkd/pull/16)，Open/CLEAN
- Checks: 未配置，事实为 `required_checks_not_configured_bootstrap`

本交付把既有 M2-I trusted-host recovery bridge 移植到当前 M2-J main，保留
delivery document sequencing。只解决了 `canonical/manifest.lock.json` 的机械冲突，
未实现 M3、修改生产或 AIO、修改 GitHub 设置、验收、合并或清理。

## 实现

- 保留 M2-I 的 attempt-aware ASCII bounded task name 和 trusted-main terminal reclaim
  行为；新的 offer/epoch 不复用旧 task name。
- 保留 terminal、task、offer、claim、role/config/bundle/route 绑定及 fail-closed
  失败路径；candidate-facing claim/reclaim 和 public automatic CLI 仍不可用。
- 保留 M2-J 的 delivery 顺序：implementation/evidence 提交之后，单独提交本文件，
  再调用 `gkd-task deliver` 绑定本文件路径和 digest。

## Digests

- Accepted execution bundle: `d17c5f5259591ab1dbd0b1148786fc5126dc858bdf577172c0df7c2a29f1c95b`
- Candidate output bundle: `1983f05b64860510bfb1af661e5458a6c7b660632479a33af46c27d35ff188d4`
- M2-I evidence digest: `be0a8b80229d832bf21d1d27e243a57a9832170940fbf28dfcb959b1816c29ea`
- Evidence file SHA-256: `6ad650b4aa40c081c5d0fc5a401b122d728ce78569de52d8ff7a40ea1587b790`
- Executor role/config/route: `8ffae4b3401343b662314626eae1e9edff4120efbf42f737f73853cbed1b7158` /
  `10c0675808974609242280367f2e7aea07e61dd839a1ec2e244d53a9b6c74e3e` /
  `e13b68cf50d0f7193751620c5e528affe357c2af2fcae5d9a8b1d129719e1853`

Execution bundle remains the immutable claim identity; candidate output bundle is the
separate digest passed to `gkd-task deliver`.

## 验证

已按 `gkd-local-verify` 原样运行：

`PYTHONDONTWRITEBYTECODE=1 scripts/gkd-verify --base-sha c2ae190f96ca321b1b5fe83035f8c67b4c20a42c`

终态为 `pass`：task-core 126/126、runtime-bridge 37/37、role-routing 70/70、
foundation 53/53、watchdog 47/47、watchdog-live-negative 15/15。未安装依赖。

M2-I deterministic evidence 两次各运行 3/3 focused contracts，输出逐字节一致；
candidate bundle 通过 `gkd-bundle` 隔离 install、verify、version，版本为
`0.0.0-dev.0`，安装清单 56 项，digest 与上文一致。未运行历史 live probe 或真实
一小时等待。

## 停止边界

本文件在 `gkd-task deliver` 前单独提交；随后仅由 `gkd-task deliver` 生成最终协调
提交。executor 停在该任务的 fixed head，不验收、不合并、不归档、不清理 worktree
或分支、不启动其他任务或 M3、不修改生产 `~/.codex`、AIO、Secrets、runner、tag
或 Release。
