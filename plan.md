# Task plan

## Goal

完成 manual-first 工作流收敛：使 `gkd-main` 自包含且可发现，删除仍可执行或可路由的旧自动化合同、脚本、schemas、测试和配置，并保留简短的 Markdown 交接闭环。

## Worktree

本文件所在的独立 Git worktree 根目录（`.`）。

## Behavior constraints

- 普通执行 session 只读取 `plan.md`、适用的 `AGENTS.md` 和完成目标所需的代码。
- 不新增机器状态、JSON 合同、生命周期脚本或第二个通用 GKD Skill。
- 不触碰生产 `~/.codex`、AIO、GitHub 设置、Secrets、付费 runner、既有 tag 或 Release。
- 删除范围限于仓库中旧 automatic/fixed-head 合同的可执行实现、路由和测试；Git 历史仍是历史追溯方式。
- 验证只覆盖新的 manual-first 用户路径和删除后仓库不再暴露旧入口的事实。

## Completion conditions

- 当前工作树仅保留自包含、可发现的 `gkd-main`。
- `gkd-main` 明确规定计划、进度、审查、恢复和最小验证证据。
- 仓库不再保留或路由旧 task/role/CI/acceptance/release 合同实现。
- README、模板、持久记录与实现一致，并有可复核的最小验证结果。
