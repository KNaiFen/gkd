# GKD Runner Resource Fact Binding Plan

## Goal

让 GKD CI recommendation 只根据可归属到当前 verified runner 的资源事实给出容量建议，避免 host 信息漂移为 cloud capability。

## User Decisions

- 用户授权修复这个已复现的通用事实绑定缺口，并在 fixed-head acceptance 后按现有授权合并。
- 价格继续 unverified；不新增 runner、Secrets、付费资源或 GitHub 设置。

## Behavior And Defaults

- resource-constrained 仍是没有 runner-bound complete facts 时的默认。
- runner capacity 只能由输入的当前 verified runner 事实表达；不存在的替代 runner 不被推荐为可选择对象。
- speed-first 只在 source=runner、资源完整已验证且与当前 runner capacity 一致时提升 preset。

## Scope

- 修改通用 recommendation normalization/selection、focused tests 和 resource documentation。

## Non-Goals

- 不改变 scanner、artifact limits、billing schema、workflow、AIO adapter、release 或 production migration。

## Acceptance Criteria

- 满足 requirements.md 的全部 AC，并从完整 base 运行版本化 verifier与 fixed-head CI。

## Compatibility

- 保持 public machine result schema；收紧不可信输入的 recommendation 值，不为旧 host-derived 高容量输出保留兼容路径。

## Security And Data

- 输入/输出不回显 credentials、机器路径或价格；host 资源只能作为 host 事实，不能作为云端证明。

## Migration

- 无状态迁移；调用方在不完整或非 runner 资源事实下得到保守 recommendation。

## Public Interfaces

- 保持 `gkd-resource-scanner recommend` CLI 形状不变；只收紧 `preset` 和 `runnerAction` 的语义。

## Execution Route

- automatic route；trusted main 使用 accepted v0.1.3 bundle、project verification、六门 route、bridge prepare 和唯一 direct `gkd_executor`（`fork_turns="none"`）。

## External Side Effects

- 允许任务分支 commit/push、一个 PR、范围内 CI 修复和 fixed-head independent acceptance 后 squash merge；不允许 tag、Release、runner 或 GitHub settings。

## Action Mode

- `implement_and_merge_on_acceptance`；actions 为 `ci_repair`、`commit`、`conditional_merge`、`pr_update`、`push`、`ready_for_review`。

## Implementation Notes

- 首先以 host facts + standard GitHub runner 的反例锁定 bug；避免以本机资源或价格为 fixture 常量。
