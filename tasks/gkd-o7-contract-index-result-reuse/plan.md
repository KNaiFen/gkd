# GKD O7 Contract Index And Result Reuse Plan

## Goal

将已执行的 canonical scope 结果作为唯一行为事实，允许多个合同稳定引用同一测试结果，并让 delivery 只补充自身独有的边界验证。

## User Decisions

- 固定基线 `20f787b01248bcdc77af32952b439773b06be752`，execution bundle `8c34b7474d4fb55c1d688f515dbd2f4f7cac32c8706865a4bc8eea2060bd10b3`。
- O6 已将默认 core 收窄为八 scopes；O7 只在该 accepted result/delivery 格式上实施，保留此前 rejected attempts 的历史事实。

## Behavior And Defaults

- canonical scope runner 是行为测试的唯一执行者；有 canonical results 的 consumers 只能验证并选取其中通过的测试，不能隐式重跑同一行为。
- contract catalog 使用完整 test ID 作为证据主键，contract-to-tests 与 test-to-contracts 由同一声明确定性派生；一个测试被多个合同引用不会产生多次执行。
- 无 canonical results 的直接 runner 保持显式调用路径，用于局部诊断或 evidence lane，不作为默认重复验证路径。

## Scope

- 增加可复用的 catalog/index 与已验证 canonical-result 选集接口，迁移 task-core/delivery、watchdog、foundation 的现有 suffix/手写映射。
- 在 delivery canonical-result 路径移除 focused unittest 执行，保留其 implementation head、document binding、protected/temporary/output 检查与明确的九项合同清单。
- 添加正反单元和集成合同，更新 manifest/lock、验证和必要文档。

## Non-Goals

- 不压缩合同集合、不将 historical watcher lane 带回 core、不重写测试框架或改变 result schema。
- 不实施 O8 的 compatibility matrix 调整，也不合并 release/finalization 模块。

## Acceptance Criteria

- 一次 task-core canonical result 可被 delivery 准确消费；九项目标的缺失、失败或任何结果绑定漂移都会失败。
- watchdog/foundation evidence 保持每个既有合同的 test 关联，并新增稳定的反向可查询性；共享测试只记录一次执行结果。
- 双解释器 core verifier、focused regression、bundle/install、fixed-head CI 和 independent acceptance 成功，且证据可绑定 fixed head。

## Compatibility

- 保持 canonical result schema 与所有现有 CLI 参数不变；已有 result manifests、scope 文件和 legacy read/reject/migrate 入口仍可读取或按既有规则拒绝。

## Security And Data

- 仅使用仓库内完整 test ID、已验证结果和受管临时路径；未知 test ID、重复 ID、跨 scope 映射、结果失配及路径重叠在写入前拒绝。

## Migration

- 合并后只刷新未发布 development bundle 与隔离 project stage；不写入生产 `~/.codex`、AIO 或已发布资产。

## Public Interfaces

- 若结果模块增加查询函数，其输入为已验证 scope、完整 test ID 列表和仓库根；现有 `load_canonical_results` 和 runner CLI 保持兼容。

## Execution Route

- gkd-main 完成 planning、authorization、offer/claim；bridge 在 spawn 后立即写入 claim。executor 只交付，独立 acceptor 只验收，trusted main 按 fixed head 合并和清理。

## External Side Effects

- 仅允许 task worktree/branch/PR、verifier/evidence 与只读 CI；禁止生产、AIO、GitHub settings、Secrets、runner、tag/Release 写入。

## Action Mode

`implement_and_merge_on_acceptance`

## Implementation Notes

- catalog 应足够小且声明式：以完整 test ID 声明 contract ownership，反向索引排序并检查无重复；不得依赖 suffix 的偶然唯一性作为证据主键。
- delivery 的 canonical-result 路径不得构造或运行 focused suite；直接模式的行为须有测试明确覆盖。result 选集接口必须复用完整 scope 验证而不是宽松读取 JSON。
- foundation 的已参数化 mode-drift 测试和独立 source-mode boundary 保持原样；只消除它们周围重复的映射/证据实现。最终 implementation commit 后 delivery.md 是唯一的直接子提交。
