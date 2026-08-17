# GKD

GKD 工作流的规范源码、版本管理与专属验证仓库。

当前仓库只完成初始化。完整设计仍在 AIO Coding Hub 的工作流实战审查任务中逐项确认；在全部决定冻结并获得单独实施授权前，不迁移生产 Skills、agents 或脚本。

## 验证边界

- GKD 源码变更运行 GKD 专属验证。
- GKD release candidate 运行适用的 agent 与 live GitHub 验证。
- 消费项目的普通产品代码和文档变更不运行完整 GKD 测试。
