# Progress

## 当前状态

第二阶段返工已完成，等待主代理审查。

## 已完成

- 在 `tests/role_routing/handshake_preflight.py` 增加 raw rollout/host JSONL adapter：
  解析层显式记录 `schemaVersion`、CLI 版本、source 和 format，归一化层继续只输出原有最小 host facts。
- 保留 `0.147.0` payload-wrapped historical rollout；current `0.152.0` fixture 改为官方
  `thread.started`、`turn.started`、`item.*`、`turn.completed` 外壳。
- current parser 只接受已捕获的 direct JSONL 外壳和已知 item 类型；顶层
  `function_call`/`subagent.started`/`task.completed` 不再被当成当前协议。
- 没有真实脱敏 capture 支撑的 `collab_tool_call` 具体字段不做映射，current rollout/host
  normalizer 明确返回 `UNSUPPORTED_*`；未知包装、字段漂移、线程身份漂移和缺 terminal 继续快速失败。
- 旧 spawn/task/fork、child 绑定错误和多个 spawn 负向合同仍由 legacy facts/handshake 层判定 blocked。

## 约束提醒

只处理子代理事件归一化；MCP、initialize 和 `turn/steer` 暂不处理。

## 验证

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:canonical/payload/lib:. python3 -m unittest tests.role_routing.test_handshake_preflight`：22 项通过。
- role-routing 全量回归：79 项中 76 项通过；3 项失败来自 manual-first 分支默认 payload 已移除 `gkd-role`/旧 role-routing manifest 的既有 packaging 边界，与本阶段事件适配无关。
- `git diff --check`：返工提交前运行。
