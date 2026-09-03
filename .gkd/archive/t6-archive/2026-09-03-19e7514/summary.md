# GKD task archive

## Task

目标项目：GKD。任务逻辑 ID：`t6-archive`。归档日期：2026-09-03。来源 PLAN revision：`2026-09-03-r8`。

### Task identifier

`t6-archive` / `2026-09-03-19e7514`

### Source revision

来源记录 revision：`2026-09-03-r8`；逻辑 worktree：`t6-archive`；分支：`task/t6-archive`；代码 revision：`19e7514`。

## What changed

- `gkd-main` 增加归档时机、来源、目录结构、脱敏规则和 `direct-main` 取舍，保持归档为普通 Markdown 长期记录。
- 手工工作流补充 main 从 worktree 与目标项目 `.gkd/` 汇总五份记录、填写摘要、检查脱敏并记录验证的实际顺序。
- README 同步简洁归档说明；归档摘要模板增加任务标识、来源 revision、用户可见结果和未验证风险字段。
- 创建本轮六份归档文件：`summary.md`、`plan.md`、`plan-changes.md`、`execution.md`、`progress.md`、`review.md`。

## User-visible result

目标项目现在有一份可独立阅读的 `.gkd/archive/t6-archive/2026-09-03-19e7514/` 施工记录快照，能说明 T6 的目标、取舍、文档改动、验证和后续风险。归档不自动提交、推送、合并或发布，交付动作仍由 PLAN 和用户授权决定。

## Why

PLAN revision `2026-09-03-r8` 要求把执行交接材料纳入目标项目的长期记录，同时维持 manual-first、自然语言协作和用户控制边界，不恢复机器化流程。

## Verification and review

- `git diff --check`：通过。
- 归档文件清单和文档交叉引用：通过；六份快照齐全，规则、来源和模板字段均有引用。
- 归档敏感路径/凭据扫描：无本机路径或凭据命中；历史“不恢复”边界说明中的机制关键词保留。
- 主代理尚未完成独立审查；本文件记录施工事实，不代替 `review.md`。

## Unverified risks

- 未进行真实跨项目复制、真实角色启动或外部 GitHub API 验证；这些仍属于环境级风险。
- 本轮只验证本仓库内的 Markdown 快照、脱敏和文档一致性，没有验证目标项目不同目录约定下的归档体验。

## Related records

- 活动记录：`.gkd/plan.md`、`.gkd/plan-changes.md`、`.gkd/execution.md`、`.gkd/progress.md`、`.gkd/review.md`。
- 使用模板：`docs/templates/manual/archive-summary.md`。
