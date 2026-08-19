# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: 里程碑 1 已完成并清理；M2-A F-005 保持已整改且未变更。F-004 v4 继续验证正常生产使用环境：生成 project/role TOML 由 Python `tomllib` 严格解析，正常用户 provider/auth/model routing 通过非 strict app-server 到达预期 no-transport；live command 已移除 `--ignore-user-config`、parent `--model`/effort override 和 `--strict-config`。静态门证明 digest/trust/项目角色定义接受与非漂移，但不证明 activation；`modelInvocations=0`、`liveAttemptsConsumed=0`。v3 `USER_CONFIG_PARSE_FAILED` 保留为历史兼容性事实。F-004 与总体交付继续 `blocked`，等待新 fixed-head 的一次独立 live 授权；M2-B、auto route、生产安装、AIO 和里程碑 3 继续禁用/未授权。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
