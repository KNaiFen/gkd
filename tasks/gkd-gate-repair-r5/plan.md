# GKD Gate Repair R5 Plan

## Goal

先消除 executor Python 3.9 的 payload 兼容断点，再以 revision、planning refresh 和 fixed-tree sidecar 完成可自举 delivery 门禁修复。

## User Decisions

- 基线为 trusted main `2b8cdf0`，accepted merge 前 O4 保持暂停。
- 一个 executor、一个 independent acceptor、trusted main merge；旧 attempts 不复用。
- 生产、AIO、GitHub settings/Secrets、runner、tag/Release、已发布资产不变。

## Behavior And Defaults

- payload 使用 Python 3.9 可用的显式严格配对，而不依赖 `zip(strict=True)`；程序性错误不伪装成 state filesystem 问题。
- revision 是逻辑顺序，UTC 是审计字段；planning-refresh 是 planning-only CAS transition。
- automatic delivery 的 sidecar 从 existing implementation head fixed tree 推导位置，不自报 SHA；服务从真实 canonical result/evidence artifacts 重算全部 digest。final implementation commit 后仅 delivery.md，随后状态冻结。

## Scope

- 更新 Python 兼容实现、gkd_task model/service/CLI/acceptance、result-manifest schema、packaging/lock、文档与合同。

## Non-Goals

- 不改变验证 scope、watcher、CI provider、roles、release 或手动 route。
- 不将一次性可信解释器 precheck 固化为产品路径。

## Acceptance Criteria

- Python 3.9 pre/post compatibility、revision、refresh、actual artifact digest、fixed-tree sidecar、delivery ancestry与post-delivery freeze均有正反合同。
- old trusted validator读R5 state；full verifier、CI和independent acceptance在一固定head通过。

## Compatibility

- 保留现有 state key、UTC/revision/CAS/phase/delivery record；R5不写新state字段。
- 历史状态不迁移；新的 refresh 行为仅供合并后任务使用。

## Security And Data

- 输入为canonical regular files，sidecar仅含identity/digest；不保存path、prompt、transcript或credentials。
- 失败不吞错或写半状态。

## Migration

- accepted merge后，O4从该merge SHA bootstrap；旧拒绝/阻塞记录继续归档。

## Public Interfaces

- planning-refresh、automatic delivery artifact/sidecar 参数与错误码稳定；acceptance/rework复核同一链。

## Execution Route

- trusted main完成授权/offer/claim。executor可用受控兼容解释器完成首次旧payload precheck；补丁后必须以actual Python3.9验证。最终implementation commit包含sidecar，下一提交仅delivery.md再deliver。
- acceptor以相对`.gkd/policy.json`固定head CI，全部通过后 narrow accept。

## External Side Effects

- 允许隔离worktree/branch/PR/runtime/evidence与只读CI；禁止生产、AIO、settings、Secrets、runner、tag/Release写入。

## Action Mode

`implement_and_merge_on_acceptance`

## Implementation Notes

- 先枚举所有 strict-only用法并针对 Python3.9建立失败基线；不要只修单个出现点。
- final implementation commit必须同时包含兼容修复、三项门禁、schema/tests/lock/sidecar；delivery后无后续提交。
