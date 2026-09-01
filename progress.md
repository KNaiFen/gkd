# Progress

## 当前状态

已完成第一阶段实现，等待主代理审查。

## 已完成

- 在 `src/gkd_watchdog/constants.py` 登记历史 `0.147.0` 与本机捕获的
  `0.152.0` runtime baseline；旧 `EXPECTED_*` 名称保留为历史兼容别名。
- `SubprocessRuntimeVerifier` 按 CLI 版本选择 baseline，并区分未知版本
  (`codex_version_unsupported`)、已登记版本 schema 漂移
  (`schema_digest_mismatch`) 和请求/实际 baseline 错配
  (`runtime_baseline_mismatch`)；错配在 app-server 启动前终止。
- `native_probe.py` 输出 `runtimeBaseline`，记录版本、schema digest 和脱敏
  feature summary；新增 `evidence/m-1-native-d2/compatibility-baselines.json`
  保存 0.147.0 历史事实与 0.152.0 当前捕获。
- 更新 watchdog 与 live probe 说明，明确 automatic watcher 仍是 legacy lane，
  manual-first 默认 bundle 不变。
- 新增 runtime compatibility 单测，并让历史 `run_contracts.py` 排除该新增单测，
  保持既有 47 项 M-1B evidence 数量和旧 baseline 语义。

## 验证

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. python3 -m unittest discover -s tests/watchdog -p 'test_*.py' -t .`：53 项通过。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. python3 -m unittest tests.watchdog.test_runtime_compat tests.watchdog.test_app_server tests.probes.test_native_probe`：25 项通过。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. python3 tests/watchdog/run_contracts.py --output /tmp/gkd-watchdog-current.json`：退出 0，当前 CLI 输出 `compatibility_baseline_recorded`，历史 scope 仍为 47 项。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. python3 probes/multiagentv2/native_probe.py --output /tmp/gkd-native-baseline-current-v2.json`：成功记录 `0.152.0` 与 digest `398b3be7ac8f5135c7ed6f258e3ba0264c734715b0384539adb462b873745519`。
- `git diff --check`：通过。
- `tests/probes` 的 unittest discover（带 `-t .`）未运行，因该目录当前不是可导入 package；对应 probe 测试已通过显式模块命令覆盖。

## 剩余风险

- `0.152.0` 仅登记为兼容性 capture；watcher 请求模型仍绑定历史 `0.147.0` digest，后续阶段需分别处理事件归一化、MCP、parser 和 initialize 能力，不能据此宣称 automatic watcher 支持。
- 本阶段没有修改 `turn/steer`、生产 `~/.codex`、AIO 或发布资产。

## 约束提醒

本阶段只处理 CLI/runtime/schema baseline。旧 automatic/historical 事实保持可追溯；`turn/steer` 必须留到最后阶段。
