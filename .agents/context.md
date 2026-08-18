# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: 里程碑 1 已完成并清理；`GKD-M2-A` 固定角色与路由核心已从 main `839974fbcd9114e5a5ad3b8fa1d4c58e68cb90ea` 建立独立 worktree `/Users/knaifen/Documents/Codex/gkd-worktrees/m2-role-routing-core`、branch `task/m2-role-routing-core` 和 Draft PR #6，planning head 为 `51fee63a8b600df4f94aa042ea42ef09e3b73986`，等待 GPT-5.6 Sol / xhigh 的人工顶层 execution session。M2 拆为 M2-A 确定性角色/路由核心与 M2-B fresh-runtime 一小时 live gate；M2-A 不运行真实一小时等待。development version 仍为 `0.0.0-dev.0`，当前已验收 M1 content digest 为 `fc96a10cb82b628bd14280e4e878417a3fbc7a1d560fac5a61bb7abe7f3c3024`。固定角色、可信 activation evidence 和实际一小时 `wait_agent` 门尚未通过，auto route 继续禁用；生产安装与 AIO 仍未授权。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
