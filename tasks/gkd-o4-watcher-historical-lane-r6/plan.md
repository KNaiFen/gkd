# GKD-O4-R6 Plan

## Goal

将 watcher/probe 从默认验证成本中隔离，同时保留显式历史验证能力，并让 fixed-tree result consumer 按 manifest 的 lane/profile 验证 scope，而非沿用旧全局假设。

## User Decisions

- 基线为 `ba32d14729eb38058f4d59e9c83b3e22ff0c8993`，execution bundle 为 `04efd9ce5f1e0f678f9853eef5d9fb20606fff6e667aba69d9b204bddeb9b5d6`。
- R6 是新的 task/offer/claim/runtime/branch/worktree/PR；历史 lifecycle 不重用。compatibility R3 已提供 accepted lane/profile consumer。
- executor 使用 bridge execution context 的精确 absolute CLI/candidate/task/runtime argv；不依赖 PATH 或 cwd。
- 一个 executor、一个 acceptor；仅 trusted main 合并和清理。生产/AIO/settings/Secrets/runner/tag/Release 不变。

## Behavior And Defaults

- default `gkd-verify` 只运行十个 core scopes，不隐式启动 watcher、app-server 或 live probe。
- historical lane 使用明确命令或 flag，记录独立 lane/profile、scope、canonical result/evidence；host 不可用时返回稳定 `unsupported`。
- manifest 是 producer、consumer、delivery、acceptance 与 rework 的唯一 lane/profile 事实源。consumer 先验证已知 lane/profile、完整无重复 scope，再验证 test IDs 与 digests。

## Scope

- 修改 default scope 列表、historical runner、manifest producer、README、tests 和 manifest/lock；consumer、delivery/acceptance/rework validation 只做与 producer 分层所需的最小集成或回归更新，不重复 compatibility R3。

## Non-Goals

- 不重写或删除 watcher/probe，不删历史证据，不进入 O5-O8，不更改 gate-repair/Python 3.9 合同。

## Acceptance Criteria

- default 十 scope 与 historical 47 contracts 各自独立可验证；双解释器、bundle、delivery、CI、independent acceptance 全部通过。
- lane/profile 未知或 scope/test/digest/base/head drift 继续拒绝且无半状态；两次 historical evidence 字节一致。

## Compatibility

- `gkd_watchdog`、`gkd-watchdog-mcp`、M-1B evidence、M-1C probe 参数和旧无 lane/profile manifest 的 legacy strict path 保持兼容；新路径不能放宽为任意 scope 集合。

## Security And Data

- 不读取凭据、生产 config 或原始 session；historical evidence 仅含脱敏摘要、digest、枚举、清理状态。临时资源清理失败 fail-closed。

## Migration

- 已发布 bundle 不修改；合并后仅 trusted main 刷新未发布开发 bundle 和 project staging。现有 watcher CLI 继续可用，完整历史验证走 explicit lane。

## Public Interfaces

- 保留现有 watcher CLI/probe 参数；新增 historical entry 和 manifest lane/profile 具稳定帮助文本、错误码与 scope 名称。`gkd-task`、`gkd-role`、`gkd-ci-monitor` 既有接口不变，除非有明确 schema version 与 legacy contracts。

## Execution Route

- gkd-main 完成 planning、authorization、offer、claim 和 trusted bridge；spawn 前固定 acknowledgement 与 status CAS，spawn 后立即 claim；精确角色为 `gkd_executor`，无 worker/fallback/nested/retry。
- executor 只实现交付；acceptor 在真实 canonical checkout 对 explicit full head 验收；trusted main 才合并清理。

## External Side Effects

- 仅允许 task worktree/branch/PR、default/historical verifier、隔离 evidence 与只读 CI；禁止生产/AIO/settings/Secrets/runner/tag/Release 写入。

## Action Mode

`implement_and_merge_on_acceptance`

## Implementation Notes

- 先检索 SCOPES、producer/consumer、delivery/acceptance/rework validators 和 watcher/probe runners，建立 default/historical 基线；不用删测试、跳过失败或硬编码 pass 缩短验证。
- final implementation commit 含代码/schema/lock、双解释器验证和 R6 artifacts；delivery.md 是其唯一直接子提交，delivery 后无实现提交。
