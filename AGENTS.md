# AGENTS.md

## 项目定位

- 本仓库采用 manual-first Agent 工作流：目标项目的 `.gkd/` 目录保存当前 `plan.md`、`plan-changes.md`、`review.md`，以及 worktree 内执行 session 使用的 `execution.md`、`progress.md`；已批准 delegated 成功后必须归档到 `.gkd/archive/`，direct-main 按需归档。
- 旧 bundle、automatic route、固定 head 验收和发布验证已从当前工作树移除；需要追溯时查看 Git 历史，不恢复迁移流程。用户明确选择自动执行时，main 只能以命名 `agent_type=gkd_execute` 启动执行 session；这不是旧自动化流程的恢复。
- “拟 PLAN”和“批准 PLAN 后开始执行”是两个独立授权状态。`plan-only` 只允许调查、问答和写计划，禁止创建 worktree/分支、写代码、启动代理、提交、推送、合并、发布或清理；材料性方案变化须追加 `plan-changes.md` 并重新确认。
- 需要等待 CI 时只能由命名的 `gkd_ci_monitor` 只读角色调用目标项目 `scripts/gkd-github-watch`，每次显式传入 `--interval 30 --timeout 3600`；改变任一参数须有 PLAN 授权，目标缺失、漂移或认证失败即阻塞，不得临时使用 GitHub CLI 的 watch 子命令或其他轮询。
- delegated 执行完成后才可由 `gkd_accept` 独立验收；成功收尾必须先脱敏归档，再按授权创建包含活动记录删除的 cleanup commit，经过 main 审查/合并后才清理 worktree、仅删除已确认合并的本地/远端本轮任务分支并恢复干净 `main`；异常或远端状态不明时保留现场。

## 工作规则

- 材料性规划、架构或流程变更前必须完整阅读并遵守 [VISION.md](VISION.md)。
- 普通任务先阅读适用的 `AGENTS.md`；只有会改变 GKD 架构、流程、发布状态或授权边界时，才读取 `.agents/` 中的持久记录。
- 保持变更小而明确，禁止写死仓库、用户名或本机绝对路径。
- 人工任务的持久交接使用上述 Markdown 文件；不要为普通任务新增机器合同或状态副本。项目归档仅保存脱敏后的 Markdown 事实和摘要，不承担运行时状态。
- 只有 GKD 架构、流程、发布状态或授权边界变化时，才同步更新 `.agents/context.md`、`.agents/decisions.md` 和 `.agents/open-items.md`；普通任务不要求更新这三个文件。
