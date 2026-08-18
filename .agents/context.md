# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: `GKD-M0-A` 首个fixed head `0f69a4ad34d095d70f6d5e5ed93569193ad75578` 的3项阻塞finding已由implementation/evidence commit `3bab17697735adcf85e1214d6580966a7e896f47` 修复；foundation 53项、M-1B 47项、M-1C negative 15项及双次确定性证据通过，development version `0.0.0-dev.0`，content digest `0b8b2487640ff2c78360a18e7f24304f72a8e8c8b5cbd1317ef833c323726228`。PR #4等待新固定head独立验收；不得合并或开始M0-B/里程碑1。D2保持 `unsupported`，manual-only继续生效。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
