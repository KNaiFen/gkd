# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: `GKD-M3-A` 已通过 accepted automatic route 的 exact claim 实现并推送至 PR #8。候选修复 shallow checkout 的 full-base 验证并移除对 `origin/HEAD` 的隐式依赖，同时保持 strict `.gkd/policy.json`、GitHub origin/base 一致性、installed fixed-head terminal monitor、标准 `GKD Verify` Actions job 与统一 `scripts/gkd-verify`；candidate output bundle digest 为 `0484095704599750df655bc6c92cf0b5829bc2c1ebb877aa3f3cd132cc29998f`，与 accepted execution bundle `1983f05b64860510bfb1af661e5458a6c7b660632479a33af46c27d35ff188d4` 分离。335 项版本化本地验证通过；29 项 M3-A 双 evidence 逐字节一致，evidence digest/file SHA-256 为 `22b72cd484492317b9dd3196a86e34edfd3f697dbf4b1d526ff90263fd6db4ba` / `4568aa0d8aafead6ca53c5d37d3cd8986be0c6d0dec3ffb59575c9f27c4158f5`，生产与 AIO 保护面不变。等待最终 delivery head 的 policy-backed CI 终态与 trusted-main 独立验收；M3-B/M3-C、生产安装、AIO、付费 runner、Secrets 和计划外 GitHub 设置继续未授权。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
