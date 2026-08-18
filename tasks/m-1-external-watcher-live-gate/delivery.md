# GKD-M-1C 交付

## 终态

- Outcome: `unsupported`
- 实现/证据 commit: `bf18ad645026e8055803bed1055a155a980bee42`
- Final head: 本文件所在的 PR #3 live head；GitHub 是最终 40 位 SHA 的事实源，执行 session 在固定 head 交付中回报精确值。
- PR: `https://github.com/KNaiFen/gkd/pull/3`
- Fixed base: `c438855961760707c119cb172be97ae9030a4508`
- Synced main: `69880eb9fb2ab9b78ddcaee71614d160dff0b630`
- Auto route: 保持禁用；manual handoff 继续可用。

真实 fresh Codex parent 在四个固定场景中均启动了进程级 MCP server。模型没有按固定顺序先调用 native `spawn_agent`，而是直接调用或跳过 live gate，因此无法建立无猜测的 parent/child/session/turn 绑定，四个场景均不能进入 watcher 状态机。required live facts 不足时按冻结规则输出 `unsupported`，不得从实际 MCP transport 已启动推导 watcher 支持。

## 固定运行时

- `codex-cli`: `0.147.0`
- Model / reasoning: `gpt-5.6-sol` / `xhigh`
- Runtime/schema SHA-256: `ea75b7760483b70be4535b2d966e1ccd92035f6c71362a79f2cb2d54d0088bcf`
- Live evidence schema: `1`
- MCP tool timeout: `43200` seconds
- Watch request max wait: `43200000` ms
- 证据类型: `combined_timeout_contract_not_soak`；未声称 12 小时墙钟 soak。
- M-1B: 47 项通过，test-ID digest `2e61a1c79e02515de194ac30c9999de0f75f60bca1a1fac207d909f75e19b965`。

## Required live gate

| Gate | 结果 | 证据边界 |
| --- | --- | --- |
| 1 实际接线与跨进程身份 | fail | `cross_process_identity_not_proven`；无 child binding。 |
| 2 健康静默 | fail | `healthy_silence_not_proven`；未进入健康周期。 |
| 3 正常终态去重 | fail | `normal_terminal_deduplication_not_proven`；无正常 child 终态，且 allowlist trace 不能安全区分 native mailbox/final 与 watcher completion。 |
| 4 异常顺序与作用域 | fail | `safe_real_system_error_not_proven`；未建立可控制 child。 |
| 5 expected-turn CAS | fail | `live_expected_turn_rejection_not_proven`；未到达绑定 parent steer。 |
| 6 编排器故障唤醒 | fail | `orchestrator_failure_wakeup_not_proven`；未进入 watcher-owned transport。 |
| 7 12 小时合同组合 | fail | Fresh session 实际接受并发起 43200 秒配置下的 MCP call，但 43200000ms watch request 未进入状态机，组合证据不足。 |
| 8 父上下文 trace | fail | `required_parent_trace_missing`；无健康窗口可证明。 |
| 9 数据与清理 | pass | 最终运行无原始正文/标识/绝对路径；所有已知 thread/进程清理，临时目录删除，生产配置前后快照匹配。 |

## 验证证据

- `evidence/m-1-external-watcher-live-gate/live-results.json`
- Outcome: `unsupported`
- Normalized digest: `bc3237802b839565b74665381a6df2cdbf920a13d9cbb48f8daddd9d29adf610`
- 规范化范围: `decision_gates_and_safety_contracts`
- 最终代码连续两次完整四场景运行得到相同 outcome、gate 状态和 normalized digest；完整 trace 保留非决定性的中间事件差异。
- 四场景最终失败分类均为 `binding_not_observed`。

执行命令：

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /opt/homebrew/bin/python3 tests/watchdog/run_contracts.py --output evidence/m-1-external-watcher-core/contract-results.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /opt/homebrew/bin/python3 -m unittest discover -s tests/watchdog/live -p 'live_test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /opt/homebrew/bin/python3 probes/app-server-watcher/live_probe.py --output evidence/m-1-external-watcher-live-gate/live-results.json
git diff --check
```

结果：M-1B 47/47 通过；live negative 15/15 通过；live probe 正常退出并生成二选一终态；`git diff --check` 通过。未运行大型 build、Rust、Tauri 或无关测试。

## 配置、清理与残余风险

- `~/.codex/config.toml` 前后 SHA-256 均为 `f5123b569314e0a260ebcdf5b95c5d32cad634df6fd3cd2de5a9dd7df342fd4a`，mtimeNs 均为 `1787025893679374153`。该证据准确表示前后快照匹配；MCP 配置仅通过命令行 `-c` 注入。
- 每个最终场景跟踪 4 个已知进程，`residualProcessCount=0`，`threadsComplete=true`；临时目录已删除。
- 在通知省略 `jsonrpc` 的真实协议兼容修复前，诊断 parent 的 thread 删除确认曾失败；未创建 child，且没有进程、配置或 worktree 外临时文件残留。执行 session 未读取私有 session 存储，也未通过“最近 thread”猜测身份。
- 当前 CLI allowlist 事件不足以无正文地区分 native child-final/mailbox 信号；这是 Gate 3 的独立证据缺口。
- `--strict-config` 与现有只读用户配置不兼容，最终 live 命令未启用 strict 模式；固定 `tool_timeout_sec` 由实际 fresh MCP call 证明被接受，但没有运行时回读值。
- 仓库没有 AIO 的 `.trellis/scripts/task.py` 或 `scripts/check-local-verification.mjs`，因此无法执行对应 Skill 的 status/doctor/deliver/local runner；按用户交接，AIO 临时审查的固定本地校验为 `local_ready`。本仓库实际验证命令和结果如上。
- GitHub 当前未配置 required checks，记录为 `required_checks_not_configured_bootstrap`，不得表述为 CI 成功。

停止点：PR ready 且固定 head 交付。不得合并、启用 auto route、安装生产 watcher、创建后续任务或开始里程碑 0。
