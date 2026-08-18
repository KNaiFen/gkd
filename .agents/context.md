# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: `GKD-M0-A` PR #4 head `0f69a4ad34d095d70f6d5e5ed93569193ad75578` 已交付，但固定head独立验收发现3项阻塞finding：canonical metadata mode未真实绑定、evidence可在after快照后写入受保护根并虚报unchanged、污染扫描按裸用户名/任意`aio`子串误杀。原GPT-5.6 Sol / xhigh顶层execution session正在返工并重新取证；PR保持Draft，不得合并或开始M0-B/里程碑1。D2保持 `unsupported`，manual-only继续生效。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
