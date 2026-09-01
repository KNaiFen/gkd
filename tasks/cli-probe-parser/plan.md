# CLI 探针解析适配

## 目标

根据当前 Codex CLI `0.152.0` 的 `codex exec --json` 事实，收紧 CLI 探针解析边界：正确读取 JSONL 外层生命周期事件，保留历史 `0.147.0` wrapper 兼容；对无法由真实 capture 证明的协作事件、字段或关系返回可观测的 unsupported，不再用猜测值填充子代理事实。

## 范围

- CLI probe/parser 源文件
- 当前/历史 JSONL 夹具、归一化测试和 contract catalog
- 本任务 `progress.md`、`review.md`、脱敏 evidence 及必要 `.agents/` 状态记录

## 约束

- 当前事实仅限官方 `thread.started`、`turn.started`、`item.started`、`item.completed`、`turn.completed`、`turn.failed`、`error` 等外层事件；不得发明直接的 `subagent.started`、`task.completed` 等顶层事件。
- `item` 内部协作字段没有真实脱敏 capture 时，归一化为 unsupported，而不是猜测 spawn/child 关系。
- 不修改 MCP、app-server watcher、turn/steer 或生产 `~/.codex`。
- 保留 `0.147.0` 历史正向和负向语义，避免重写已有证据。

## 完成标准

1. 当前 JSONL 夹具仅使用已证实的事件外壳并可稳定解析。
2. 未知事件、缺失身份或推测协作字段均有明确 unsupported/blocked 结果和测试。
3. 历史 wrapper 与错误关联测试继续通过。
4. 相关测试、仓库校验、bundle 生成和 `git diff --check` 通过，并将证据写入进度和审查文档。
