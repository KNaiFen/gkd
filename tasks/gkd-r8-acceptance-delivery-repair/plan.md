# GKD Acceptance Adapter And Delivery Repair Plan

## Goal

修复 acceptance 的 GitHub host integration 与 executor delivery 使用边界，使后续 AIO task 不再依赖临时 adapter 或错误 CAS 参数。

## User Decisions

- R8 从 clean main 重新实现；R7 是已记录的 blocked attempt，不构成可合并候选。
- 本任务只产生一个标准 GKD PR，满足固定 head 验收前不创建 tag/Release。

## Behavior And Defaults

- adapter 仅接受 canonical snapshot/merge request；merge 始终 squash + exact head，绝不 admin/auto/delete branch。
- executor 在 delivery document 单独提交后，以其 full head 调用 `gkd-task deliver`；该 CLI 负责唯一 final state commit。

## Scope

- 实现 requirements 中的 adapter、fake-gh contracts、executor Skill/测试、manifest 和操作说明。

## Non-Goals

- 不修改 AIO、生产安装、通用 task state 或已发布历史记录。

## Acceptance Criteria

- 满足 requirements 的全部条件。

## Compatibility

- 保持现有 adapter protocol 和 task delivery state schema；只提供受信实现和正确调用指引。

## Security And Data

- 不回显 credentials 或 gh stderr；不让自检调用真实 merge。

## Migration

- 无迁移；历史异常只记录，不回填状态。

## Public Interfaces

- 新增 bundle 内 GitHub acceptance adapter executable，并更新 gkd-execute delivery contract。

## Execution Route

- automatic。six gates、bridge 与唯一 exact `gkd_executor` / `fork_turns="none"` 必须完整绑定。

## External Side Effects

- 允许任务 PR、范围内 CI 修复与无阻塞 acceptance merge；禁止 tag、Release、production 与 AIO 写入。

## Action Mode

- `implement_and_merge_on_acceptance`；允许 `ci_repair`、`commit`、`conditional_merge`、`pr_update`、`push`、`ready_for_review`。

## Implementation Notes

- 使用 fake gh，不从真实 PR 自检 merge；delivery sequence 以 task core 已实现合同为事实源。
