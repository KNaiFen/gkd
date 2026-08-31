# GKD I1 Trusted Context Symlink Boundary Plan

## Goal

在所有物理路径解析前验证输入路径的 lexical ancestors，消除 I1 context resolver 可被 ancestor symlink 绕过的边界缺陷。

## User Decisions

- 固定基线 `5605c5fb16d0571185aeab256cf4c4c40a52061c`，execution bundle `045604ca8572525c56cf6561bad53e22a16a6efa2fec1b875c3f97e118960192`。
- 只修复 post-accept audit 的 symlink finding；不重新设计 I1 高层 API，也不提前实施 P2。

## Behavior And Defaults

- lexical ancestor 检查先于 `resolve()`、`git_root()`、`verify_identity()`；不存在的最终路径可按既有创建/读取语义处理，但已存在的任一祖先 symlink 必须拒绝。
- 所有正常非 symlink 输入保持现有 canonicalization 和 context 输出。

## Scope

- 提取一个最小的路径 ancestor validator，接入 orchestrator current path、candidateRoot 和 runtime attachment validator；补齐 focused tests 与必要 manifest/lock。

## Non-Goals

- 不改变任何 task lifecycle、runtime receipt、bundle identity、planning parser 或 CLI 参数；不处理生产 home。

## Acceptance Criteria

- cwd/attachment/trusted anchor 的 ancestor symlink 正例拒绝，正常三路解析和历史 drift selector 回归通过，双解释器与 fixed-head CI 通过。

## Compatibility

- 保持已有绝对路径规范化、`/private/tmp` 等系统别名行为；只新增对 symlink ancestor 的拒绝，不改变错误成功路径。

## Security And Data

- 使用 `lstat` 逐段检查原始 lexical path，不持久化原始路径或生产信息；失败不产生任何写入。

## Migration

- 合并后刷新未发布 development bundle/project stage；旧 I1 bundle、已发布资产和生产不改动。

## Public Interfaces

- 不新增用户可见参数；现有 `gkd-main inspect/preflight` 输出和错误分类保持兼容。

## Execution Route

- fresh task lifecycle、bridge claim、单 executor、独立 acceptor、trusted main merge；executor 只交付。

## External Side Effects

- 仅允许 task worktree/branch/PR、verifier/evidence 与只读 CI；禁止生产/AIO/settings/Secrets/runner/tag/Release。

## Action Mode

`implement_and_merge_on_acceptance`

## Implementation Notes

- 在任何 `Path.resolve()` 前对 current cwd、attachment candidateRoot、trusted anchor 的每个现存 component 执行 `lstat`；不要在 resolve 后再尝试恢复 lexical 信息。
- 复用现有 locator identity 校验和 runtime attachment schema；focused tests 必须证明候选 cwd 与 runtime fallback 都不能通过 ancestor symlink。
- implementation commit 后 delivery.md 是唯一直接子提交，delivery 后不再加入实现提交。
