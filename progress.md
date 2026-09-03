# Progress report

## Current state

执行 session 双启动入口的文档、模板、规则和持久记录已完成，等待 main 审查。

## Completed

- 删除 canonical bundle、旧 CLI/runtime、JSON schemas、合同测试、任务/证据、watcher/probe、legacy workflow 和历史方案文档。
- 新建受跟踪的 `.agents/skills/gkd-main/SKILL.md`，内联执行提示、最小验证、审查与恢复边界。
- README、协议、模板和持久记录已改为只描述 manual-first；历史追溯改由 Git 历史承担。
- 消融后仅保留 16 个当前流程所需文件，删除未参与执行或交接的通用模板和治理说明。
- 已读取 `VISION.md`、计划、现有 Skill、流程文档、模板和持久记录。判定为仅补充原生 session 启动，不恢复旧 automatic route、JSON 合同或机器生命周期。
- 已检查目标 worktree：开始前工作树干净，当前分支为 `feat/execution-session-routing`。
- 已检查用户级 `~/.codex/skills/gkd-main`：仍为 manual-only 文案；已知项目目录中未发现第二份项目级 `gkd-main`。本轮只修改声明 worktree，用户级安装同步留给 main 的另行明确授权步骤。
- 已更新唯一项目 Skill、工作流文档、计划模板、README、AGENTS、VISION、ADR 与 `.agents/` 持久记录：保留 `direct-main`，将 `delegated/manual` 设为默认，并把 `delegated/automatic` 限制为用户明确选择后的原生子代理启动。

## Verification evidence

- `git diff --check`：通过。
- `rg` 检查目标文档：`direct-main`、默认 `delegated/manual`、用户明确选择后的 `delegated/automatic`、`spawn_agent`、`fork_turns=none` 和失败不降级边界均有明确表述。
- `rg` 检查角色配置：目标 Skill、文档和模板未写死角色名、模型或权限；均要求 main 读取当前 Codex 配置。
- `rg` 检查旧术语：仅在 ADR、规则和持久记录中作为已删除或拒绝恢复的边界出现，未新增 `gkd-task`、`gkd-role`、runtime bridge、offer/claim/receipt、CAS 或 fixed-head 的可执行入口。
- 自动入口的真实子代理事件尚未执行：本执行 session 的任务约束禁止启动其他代理，该验收由 main 在后续独立轮次完成。
- 构建、类型检查、lint 和业务测试未运行：变更仅为 Markdown 规则与模板，仓库未提供适用于此表面的专用检查。

## Decisions

- 不用新的 executor Skill 替代旧合同；执行 session 使用简短启动提示词和任务计划。
- 不保留可执行的旧 pack、CLI、schema 或合同测试；历史由 Git 历史保留。
- 自动启动仅在用户明确选择后发生，且由当前 Codex 配置决定执行角色；Skill 不写死角色、模型或权限。

## Blockers and risks

- 自动入口尚未在本执行 session 中手工调用：本任务约束禁止启动其他代理，自动事件验证由 main 在后续独立验收轮次完成。
- 用户级 `gkd-main` 安装副本尚未同步：计划要求仓库改动完成后另行执行明确授权的同步，当前执行 session 无该授权。

## Next step

main 审查本 worktree 的 diff、`plan.md` 与本报告；随后按用户授权决定用户级安装同步和自动入口手工验收。
