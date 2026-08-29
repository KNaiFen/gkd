# GKD Gate Repair R2 Plan

## Goal

在不改变 self-hosting task-state 外形的前提下，把历史 revision、planning refresh 和固定 result-manifest sidecar 收敛为可恢复、可验证的任务门禁。

## User Decisions

- 以 trusted main `62ea7d9` 为完整基线；R2 accepted merge 前不重启 O4。
- 使用一个精确 `gkd_executor`、一个独立 `gkd_acceptor`；只有 trusted main 可以 merge、记录和清理。
- 生产、AIO、GitHub settings/Secrets、付费 runner、tag/Release 和已发布资产均不在范围内。

## Behavior And Defaults

- history 的 revision 已是持久、顺序且 integrity-covered 的逻辑事实；UTC 值仅为审计时间，新 validator 不再要求其单调。
- `planning-refresh` 是显式、CAS 保护、仅 planning 可用的事务；它更新 document digest 与 material digest，不改变既有 approval/authorization 的有效性规则以外的状态。
- 自动 delivery 必须在 implementation head 中存在 canonical result-manifest sidecar，且其 task/base/implementation/bundle/result/evidence 事实与 CLI 参数和固定 tree 一致；state delivery record 继续只用现有字段。
- delivery document commit 后无任何候选提交；任何发现的修复必须走 canonical rework 和新 offer/claim。

## Scope

- 调整 `gkd_task` model/service/CLI/acceptance 和独立 result-manifest schema。
- 更新 packaging expected-set、bundle build inputs、使用文档及 task-core/runtime-bridge/rework 合同。
- 以 backward-compatible 方式验证旧 state；不向 task state event/delivery records 新增字段。

## Non-Goals

- 不改变 watcher/probe、CI provider 查询、角色选择或 release 语义。
- 不让 manual delivery 获得自动路线的 candidate bundle 语义；原有 manual contract 继续保持最小行为。

## Acceptance Criteria

- 相同或回拨 wall-clock 的历史由 revision 验证，state key set 保持兼容。
- planning refresh、sidecar digest/head/bundle drift、missing/noncanonical sidecar 和 post-delivery drift 都有稳定负向测试。
- default verifier、bundle verify、trusted-main status/doctor、fixed-head CI 和独立 acceptance 在同一 final head 上通过。

## Compatibility

- 保留 UTC、revision/CAS、phase matrix、delivery document 和 candidate output bundle digest 字段。
- 旧 state 在读取时不改写；新 refresh event 仅在 R2 merged 后的后续任务出现。
- R2 task 不写新 state 字段，因此旧 trusted main 能在 merge 前执行 acceptance/rework。

## Security And Data

- sidecar 只保存 canonical digest、固定 SHA、枚举和脱敏状态；不保存 prompt、transcript、凭据或本机路径。
- 输入必须是 canonical regular file，失败不吞错且事务不产生部分 coordination 状态。

## Migration

- R2 accepted merge 后，O4 从该 merge SHA 重新 bootstrap；旧 rejected attempts 不迁移、不修改。
- 只有新创建的任务使用 planning refresh；历史任务保持原文件和 digest 事实。

## Public Interfaces

- 新增稳定 `gkd-task planning-refresh` 和自动 delivery sidecar 参数/约定，帮助文本明确 CAS、phase、固定路径与必需字段。
- status、doctor、rework、acceptance、O3 result consumer 和 gkd-role 继续读取 task state 的既有字段。

## Execution Route

- trusted main 完成 requirements-ready、plan-approve、authorization、route、offer、claim 和 bridge handoff。
- executor 完成所有代码、schema、tests、bundle/lock、sidecar 与 delivery document 后才调用 deliver；delivery 后停止。
- acceptor 在 clean trusted main 使用 exact full head 和相对 `.gkd/policy.json` 运行 fixed-head CI，随后仅走 canonical acceptance/rework。

## External Side Effects

- 允许一个任务 worktree/branch/PR、隔离 runtime/evidence 和只读 CI 查询。
- 禁止生产、AIO、settings、Secrets、runner、tag/Release 和计划外外部写入。

## Action Mode

`implement_and_merge_on_acceptance`

## Implementation Notes

- 先建立 `advance_state`、`_history_relationships`、`read_state`、`deliver`、acceptance/rework、bundle packaging 和 R1 finding 的基线。
- 先完成及验证所有源码/lock/packaging 改动，再生成最终 candidate output digest 和 sidecar；delivery 后只允许 state coordination commit。
