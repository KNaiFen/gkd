# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: 里程碑 1 已完成并清理；M2-A F-005 保持已整改且未变更。F-004 v3 改为验证正常生产使用环境：parent 读取正常用户 provider/auth/model routing，临时项目提供固定 `gkd_executor`；live command 已移除 `--ignore-user-config`、parent `--model` 和 effort override。M2 63 项双 evidence 及旧回归 219 项全通过；但 `codex-cli 0.147.0 --strict-config` 因正常用户配置未知字段 `disable_response_storage` 在 project role discovery 前 fail-closed，分类 `USER_CONFIG_PARSE_FAILED`，模型调用/live attempt 均为 0，生产/AIO 保护面不变。交付继续 `blocked`；未具备新 live 授权条件，M2-B、auto route、生产安装、AIO 和里程碑 3 继续禁用/未授权。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
