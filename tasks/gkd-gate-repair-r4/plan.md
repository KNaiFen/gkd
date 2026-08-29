# GKD Gate Repair R4 Plan

## Goal

通过 revision 逻辑顺序、planning refresh 与从 state/fixed tree 推导位置的 result-manifest sidecar，完成可自举的 GKD 门禁修复。

## User Decisions

- 基线 trusted main `6f74ce9`；R4 accepted merge 前 O4 不启动。
- 一个 executor、一个 independent acceptor、trusted main merge；旧 attempts 不复用。
- 外部生产/AIO/settings/Secrets/runner/tag/Release 保持未修改。

## Behavior And Defaults

- revision 是逻辑序列，UTC 是审计字段。
- planning-refresh 是 planning-only CAS transition。
- automatic delivery 从 lifecycle 已有 implementationHead 固定 tree 定位 sidecar；sidecar不自报 SHA。服务以实际 results/evidence 重算事实，delivery.md 紧随 sidecar 所在 implementation commit，delivery 后冻结。

## Scope

- 更新 gkd_task service/CLI/model/acceptance、result-manifest schema、packaging expected set、bundle lock 与合同。

## Non-Goals

- 不改变验证 scope、watcher、GitHub API、roles 或 release；manual delivery 保持既有最小语义。

## Acceptance Criteria

- revision、refresh、sidecar fixed-tree location、actual results/evidence recomputation、delivery ancestry和post-delivery freeze都有稳定正反合同。
- R4 state 被 old trusted validator 读取，final verifier/CI/independent acceptance 在同一 full head 通过。

## Compatibility

- 保留现有 UTC/revision/CAS/phase/delivery key set；R4 不写新 task state fields。
- 旧状态只读；新 refresh event 仅供 merge 后任务使用。

## Security And Data

- sidecar与结果/证据输入均为 canonical regular file，只含 digest/identity；不记录本机路径、prompt、transcript或凭据。

## Migration

- R4 accepted merge 后，O4 从 merge SHA 新 bootstrap；旧 attempts 继续归档。

## Public Interfaces

- planning-refresh 和 automatic delivery 的 result/evidence/sidecar CLI 参数提供稳定帮助与明确错误码；新 acceptance/rework 复核同一绑定链。

## Execution Route

- trusted main 做授权/offer/claim；executor在final implementation commit完成全部代码、schema、tests、lock和sidecar，下一提交仅delivery.md再deliver。
- acceptor使用相对 `.gkd/policy.json` 对 full head CI，全部通过后 narrow accept。

## External Side Effects

- 允许隔离 worktree/branch/PR/runtime/evidence和只读CI；禁止生产、AIO、settings、Secrets、runner、tag/Release写入。

## Action Mode

`implement_and_merge_on_acceptance`

## Implementation Notes

- 以 R3 的 Git 自引用事实为硬约束：不得在 sidecar 中写 implementation SHA；通过 state delivery implementationHead 的固定 tree 反向定位。
- delivery 后不允许任何提交；若发现问题，必须新 attempt。
