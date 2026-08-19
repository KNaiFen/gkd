# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: 里程碑 1 已完成并清理；M2-A F-005 最小整改已移除 canonical/installable activation writer 与 M1 fixture evidence seam，测试 seam 仅留在 tests，正常 CLI/library claim/recovery 无 host attestation 时 fail-closed 且不改 runtime/tracked bytes。全部短合同与双 evidence 通过。本轮新增授权的本机握手在严格静态发现通过后只启动一次；宿主在 parent turn 前以 HTTP 400 拒绝 ChatGPT account 使用 `gpt-5.6-sol`，分类 `HOST_MODEL_UNSUPPORTED_FOR_CHATGPT_ACCOUNT`，未产生 custom-role/effective-config/terminal 事实。交付继续 `blocked`；M2-B、auto route、生产安装、AIO 和里程碑 3 继续禁用/未授权。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
