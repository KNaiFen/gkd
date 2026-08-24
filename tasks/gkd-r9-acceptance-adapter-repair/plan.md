# GKD Acceptance Adapter Delivery Repair Plan

## Goal

提供受信 GitHub adapter 并固定 executor delivery 调用顺序。

## User Decisions

- R9 使用已发布 `v0.1.4` bundle 的 automatic route；不重用 R7/R8 claim 或候选代码。

## Behavior And Defaults

- merge 仅使用 squash 和 `--match-head-commit`；adapter 不输出 credential 或 gh stderr。

## Scope

- 实现 requirements 所列 adapter、contracts、Skill/文档和 manifest 更新。

## Non-Goals

- 不改 AIO、production、GitHub settings、release 或 task core state schema。

## Acceptance Criteria

- 满足 requirements 的所有条件。

## Compatibility

- 保持现有 `gkd-task accept` adapter protocol 和 delivery state schema。

## Security And Data

- 不执行真实 merge 自检；假 gh 覆盖所有测试写入路径。

## Migration

- 无迁移；历史 blocked attempt 只保留事实。

## Public Interfaces

- bundle 增加 GitHub acceptance adapter executable。

## Execution Route

- automatic，完整 six-gate/bridge，唯一 exact `gkd_executor` 且 `fork_turns="none"`。

## External Side Effects

- 允许任务 PR、CI repair 与无阻塞 fixed-head merge；禁止 tag、Release、AIO 与 production。

## Action Mode

- `implement_and_merge_on_acceptance`；允许 `ci_repair`、`commit`、`conditional_merge`、`pr_update`、`push`、`ready_for_review`。

## Implementation Notes

- delivery document commit 是 `gkd-task deliver` 的 expected head；CLI 是 final state 的唯一 writer。
