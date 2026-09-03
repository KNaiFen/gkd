# T6 执行交接：项目级施工记录归档

## 对应方案

- 依据 main 的 `.gkd/plan.md` T6 和 `plan-changes.md` revision `2026-09-03-r8`。
- 本文是当前 `t6-archive` worktree 的执行输入；执行 session 不把 `.gkd/plan.md` 当作施工指令。

## 目标

把“活动交接记录”和“长期历史记录”明确分层：施工期间使用目标项目 `.gkd/`，验收后由 main 在同一目标项目创建 `.gkd/archive/<task-id>/<date>-<revision>/`，保存本轮可读快照和摘要。本轮同时在 GKD 自身创建一份真实归档示例，证明规则不是只写在说明里。

## 可修改范围

1. `.agents/skills/gkd-main/SKILL.md`：补充归档时机、来源、目录结构、脱敏和 direct-main 取舍；保持自然语言协作，不增加状态机、门禁、合同、索引服务或常驻脚本。
2. `docs/manual-workflow.md`：把归档的实际操作顺序写清楚，明确执行 worktree 的记录如何由 main 汇总到目标项目主工作树的 `.gkd/archive/`。
3. `README.md`：同步一段简洁的归档说明和长期记录用途，不重复完整协议。
4. `docs/templates/manual/archive-summary.md`：增加任务标识、来源 revision、用户可见结果和未验证风险字段，提醒不写本机绝对路径、令牌或运行时状态。
5. `.gkd/archive/t6-archive/2026-09-03-19e7514/`：创建本轮归档示例，至少包含 `summary.md`、`plan.md`、`plan-changes.md`、`execution.md`、`progress.md`、`review.md`。快照内容应来自本轮 GKD 记录；`summary.md` 使用模板并说明 T6 改动、验证结果和剩余真实外部验证风险。
6. `.gkd/progress.md`：追加 T6 执行事实、归档文件清单和验证命令，不改写历史 T1-T5 记录。

## 实现步骤

1. 阅读当前 `gkd-main`、手工工作流、README、归档模板和 `.gkd/` 记录，确认只补充归档规则，不改变路由、角色模型或授权边界。
2. 在 `gkd-main` 中说明：main 审查完成后，使用普通文件复制/整理把目标 worktree 的五份记录和摘要放入目标项目自己的 `.gkd/archive/<task-id>/<date>-<revision>/`；归档目录是普通 Markdown，不是运行时事实源，不反向修改活动记录。
3. 在手工工作流和 README 中同步同一规则，强调 worktree 内 `.gkd/execution.md`、`.gkd/progress.md` 是归档来源，main 的 `.gkd/plan.md`、`.gkd/plan-changes.md`、`.gkd/review.md` 是方案与验收来源。
4. 用模板创建 `summary.md`，整理本轮实际改动、原因、验证、验收和未验证范围；快照只写逻辑 worktree/分支/提交标识，不写本机绝对路径、令牌、账号或机器状态。
5. 创建归档示例目录并保存六份 Markdown 快照。快照可通过文件复制生成，但提交前检查其内容没有机器路径和敏感信息。
6. 在 `.gkd/progress.md` 记录事实，运行验证并停止；不要提交、合并、发布、清理 worktree 或启动其他代理。

## 验证

- `git diff --check`：无空白错误。
- `find .gkd/archive/t6-archive/2026-09-03-19e7514 -maxdepth 1 -type f -print | sort`：六份归档文件齐全。
- 归档内容扫描：不出现本机路径、凭据或被禁止的机器化机制（历史“不恢复”说明除外）。
- `rg -n '\.gkd/archive|execution\.md|progress\.md|summary\.md' .agents/skills/gkd-main/SKILL.md docs/manual-workflow.md README.md docs/templates/manual/archive-summary.md`：规则、来源和模板相互一致。

## 边界

- 归档不代表自动提交或发布；是否随目标项目提交仍由 PLAN 和用户授权决定。
- 真实跨项目复制、真实 GitHub API、真实 `agent_type` 调用属于环境验证，不在本轮伪造成功证据。
- 如发现归档内容需要改变功能范围或授权，记录到 `.gkd/progress.md` 并交回 main，不自行扩展。

完成后在 `.gkd/progress.md` 写明实际文件和验证结果，并通知 main 审查。
