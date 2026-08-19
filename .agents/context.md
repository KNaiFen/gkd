# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: 里程碑 1 已完成并清理；M2-A F-005 已在 implementation/evidence fixed head `010746ba5eda61bde22db0ca4b08f5ff647a698d` 修复：canonical/installable payload 不再暴露 activation writer，安装态 claim 在缺少候选不可访问 host attestation 时 fail-closed。全部 M2/L2 与保留合同通过；唯一获授权本机握手在临时配置准备阶段以 `HANDSHAKE_SETUP_FAILED` 中止，未建立可信 custom-role/child/parent evidence，因此交付继续 `blocked`。M2-B、auto route、生产安装、AIO 和里程碑 3 继续禁用/未授权。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
