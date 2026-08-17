# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: GKD本体计划、hybrid B路线及双public GitHub仓库布局已批准；`KNaiFen/gkd`用于源码/CI/发布，`KNaiFen/gkd-sandbox`用于L4隔离演练。两个远程仓库尚未创建，实施与GitHub写操作尚未授权；下一步确认外部动作模式。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
