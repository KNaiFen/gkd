# r10.6 执行交接

## 任务身份

- PLAN revision：r10.6
- 路由：`delegated/automatic`
- 当前 worktree：本文件所在 worktree
- 执行角色：`gkd_execute`
- 用户授权：按 r10 开始施工；施工完成且收尾条件满足后，主代理可清理本轮本地任务分支与远端任务分支。

## 目标

把 r10 规划中的流程约束落到 GKD 仓库：CI 等待必须由专用只读子代理执行，拟 PLAN 与施工授权严格分离，提供一次性旧版 GKD 清理 Skill，并补齐详细报告、归档、worktree/分支清理和审查 revision 规则。

## 允许修改的文件

只修改下列文件；如发现需要扩大范围，停止并在 progress.md 报告，不自行修改计划：

- `.agents/skills/gkd-main/SKILL.md`
- `.agents/skills/gkd-ci-monitor/SKILL.md`（新增）
- `.codex/agents/gkd_ci_monitor.toml`
- `.agents/skills/gkd-legacy-cleanup/SKILL.md`（新增临时 Skill）
- `docs/manual-workflow.md`
- `README.md`
- `AGENTS.md`
- `docs/templates/manual/plan.md`
- `docs/templates/manual/archive-summary.md`
- `docs/templates/manual/closeout-report.md`（新增）
- `.agents/context.md`
- `.agents/decisions.md`
- `.agents/open-items.md`

主代理保留并负责更新当前任务的 `.gkd/plan.md`、`.gkd/plan-changes.md`、`.gkd/review.md`；执行代理不得修改、删除或归档这些文件，也不得删除本 worktree 的 `.gkd/execution.md` 或 `.gkd/progress.md`。

## 实施要求

1. 先阅读本仓库适用的 `AGENTS.md`、现有目标文件和 r10 草案，保持 manual-first、worktree 交接和无兼容模式的既有方向。
2. 为 CI Skill 写清：单一目标、固定 `scripts/gkd-github-watch` 入口、只读边界、缺失/漂移/认证失败即阻塞、默认 `--interval 30 --timeout 3600`、主代理一次性等待和终态处理；不得引入 `gh ... --watch` 替代路径。
3. 在 `gkd-main`、手工流程和模板中明确 `plan-only` 不创建 worktree/代理/代码/提交/推送/合并/发布/清理；只有用户明确批准“按此 PLAN 开始执行”后才进入 delegated 路由，材料性变更要追加 plan-changes 并重新授权。
4. 新增临时 `gkd-legacy-cleanup` Skill：先只读盘点并分类，再按明确授权删除已确认的旧 GKD 可执行入口/Skill/脚本/状态和引用；保留普通业务及历史归档，不触碰生产用户目录和当前 GKD 活动记录，不设计兼容模式。
5. 补齐详细 closeout report 模板和归档字段；写清 delegated 先 `gkd_accept`、再 main 审查、归档后清理活动记录、清理 worktree/本地与经授权的远端任务分支、恢复干净 main 的顺序。审查采用当前 revision 块和旧结论一行 superseded 标记。
6. 同步项目说明、持久记录和 role TOML，避免与现有角色边界冲突。不要恢复旧自动路由、状态机、固定 head、watcher、bundle 或发布流程。

## 验证

- `git diff --check`
- 对新增/修改文档做交叉引用和规则一致性检查，确认 CI 入口、plan-only 闸门、收尾顺序、审查 revision 用语一致。
- 检查不存在直接 `gh pr checks --watch`、`gh run watch` 或临时轮询流程性引用；可运行现有静态/文档测试时运行并记录结果。
- 验证新增文件存在，未超出允许修改范围。

## 停止条件

遇到计划含义冲突、文件范围不足、无法判断 role TOML 的运行时语义或需要修改非允许文件时，停止施工并把事实、路径和建议写入 progress.md，等待主代理处理。不要启动其他代理，不做 CI/发布/远端 Git 操作，不合并、不验收、不清理现场。
