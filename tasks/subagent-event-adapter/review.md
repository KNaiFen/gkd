# Review

## 结论

返工完成，等待主代理审查。

## 变更范围

- raw rollout/host JSONL 解析与内部 facts 归一化分层，解析结果携带 `schemaVersion`、`cliVersion`、`source`、`format`。
- 旧 `0.147.0` payload wrapper 保持可读；新增严格 `0.152.0` direct-event 脱敏 fixture。
- 未知 wrapper、格式混用、版本/格式不匹配和 spawn 字段漂移显式返回 `UNSUPPORTED_*`，避免静默 `spawnCount=0` 或缺角色事实。
- 未修改 MCP、CLI 文本 parser、app-server initialize、watcher 控制、`turn/steer`、生产/AIO 或默认 bundle。

## 验证

- 握手专项：18/18 通过。
- role-routing 全量：74/77 通过；剩余 3 项是当前 manual-first 默认 payload 缺少旧 `gkd-role` CLI/manifest 文件的既有失败，不由本阶段改动引入。
- 交接前另行运行 `git diff --check`。

## 阻塞问题

- 已将 `current-parent.jsonl`/`current-child.jsonl` 改为官方外层事件：`thread.started`、`turn.started`、`item.started`/`item.completed`、`turn.completed`。
- current parser 现在拒绝顶层 `function_call`、`subagent.started`、`task.completed` 等未证实事件；保留旧 `0.147.0` payload wrapper 读取。
- current normalizer 只输出 thread/turn/item 外壳事实；协作 item 具体字段没有真实脱敏 capture 支撑时明确返回 `UNSUPPORTED_*`，不发明 spawn 映射。
- 已覆盖当前 fixture 的稳定 blocked 归一化、未知当前事件、协作 item、线程身份漂移和缺 terminal 负向合同。

## 返工要求

1. 基于官方 JSONL 外层事件重做当前 fixture 和 parser；保留旧 `0.147.0` payload wrapper 读取。
2. 为当前格式记录来源和版本，但不声称未捕获的协作 item 字段已支持。
3. 旧负向语义（错误 task/fork、多个 spawn、child 绑定错误）仍由最小 facts/handshake 层判定 blocked；结构性漂移才进入 `UNSUPPORTED_*`。
