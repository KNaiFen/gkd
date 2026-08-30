# GKD O4 Lane Manifest Compatibility R3 Plan

## Goal

先将 result manifest 的 lane/profile 消费能力以旧默认验证产物安全合并，再让后续 O4 分层任务改变 default scope 集合。

## User Decisions

- 基线 `5708aaf990564b07c258bdc34682249df1b5b5f6`，execution bundle `65354c4a94abad709be30e8c154cb671c75631b1bc3dc13a5fddfa1d634fdaa3`。
- 历史 O4/compatibility attempts 只读；一个 executor、一个 acceptor，trusted main 合并清理；executor 必须使用 bridge execution context；无生产/AIO/settings/Secrets/runner/tag/Release 副作用。

## Behavior And Defaults

- manifest 的 lane/profile 是 producer、consumer、delivery、acceptance/rework 共享事实源。已知 profile 必须定义完整无重复 scope；legacy manifest 保留明确 strict path。
- 本任务实际 default verifier 保持现有完整 scope 结果，因此 current trusted acceptance 仍可验证自己的 delivery。

## Scope

- 实现 shared manifest validator、schema/profile、consumer/delivery/acceptance/rework integration 与正反 tests；更新文档、manifest/lock。

## Non-Goals

- 不改变 verifier `SCOPES`、watcher/probe runner 或默认安装面；不进入 O4 feature/O5-O8。

## Acceptance Criteria

- 旧实际 default artifacts 继续由 current accepted bundle acceptance 读取；synthetic explicit default/historical profiles 通过 shared consumer；所有 unknown/mismatch/tamper/drift 失败。
- 双解释器 verifier、bundle、delivery、CI、independent acceptance 通过。

## Compatibility

- 保留 legacy manifest strict validation，不接受任意 scope；公开 CLI 和 watcher API 不变。

## Security And Data

- 不读取凭据或生产配置；artifact/evidence 仅含 canonical 脱敏内容；错误 fail-closed。

## Migration

- 合并后仅刷新未发布 development execution bundle/project staging；下一项才创建完整 O4 feature task。

## Public Interfaces

- manifest schema/profile 版本化；`gkd-task`、`gkd-role`、`gkd-ci-monitor` CLI 不改变调用形状。

## Execution Route

- gkd-main 完成 planning/authorization/offer/claim；host acknowledgement 在 spawn 前按 bridge 请求 task name 准备，spawn 返回后主线程立即 bridge claim；executor 只交付，acceptor 只验收，trusted main 合并清理。

## External Side Effects

- 仅允许 task worktree/branch/PR、verifier/evidence 和 read-only CI；禁止生产/AIO/settings/Secrets/runner/tag/Release。

## Action Mode

`implement_and_merge_on_acceptance`

## Implementation Notes

- 先定位 manifest producer/consumer、delivery/acceptance/rework validators；以最小 shared validator 替代旧全局 scope 假设。final implementation commit 含代码/schema/lock/results/evidence/sidecar，delivery.md 是唯一直接子提交。delivery 后用 document head 和当前 revision 调用 canonical deliver。
