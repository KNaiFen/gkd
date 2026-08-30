# GKD O6 Delivery Pack Compatibility Plan

## Goal

先合入 forward-compatible consumer，再让 O6 producer 改变默认 scope 与安装面，消除 self-hosting delivery deadlock。

## User Decisions

- 基线为 `db72c1e1ef8e4c377274107a87299a368b57efb1`，execution bundle 为 `b7f1d783cf01cdcecfb12f98ce426877aec99b7b4647dacc542fdae8cc053d02`。
- blocked O6 只作为 future-format 测试事实，不复用 lifecycle；本任务保持 v1/full-install producer 与十 scope default。

## Behavior And Defaults

- 当前 producer 完全冻结；兼容逻辑只允许理解两个版本化格式并严格区分其不变量。
- schema v1 仍是本任务自身的输出格式；schema v2 只能作为明确 future candidate 输入进入验证。

## Scope

- 扩展 result lane/profile consumer 和 bundle/source/manifest/lock fixed-tree consumer；增加 future-format 正反合同、双解释器证据和文档。

## Non-Goals

- 不移出默认文件/Skills/scopes，不实现 optional pack 写入操作，不移植 O6 blocked implementation。

## Acceptance Criteria

- 本任务仍可由旧 execution bundle 以十 scope default 和 schema-v1 full install 交付；其安装态 consumer 可严格验证未来 O6 v2 packs 与八 scope/optional artifacts。

## Compatibility

- schema v1 行为字节和语义保持；schema v2 不允许隐式降级、自由路径 pack 或宽松 unknown fields。

## Security And Data

- future fixtures 只含仓库中立脱敏事实；所有文件路径、mode、size、digest 与 ownership 来自实际临时输入重算。

## Migration

- 合并后刷新未发布 development bundle/project staging；旧 release asset、生产与 AIO 不修改。

## Public Interfaces

- 不新增 pack 写入 CLI；只扩展现有 bundle/result consumer 的版本化输入接受集合，旧调用形状保持。

## Execution Route

- gkd-main 完成 planning/authorization/offer/claim；spawn 后立即 bridge claim；executor 只交付，acceptor 只验收，trusted main 合并清理。

## External Side Effects

- 仅允许 task worktree/branch/PR、verifier/evidence 与只读 CI。

## Action Mode

`implement_and_merge_on_acceptance`

## Implementation Notes

- 先复现 accepted consumer 对 O6 八 scope sidecar 的 `INVALID_RESULT_MANIFEST`，再以最小 forward parser 修复。final implementation commit 必须保留 schema-v1/full-install producer 和十 scope default，并包含实际 verifier result/evidence/result-manifest；delivery.md 是唯一直接子提交。
