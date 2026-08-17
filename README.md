# GKD

GKD 工作流的规范源码、版本管理与专属验证仓库。

GKD 本体设计与执行边界已经冻结，并于 2026-08-18 获得独立实施授权。开发按依赖有序的里程碑推进；生产用户目录安装与 AIO Coding Hub 接入仍是后续独立授权。

## 验证边界

- GKD 源码变更运行 GKD 专属验证。
- GKD release candidate 运行适用的 agent 与 live GitHub 验证。
- 消费项目的普通产品代码和文档变更不运行完整 GKD 测试。
