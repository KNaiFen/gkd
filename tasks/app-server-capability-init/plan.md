# app-server capability 初始化适配

## 目标

校准 GKD app-server 探针对 initialize/capability 的假设，使能力事实只来自当前 CLI 的真实响应或已登记历史证据；缺失、漂移或未捕获的能力不再被默认填充为支持。

## 范围

- app-server JSON-RPC 初始化及 watcher capability 读取路径
- 相关 current/legacy 夹具、测试、contract catalog 与脱敏 evidence
- 本任务 `progress.md`、`review.md` 和必要 `.agents/` 状态记录

## 约束

- 不恢复 automatic watcher，不修改 MCP 协议协商或 CLI JSONL parser。
- 只使用已有 `0.152.0` compatibility baseline 与 `0.147.0` 历史证据；没有真实 capture 的 capability 保持 compatibility-only/unsupported。
- 不修改 `turn/steer`；它仍是整个修复计划的最后阶段。
- 不写生产 `~/.codex`、AIO、GitHub、Secrets、runner 或 release。
- 保持旧历史负向测试语义，不保存原始敏感 payload。

## 完成标准

1. 初始化响应中 capability 的存在、类型和支持状态有明确解析规则。
2. 缺失或未知 capability 不再静默视为可用，并有稳定负向测试。
3. 历史已登记初始化响应仍可读，current baseline 不被宣称为 watcher 可用。
4. 相关测试、仓库校验、bundle 生成和 `git diff --check` 通过，证据写入进度和审查文档。
