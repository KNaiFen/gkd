# GKD-M3-C Requirements

## Goal

完成 M3-C 冻结范围：共享 review core、`gkd-optimize-ci`、`gkd-review-remediation` 与七个 Skill 的 bundle 收口，并提供消费仓库 adapter schema/fixture。

## User Decisions

- Continue automatic execution through M3, M4 and M5 with one exact accepted `gkd_executor` route.
- Keep M3-C limited to shared review core, the two new Skills, and the seven-Skill bundle closeout; do not implement M4/M5.
- Do not modify production `~/.codex`, AIO, paid runners, Secrets, GitHub settings, tags or Releases.

## Scope

- 共享审查状态、targeted/guided/recon 入口、部分批准、恢复和确定性机器事实。
- `gkd-optimize-ci` 的资源/runner/policy/费用建议调用，以及 `gkd-review-remediation` 的审查整改流程。
- 将两个新 Skill 与既有五个 Skill 纳入 canonical manifest、安装、role inventory 和验证合同。
- 多仓库 adapter schema 与脱敏 fixture；不创建 AIO 专用 adapter。

## Non-Goals

- M3-A policy/monitor、M3-B resource/scanner 语义变更。
- M4 验收/finalization/release 机制或 M5 专属验证/release candidate。
- 生产 `~/.codex`、AIO、Secrets、付费 runner、计划外 GitHub 设置、tag 或 Release。

## Acceptance Criteria

- review core 的 targeted/guided/recon、模糊推荐、partial approval、resume/recovery 正负合同与 mutation 通过。
- 两个 Skill 可从 accepted bundle 发现，七 Skill 名称唯一，manifest/lock/inventory/digest 完整一致。
- adapter schema 支持多 repo 且 fixture 脱敏；不回显 credential-shaped 数据。
- 固定 base SHA 的 local verifier 与 policy-backed `GKD Verify` fixed-head CI 通过，证据两次逐字节一致。
