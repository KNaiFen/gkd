# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: 里程碑 1、M2-A 与 M2-B 门禁已完成；M2-B 用户确认绑定执行 bundle digest `5b115a918d8a5241551b0be8dac657a448e1b912815493e1988007b1f4ed1880`。自动路线审计确认当前 canonical payload 尚缺 project-scoped role staging 和 trusted-main spawn→activation→claim 编排入口，仓库根也没有可供 fresh session 发现的 `.codex/agents`；因此不能直接启动 M3 executor，且不得退回 generic worker。下一任务为人工顶层 `GKD-M2-C automatic runtime bridge`，只补上述启动桥、固定执行 bundle 与候选输出 bundle 的边界及过时文档；M2-C 合并并从 staged project 启动 fresh main 后，M3-A/B/C 才按既有授权自动执行。M3 已拆为 A fixed-head CI/policy、B 资源与防泄漏 core、C 两项新 Skill/review core。生产安装、AIO、付费 runner、Secrets 和计划外 GitHub 设置继续未授权。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
