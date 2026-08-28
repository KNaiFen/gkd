# GKD-O4 交付

## 结果

- Outcome: `watcher_historical_lane_ready`
- Fixed base: `9009b089fb811eceaf91ada8b60397b39a451f97`\n- Claim base head: `41d5d6afe8cd8299bd7de0350759a62ec4348535`\n- Claim: `526b76d13fe5d0ad1e70586f1130bfe39ef86225912df54223379d7dc8d8e9eb`\n- Implementation head: `ff4992757344d9a87f864ad09c4c679c02a53d0a`

默认 `scripts/gkd-verify --base-sha <full-sha>` 现在只运行 10 个核心 scope，不导入或启动
watcher/probe；`--historical` 是显式的 watcher/probe 历史入口，只运行原有
`watcher-core-and-live-negative` scope。canonical result consumer 严格区分默认与历史 manifest，
并保留原 watcher core、native probe、M-1B/M-1C 事实和 fail-closed 行为。宿主能力不满足冻结的
Codex/protocol 声明时，historical runner 返回固定 `HOST_CAPABILITY_UNAVAILABLE`，不改写为通过。

## 证据

- Execution bundle digest: `06095243b2199672243b559e0af2798fb9e051e33281775b98bc68c8b16ac48a`
- Candidate output bundle digest: `911a6cf373adfa5dafce5570c05d1c6fad70f34bcc590a7b39f3a230ab132c97`
- Default verifier: 386 tests, 10 scopes, result manifest `83c2e2ca3d0ef3853481789054b32c2d60f078ce1eaf28f45a0d94531c5bd477`\n- Historical verifier: 47 tests, 1 scope, result manifest `6d6e0515effb51c3c2f02aeace13e348f5cf2b00525b3a910f0a319ae04bf1d9`\n- Historical watcher result digest (two byte-identical runs): `2cb11743c79f86d35329f0f5a4fb4b76a038a1383cc7cdbdb3d812845ae0765b`
- Stable host-capability diagnostic digest (two runs): `b0739841da2d3b5618512b7d31921038f3266128284d2f6cb80c46d376edc2fb`

默认与 historical verifier 均在 Python 3.14 下通过；watcher 47 项、manifest/packaging 定向回归
35 项通过。两次 historical canonical manifest 与 scope result 逐字节一致。真实宿主 Codex 为
`0.150.1` 且协议 digest 不匹配冻结 M-1B 声明，因此历史 host probe 两次均返回上述稳定诊断，
未写入 evidence 文件或伪造 live 成功。

## 范围与清理

仅修改 verifier scope 分层、结果 schema/consumer、watcher runner 的宿主诊断映射、README 和生成的
manifest lock。watcher 协议、MCP/app-server 控制逻辑、native probe、历史 fixtures/evidence、
生产/AIO/GitHub settings/Secrets/runner/tag/Release 均未修改。临时验证目录位于系统临时边界内，
未写入仓库或生产配置；工作树在 delivery 文档提交前保持干净（仅本文件待提交）。

## 停止边界

本文件单独提交后，executor 只调用 `gkd-task deliver` 绑定本文件、实现提交和 candidate output
bundle digest，然后停止；不验收、不合并、不归档、不清理 worktree 或分支，不启动其他任务。后续
review、固定头 CI、acceptance、merge、记录更新和清理只由 trusted main 处理。
