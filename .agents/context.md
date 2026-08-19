# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: 里程碑 1、M2-A 与 M2-B 门禁已完成；M2-B 用户确认绑定执行 bundle digest `5b115a918d8a5241551b0be8dac657a448e1b912815493e1988007b1f4ed1880`。自动路线审计确认 canonical payload 尚缺 project-scoped role staging 和 trusted-main spawn→activation→claim 编排入口，因此已登记最后一次人工顶层 `GKD-M2-C automatic runtime bridge`：fixed base `302f60d96c2f81e85052025f814593015a436bd7`，worktree `/Users/knaifen/Documents/Codex/gkd-worktrees/m2-automatic-runtime-bridge`，branch `task/m2-automatic-runtime-bridge`，planning/offer head `77331cfa33575fb9b32c0c58f2c5894f67f1e316`，PR #7，状态 `awaiting_claim`/revision 4。M2-C 只补启动桥、执行/候选 bundle 边界和过时文档；合并并从 staged project 启动 fresh main 后，M3-A/B/C 才自动执行。M3 已拆为 A fixed-head CI/policy、B 资源与防泄漏 core、C 两项新 Skill/review core。生产安装、AIO、付费 runner、Secrets 和计划外 GitHub 设置继续未授权。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
