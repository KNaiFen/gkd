# GKD O8 Release Upgrade Compatibility Plan

## Goal

把兼容承诺从默认矩阵的隐式集合变成由 catalog 声明的核心代表合同与显式 release-upgrade 完整矩阵，降低正常 PR 成本而不损失升级可验证性。

## User Decisions

- 固定基线 `48e1e25948fe2e3348068821e6d945c712be89d9`，execution bundle `904e1d02d5519b00bf9e3b9bda8e97a4ab1883d3114730d3e0caae03c25582af`。
- O8 只评估 finalization/release shared engine；ADR 的结论必须是本阶段不实施合并，并把真实迁移留给单独任务。

## Behavior And Defaults

- default/core 每种公开旧格式只执行 catalog 中的一个 read 正例和一个 reject/restore 正例；这两类测试都应有稳定、完整的 test ID。
- `release-upgrade/matrix` 是完整历史组合、稳定版本与扩展异常的显式 lane，不是 `historical/watcher` 的别名，不能被默认 verifier 隐式运行。
- 所有 lane 继续由 canonical result manifest 绑定固定 base/head、环境、scope、完整 test ID 集和 digest；release-upgrade 证据不能由 core 成功代替。

## Scope

- 新增 catalog、release-upgrade tests/lane/profile/evidence，以及将已识别完整 matrix 从 core 移到该 lane 的最小测试布局调整。
- 为 source-v1 和 result-manifest-v1 补足独立可定位的 reject/restore contract，保留所有现有读写、fail-closed 和 migration 语义。
- 按 ADR template 记录 `gkd-finalize`/`gkd-release` 不合并的架构决定和后续迁移任务的严格边界。

## Non-Goals

- 不改变 watcher historical lane、task/role/bridge/acceptance、production migration、release/finalization 的可观察接口或行为。
- 不把 release-upgrade 加入常规 GitHub PR workflow，不变更 GitHub 设置或发布流程。

## Acceptance Criteria

- catalog、core representative contracts 和 release-upgrade matrix 彼此完整、无重叠漏项，负例严格拒绝。
- Python 3.9.6/3.14.6 分别产出可验证的 default/core、historical/watcher 和 release-upgrade 固定结果；release-upgrade evidence 两次一致。
- bundle generate/verify、隔离 install/verify、fixed-head `GKD Verify` 与 independent acceptance 通过；ADR 准确限定未来 engine migration。

## Compatibility

- legacy schema-v1 source/install/result/task/offer/envelope/role/release-record 等公开入口继续 read、reject、restore 或 migrate；旧命令名称、record schema、error code 和 stdout/stderr 分类不变。

## Security And Data

- catalog 仅引用完整、受管 test ID 和枚举式 format name；未知格式、重复 ID、跨 lane 漏映射、scope drift、结果/环境/head/base/digest 失配均 fail closed。不得读取凭据或生产配置。

## Migration

- 合并后只刷新未发布 development bundle 和隔离 project stage；release-upgrade 是 release candidate 或显式升级验证的入口，生产、AIO、已发布 asset 和既有 release 不改动。

## Public Interfaces

- `scripts/gkd-verify` 可增加显式、枚举式 `release-upgrade` lane/profile；默认参数仍只运行 core。`gkd-finalize` 和 `gkd-release` 保持全部现有 CLI 名称、参数和 JSON 形状。

## Execution Route

- gkd-main 完成 planning、authorization、offer/claim；bridge 在 spawn 后立即写入 claim。executor 只交付，独立 acceptor 只验收，trusted main 按 fixed head 合并和清理。

## External Side Effects

- 仅允许 task worktree/branch/PR、verifier/evidence、ADR 和只读 CI；禁止生产、AIO、GitHub settings、Secrets、runner、tag/Release 写入。

## Action Mode

`implement_and_merge_on_acceptance`

## Implementation Notes

- 先由现有公开 tests 建立 catalog，再迁移完整 matrix；不得以删除测试或只写 Markdown 达到“降频”。每个迁移前后由 catalog 验证 core 与 release-upgrade 的 union 精确覆盖现有承诺。
- release-upgrade 必须是新 lane/profile 和测试 scope，不能把完整 matrix 留在 core discovery 后仅通过条件跳过。验证其 canonical result/evidence 的全量绑定和双运行一致性。
- ADR 仅允许记录决定及后续任务；本任务禁止移动 `gkd_finalization` 或 `gkd_release` 的 implementation。最终 implementation commit 后 delivery.md 是唯一直接子提交。
