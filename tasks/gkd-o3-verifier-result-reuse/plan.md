# GKD-O3 Plan

## Goal

建立单一 canonical scope runner 与可验证的结果消费边界，降低默认验证时间和重复 contract 维护成本。

## User Decisions

- 从 O2 accepted merge `2107ebccfb1f11979cf38d5b6ce1281bfb122bbb` 的完整 SHA 启动。
- canonical 行为测试默认只跑一次；evidence 只消费结果并补充边界快照。
- 一个 `gkd_executor` 交付、一个 `gkd_acceptor` 验收；trusted main 才能合并/清理。

## Behavior And Defaults

- 结果文件采用稳定 canonical JSON，绑定 base/head、scope、test ID、状态、环境和 verifier digest。
- evidence runner 缺结果、结果篡改、head/base/digest 不一致时立即 fail closed。
- protected/temporary/output、manifest/lock、路径泄漏和双运行一致性检查不因复用而删除。

## Scope

- `scripts/gkd-verify`、scope runners、evidence/result wrapper、相关 tests/mutations/docs 和 manifest/lock。
- 不改变 scope 名称、测试语义、失败码和历史 evidence 的事实记录。

## Non-Goals

- O4 watcher lane、O5 fixture split、O6 optional pack、O7 contract index、O8 compatibility/release boundary。
- 生产/AIO/settings/Secrets/runner/tag/Release。

## Acceptance Criteria

- 默认一次行为执行产生可消费 canonical 结果；各 runner 不再默认重复 discover 同一测试。
- 缺失/篡改/漂移结果有负向 contract；现有 verifier/evidence 通过且字节稳定。

## Compatibility

- 保持现有 CLI 参数、scope 列表、test ID、错误语义、manifest/lock 自验证和发布 traceability。

## Security And Data

- 结果只保留 redacted machine facts、digest、scope/test ID 和环境摘要；不得写入 credentials、绝对路径或原始日志。

## Migration

- 无生产迁移；新结果格式只在 candidate bundle 验证后随新 bundle 发布。

## Public Interfaces

- `scripts/gkd-verify` 默认入口保持兼容；新增的 result-consume 参数或文件格式必须版本化并有 schema/contract。

## Execution Route

- 按 GKD 状态机 bootstrap、authorize、offer、claim、deliver；独立 acceptor 固定 head 验收，trusted main 最终合并。

## External Side Effects

- 允许一个 task worktree/branch/PR、标准 CI、隔离 evidence roots 和只读 GitHub 观察。
- 禁止生产/AIO/settings/Secrets/付费 runner/tag/Release。

## Action Mode

- `implement_and_merge_on_acceptance`。

## Implementation Notes

- 先记录当前 scope/test 基线，再引入结果 wrapper；逐 scope 验证，避免一次性大重构。
- 交付文档单独提交后调用 `gkd-task deliver`；不跨入 O4-O8。
