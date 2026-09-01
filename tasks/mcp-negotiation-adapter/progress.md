# 进度

## 2026-09-02

- 已创建独立工作树，基于主分支 `6ccbca3`。
- 已检查 `src/gkd_watchdog/mcp_server.py`、`probes/app-server-watcher/mcp_adapter.py` 及其测试/夹具。
- MCP initialize 现在只在显式登记的 `2025-06-18` 或 `2024-11-05` 上返回结果；缺失、未知（包括 `mcp_2026_07_28`）版本统一返回稳定 `-32602` / `unsupported protocol version`，并列出静态支持版本，不回显请求值或静默降级。
- live adapter 复用同一版本协商；correlation metadata 只接受现有历史 watcher 合同中的 `threadId`、`x-codex-turn-metadata` 及五个已用嵌套字段，额外字段返回 `mcp_*_fields_unsupported`。
- 新增已知版本、未知/缺失版本、metadata 字段漂移和 live adapter 协商测试，并纳入 watcher contract catalog。
- 新增脱敏兼容证据 `evidence.json`（SHA-256 `9bb2c0552cb755bc097dd3c2fde0355de15c5762e2810dd48e6e9927785494c9`），只记录版本/字段名和稳定错误结果。

## 验证

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. python3 -m unittest tests.watchdog.test_mcp tests.watchdog.live.live_test_probe`：26 项通过。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. python3 -m unittest discover -s tests/watchdog -p 'test_*.py' -t .`：55 项通过。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:canonical/payload/lib:. python3 scripts/gkd-verify --base-sha 6ccbca3078aa13038122f4c05db058d292c0842e --scope-internal watcher-core-and-live-negative --head-sha 6ccbca3078aa13038122f4c05db058d292c0842e --result-output /tmp/gkd-mcp-watcher-results.json`：55 项通过。
- `PYTHONPATH=canonical/payload/lib python3 canonical/payload/bin/gkd-bundle generate --source-root canonical`：生成既有 `0.0.0-dev.1`，content digest `9a683001eb877e944c5def8dde91aa20f2a965bd9e74bf2d9609a37d3163cf2c`，115 文件。
- `git diff --check`、`python3 -m compileall -q src/gkd_watchdog probes/app-server-watcher tests/watchdog tests/contract_catalog.py`：通过。
- 主代理已审查并合并该阶段净变更，待主工作树复核后提交。
