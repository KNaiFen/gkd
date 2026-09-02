# Progress report

## Current state

旧自动化面已删除，manual-first 文档与唯一项目 Skill 已收敛并完成主代理审查。

## Completed

- 删除 canonical bundle、旧 CLI/runtime、JSON schemas、合同测试、任务/证据、watcher/probe、legacy workflow 和历史方案文档。
- 新建受跟踪的 `.agents/skills/gkd-main/SKILL.md`，内联执行提示、最小验证、审查与恢复边界。
- README、协议、模板和持久记录已改为只描述 manual-first；历史追溯改由 Git 历史承担。
- 消融后仅保留 16 个当前流程所需文件，删除未参与执行或交接的通用模板和治理说明。

## Verification evidence

- `git diff --check`：通过。
- `test ! -e canonical ... ! -e tests`：通过，确认所有旧执行目录均已移除。
- 旧入口名的精确检索：无匹配，退出码 1。

## Decisions

- 不用新的 executor Skill 替代旧合同；执行代理使用简短启动提示词和任务计划。
- 不保留可执行的旧 pack、CLI、schema 或合同测试；历史由 Git 历史保留。

## Blockers and risks

- 旧自动化实现只可从 Git 历史恢复；当前工作树不再提供兼容运行路径。

## Next step

提交本次已审查的工作流收敛变更。
