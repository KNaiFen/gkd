# GKD-O2 Plan

## Goal

把持久上下文压缩为当前事实与下一任务的单一入口，同时把完整历史留在 decisions、open-items 和 task records。

## User Decisions

- 从 O1 accepted merge 之后的完整 trusted main SHA 启动。
- 只使用一个 `gkd_executor` 和一个独立 `gkd_acceptor`；trusted main 才能合并和收尾。
- 只做文档整理，不复制 host hook，不修改 bundle、生产或 AIO。

## Behavior And Defaults

- `context.md` 顶部事实必须描述当前已发布 pin、当前授权边界和下一项 O3 依赖。
- O1 accepted 和 O2 in-progress 只各出现一次；完整时间线继续保留在 decisions/open-items。
- host-level mailbox/recovery 修正明确标记为 GKD bundle 外事实。

## Scope

- 仅修改 `.agents/context.md`，必要时同步本任务 acceptance/retrospective 和持久索引。

## Non-Goals

- 不修改 canonical payload、manifest/lock、CLI、tests、Skills、roles、生产 `~/.codex`、AIO 或 GitHub 状态。

## Acceptance Criteria

- context 无旧矛盾或重复 C final；当前状态、next task、授权边界可单页判断。
- 文档 diff 通过 `git diff --check`，无绝对路径和凭据形态。
- O2 candidate fixed head 通过独立 review、固定头 CI 和 canonical acceptance。

## Compatibility

- 不改变任何 runtime、schema、digest、task state 或发布资产；历史记录路径和链接保持有效。

## Security And Data

- 只处理仓库内公开记录；不读取 private session、credentials 或生产配置内容。
- context 不新增用户目录绝对路径、token、secret 或机器身份。

## Migration

- 无安装或消费迁移；合并后仅更新 trusted main 文档状态。

## Public Interfaces

- 不新增或删除 CLI/API；仅调整持久文档入口的表述和索引。

## Execution Route

- `gkd-main` 走 requirements-ready、plan-approve、authorize、offer、claim、delivery、accept、merge 全流程。
- executor 只交付；acceptor 只验收；trusted main 只合并和清理。

## External Side Effects

- 允许一个 task worktree/branch/PR、只读 CI 观察和 task records。
- 禁止生产/AIO/settings/Secrets/runner/tag/Release 写入。

## Action Mode

- `implement_and_merge_on_acceptance`。

## Implementation Notes

- 以当前 context 事实为输入，删除覆盖项和重复项，写出一条明确 next task。
- 运行文档 focused checks、声明的 verifier、固定头 CI 和双 review evidence（若 contract 要求）。
- delivery document 单独提交后调用 `gkd-task deliver`，不跨入 O3。
