# Subagent Event Adapter

## 工作目标

为 GKD legacy-automatic/historical lane 重写子代理 rollout/JSONL 事件归一化，避免把旧版 `item.completed`、`payload.type=function_call`、`namespace=agents` 和固定 terminal 字段当作永久协议。当前阶段只提高事件事实解析的版本意识和 fail-closed 行为，不恢复 automatic route。

## 工作目录

当前 Git worktree。

## 行为约束

- 只修改事件解析、归一化、相关 fixture/测试和必要说明。
- 保留旧 `0.147.0` historical fixture/evidence 的可读取性，不重写历史事实。
- 当前/未知 CLI 事件结构不得被猜测为成功或 `spawnCount=0`；未知结构返回明确 unsupported。
- 不修改 MCP 协商、CLI 文本 parser、app-server initialize、watcher 控制逻辑或 `turn/steer`；后者必须留到最后阶段。
- 不修改生产 `~/.codex`、AIO、GitHub、tag/Release，不把 automatic 能力放回默认 bundle。
- 不新增普通 manual-first 任务所需机器合同或状态副本。
- 持续更新本目录 `progress.md`，完成后停止等待主代理审查。

## 范围

- `tests/role_routing/handshake_preflight.py`
- `tests/role_routing/test_handshake_preflight.py`
- `tests/role_routing/run_contracts.py`
- `canonical/payload/lib/gkd_role/bridge.py` 中直接相关的归一化代码
- 相关脱敏 fixture、兼容记录和文档

## 非目标

- 不改变 `fork_turns`、agent type、task name 的既有约束语义。
- 不处理 MCP 日期/metadata。
- 不处理 CLI 文本错误解析。
- 不处理 initialize 能力确认。
- 不处理 `turn/steer` 的退役或替代。

## 完成条件

1. 原始事件解析与内部事实归一化分层，记录 CLI/version/source。
2. 已知历史 fixture 和当前版本 fixture 均能得到稳定归一化结果。
3. 字段漂移、未知包装、缺失 terminal/parent-child 关联均返回 unsupported，而不静默判定成功。
4. 既有历史合同和默认 manual-first 入口行为不变。
5. 相关最小测试及 `git diff --check` 通过。
6. `progress.md` 和 `review.md` 记录实际结果，完成后停止。
