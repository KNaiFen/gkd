# 主代理审查

## 当前审查（PLAN r10.6 / execution r10.6 / head 7b176d6）

状态：返工

- 独立验收发现：PLAN 要求的 plan-only/批准执行、材料性变更重新授权、delegated/direct-main 收尾和 review revision 演练没有可审计记录；当前 progress 只有静态检查，不能据此宣称成功标准已验证。
- CI Skill/role 要求调用方显式传 `--interval 30 --timeout 3600`，但脚本默认仍为 `10/300`；规范来源和 `interval` 的变更授权需要明确，避免直接调用产生不一致。
- 收尾顺序先删除 tracked 活动记录，再检查 clean 状态，没有定义 cleanup commit/合并步骤，无法同时保留归档并恢复干净 main。
- `AGENTS.md`、`README.md` 和手工流程仍有“当前 Codex 已配置角色/一个执行子代理”等泛化措辞，且 `gkd_accept` 可启动条件未重复已批准 delegated 前置条件，存在绕过命名角色和 plan-only 闸门的风险。
- `.agents/context.md`、`.agents/decisions.md` 仍用“可归档”描述成功收尾，弱化了 delegated 成功路径的强制归档要求；`docs/adr/002-manual-first-workflow.md` 也有未纳入本轮文件表的泛化角色措辞，需要决定是否同步。
- C 节成功标准写成对真实老项目执行清理，但本轮只加入临时 Skill，未获授权对真实老项目删除；当前标准与范围不一致。
- 清理 Skill 需要明确删除已确认旧机制的活动引用，而不仅是已失效链接。

## 决定

角色预设已完成静态审查；整体计划已按用户要求补充到可施工粒度，并已将 GKD 明确定位为完整的项目开发工作流。T1、T2、T3、T4、T5、T6 已通过独立验收并合入主分支，最终归档已完成。

## 历史审查（T1-T6）

状态：已被 r10.6 取代（superseded）

## 审查结论

- 当前计划保留 manual-first 和 worktree 交接，不把“自动路由”误解为无授权的自动写入或自动发布。
- 执行/验收角色固定为 `gpt-5.6-sol` / `xhigh`，CI 监控角色固定为 `gpt-5.6-terra` / `high`；提示词、sandbox 和禁止嵌套边界位于项目 `.codex/agents/` 预设。
- GitHub 长流程监控收敛为一个只读、无状态、可复用的脚本，避免恢复旧 watcher 或让每次 session 临时构造轮询。
- 需求问答与项目适配作为新 Skills 设计；历史没有可直接恢复的对应实现，计划已如实标注。
- 施工前 PLAN 现在应说明现状、技术栈、实现思路、文件/符号、验证和授权边界；复杂分支才写伪代码，main 可根据事实灵活调整，不把文档变成门禁或状态机。
- `execution.md` 位于 worktree，由执行 session 使用；`plan-changes.md` 由 main 追加记录计划调整；任务完成后可归档到目标项目 `.gkd/archive/`。
- 需求问答、项目适配和 CI 优化已明确为主流程的附属能力，不能绕过 PLAN、用户确认、worktree 施工或 main 审查。
- T1 验收确认 `.gkd/` 活动记录、execution-only 交接、计划变更追溯和角色提示词已一致；动态 role spawn/worktree 隔离仍留作后续端到端风险。
- T2 验收确认监控脚本只读、无状态、覆盖目标解析/终态/错误/超时；真实 GitHub API 未验证。
- T3 验收确认需求问答只针对材料性缺口，完整请求不机械提问，未引入状态文件。
- T4 验收确认项目适配和 CI 优化均证据化只读调查，资料不足时只询问少量关键事实，不引用固定 AIO 路径。
- T5 验收确认 README、手工工作流和 ADR 已统一使用目标项目 `.gkd/` 活动记录；11 项 GitHub 监控测试、文档交叉引用和角色配置静态检查通过。
- T6 的 `gkd_accept` 最终复核确认归档规则、脱敏边界和六份快照均符合计划；main 已在本审查结论确定后新建 `.gkd/archive/t6-archive/2026-09-03-r9-final/`，保留首轮 `.gkd/archive/t6-archive/2026-09-03-19e7514/`，最终目录中的 `review.md` 与 `summary.md` 反映通过结论。
- 归档扫描中的 `~/.codex`、`token` 等命中仅是规则/命令自描述，没有真实本机路径、凭据或令牌；最终摘要已如实说明这一点。

## 尚未验证

- 当前 Codex 原生角色配置是否能通过本运行时暴露的 `agent_type` 调用项目级命名角色。
- `gkd_execute` 是否能以目标角色配置在 main 指定的 sibling worktree 中实际执行。
- GitHub 监控脚本的真实远程目标解析、轮询和终态报告。
- 新路由、问答、项目适配、监控和验收的真实跨进程端到端协作。
- 不同项目目录约定下的跨项目归档体验仍未实际演练；本仓库内的归档目录、快照清单和最终结论已验证。
