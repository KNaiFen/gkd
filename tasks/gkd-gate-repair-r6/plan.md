# GKD Gate Repair R6 Plan

## Goal

以当前 revision 作为唯一逻辑顺序，为 planning 文档提供受信 refresh transition，并把 automatic delivery 声明绑定到 final implementation fixed tree 中的真实 verifier result/evidence。

## User Decisions

- 基线为 trusted main `b5569bba8268770e2363372221bbc07dbdd6b92a`，execution bundle 为 accepted Python 3.9 bundle `d9ea5f423987812bc4dd259d0bd90c485bbf0e8fdfda6c6a0d31f3f5a4a3aaf7`。
- 一个 executor、一个 independent acceptor、trusted main merge；旧 attempts 不复用，R5 implementation 只读参考。
- 生产、AIO、GitHub settings/Secrets、runner、tag/Release、已发布资产不变。

## Behavior And Defaults

- revision/head/record relationship 是逻辑顺序；UTC 只验证格式，不参与跨进程单调比较。
- planning refresh 是 planning-only CAS transition；材料变化使旧 approval/authorization/offer 失效。
- automatic result-manifest 位于 final implementation commit，不自报 commit SHA；deliver、acceptance 和 rework 从实际 canonical artifacts 重算 digest。

## Scope

- 更新 `gkd_task` model/service/CLI/acceptance、artifact parser、result-manifest schema、task schema、packaging/lock、Skills、文档和合同。
- R6 自身使用新 sidecar/artifact delivery 链，但不调用 planning refresh，也不写新 state 字段。

## Non-Goals

- 不改变 watcher、verifier scope、route、CI provider、roles、release、manual delivery 或 Python 3.9 compatibility。
- 不将 rejected candidate 的 lifecycle/task records 移植进 R6。

## Acceptance Criteria

- revision logical ordering、planning refresh、actual artifact digest、fixed-tree sidecar、delivery ancestry和 post-delivery freeze 均有正反合同。
- system Python 3.9 与开发解释器完整 verifier、bundle、R6 live deliver、fixed-head CI 和 independent acceptance 在同一候选闭合。

## Compatibility

- 保留现有 task state key、UTC/revision/CAS/phase/delivery record；R6 不增加 state 字段，历史状态不迁移。
- 新 refresh/result-manifest 行为合并后适用于后续任务；旧 manual delivery 语义保持。

## Security And Data

- 输入仅为 canonical regular files，sidecar 只含 identity 与 digest；不保存路径之外的机器身份、prompt、transcript、credentials 或配置内容。
- 失败快速返回明确领域错误，不吞错、不写半状态。

## Migration

- accepted merge 后，O4 从该 merge SHA 新建 task；旧拒绝/阻塞记录继续只读归档。

## Public Interfaces

- 新增 planning refresh CLI；automatic deliver 增加实际 result/evidence 输入；acceptance/rework复核同一 fixed-tree artifact chain。

## Execution Route

- trusted main 使用 accepted Python 3.9 bundle完成 bootstrap、route、prepare 和 claim。executor 从 current main 实现，可只读比较 R5 implementation，但不得 cherry-pick其任务记录。
- final implementation commit 同时包含代码/schema/tests/lock、result/evidence/sidecar；下一提交只含 delivery.md，随后立即用 system Python 3.9 canonical deliver并停止。
- independent acceptor 使用相对 `.gkd/policy.json` 和 explicit full head；全部门禁通过后才 narrow accept/merge。

## External Side Effects

- 允许隔离 worktree、runtime、task branch、PR、read-only CI 和 evidence；禁止生产、AIO、settings、Secrets、runner、tag/Release 写入。

## Action Mode

`implement_and_merge_on_acceptance`

## Implementation Notes

- 从 R5 `eea2973` 仅提取 gate-repair思路，与 current main/Python 3.9 bundle重新实现；不要带入其旧 task/evidence 或兼容补丁。
- 在 final implementation commit 前完成全部生成物和双解释器验证；delivery 后无提交。
