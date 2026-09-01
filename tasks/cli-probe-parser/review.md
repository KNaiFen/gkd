# Review

## 结论

主代理审查通过，已合并到 `refactor/manual-first-workflow`。

## 变更范围

- current `0.152.0` direct JSONL parser 继续以官方外层生命周期事件为唯一事实边界。
- current `thread.started`、父/子 rollout identity 和 parsed adapter metadata 采用
  fail-closed 校验，缺失或漂移返回 `UNSUPPORTED_ROLLOUT_FORMAT`。
- `turn.failed` 被计为 terminal lifecycle，同时保留脱敏 host error；历史
  `0.147.0` payload wrapper、spawn/task/fork 与 child terminal 语义保持不变。
- 未新增 `subagent.started`、`task.completed` 顶层事件，也未从无 capture 的
  collaboration item 字段推导 spawn 或身份关系。

## 验证

- handshake parser 专项（含本轮回归）：27/27 通过。
- role-routing 全量：81/84 通过；剩余 3 项是 manual-first 默认安装面缺少旧
  `gkd-role` CLI/manifest 的既有失败。
- 默认 verifier：441/450 通过；其余失败来自 manual-first 默认 bundle/旧 workflow
  与 legacy packaging 断言不一致，另有既有 runtime bridge/import 夹具问题；未改变
  本任务代码或旧兼容语义。
- bundle `validate-repo`、`generate`、隔离 install/verify、`compileall` 和
  `git diff --check` 均通过。
- 未修改 MCP、app-server watcher、turn/steer、生产 `~/.codex`、AIO、GitHub、Secrets、
  runner 或 release。

## 主代理复核

- 已核对 current parser 没有新增未经证实的顶层协作事件，`thread.started` 身份缺失/漂移会进入明确 unsupported。
- 已核对 `turn.failed` 只补充 terminal 生命周期事实，不改变旧 wrapper 的 spawn/task/fork 读取路径。
- 已接受默认 verifier 的 9 项已知 legacy/manual-first 边界失败；它们没有由本阶段变更引入，专项与仓库校验均通过。
