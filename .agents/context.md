# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: 里程碑 1 和 M2-A 已完成并清理；M2-A fixed head `b579926aaff50d40b462e7f21cf91c9709eeb3a3` 已以 merge commit `9351d628d198ec8638311901cf288abadc643a42` 进入 main。用户于 2026-08-20 明确确认 M2-B 的 `wait_agent(timeout_ms=3600000)` 与 child early-final 已验证可用，并要求不再定位 session 或重跑 live gate；该确认已绑定 M2-A bundle digest `5b115a918d8a5241551b0be8dac657a448e1b912815493e1988007b1f4ed1880` 固化于 `tasks/m2-one-hour-live-gate/acceptance.md`。里程碑 2 因此完成：manual 仍为默认，M3/M4/M5 可按既有授权显式使用专用 `gkd_executor` automatic route；exact bundle、role/config、offer/claim、activation 或 wait gate 任一漂移仍须 fail-closed。生产安装、AIO、付费 runner、Secrets 和计划外 GitHub 设置继续未授权。长会话复盘见 `tasks/m2-role-routing-core/retrospective.md`。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
