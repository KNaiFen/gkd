# Main-agent review

## Decision

Approved.

## Findings

- `gkd-main` 现在区分 `direct-main`、默认的 `delegated/manual` 和用户明确选择后的 `delegated/automatic`。
- 自动入口要求 main 读取当前可用配置角色并真实调用 `spawn_agent`，同时保留 `fork_turns=none` 和单一 worktree 写者边界。
- 手动入口、自动入口和返工轮次都继续使用 `plan.md`、`progress.md`、`review.md` 与 Git diff；没有恢复旧任务状态机或机器合同。
- 文档明确禁止自动失败时静默改由 main 施工，也没有把角色、模型或权限写死在 Skill 中。

## Verification

- 执行 session 提交前后的 `git diff --check`：通过。
- 自动入口角色探针：main 真实调用 `spawn_agent`，传入 `agent_type=worker` 和 `fork_turns=none`；子代理 `/root/gkd_role_probe` 正常返回并未修改文件。
- 自动执行施工 session：main 真实启动 `/root/gkd_execution`，子代理在声明 worktree 中完成文档修改并提交 `6b0d178`；main 等待其终止后审查 diff。
- 旧入口检索：旧 automatic route、`gkd-task`、`gkd-role`、runtime bridge 和 fixed-head 仅作为边界说明出现，没有新增可执行入口。

## Remaining risk

- 用户级 `/Users/knaifen/.codex/skills/gkd-main` 尚未同步；仓库改动完成后需要单独执行安装同步。
- 自动角色配置由当前 Codex 运行时提供，仓库不维护角色定义；不同安装环境的角色可用性仍需在启动时报告。
