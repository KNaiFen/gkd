# GKD-O4 交付

## 结果

- Outcome: `watcher_historical_lane_ready`
- Fixed base: `fe5fae5ecd1500f65d5bad100dc66084f8d72472`
- Claim base head: `129f9d96fee52f9877649a4da849da888233c410`
- Claim: `67fb061d34bff29b9cd5738e1e65d56678e2d7d6995b6997535edfefc3e96fe2`
- Implementation head: `e8145f74ac23a71682c2592f3b178addc748e163`

默认 `scripts/gkd-verify --base-sha <full-sha>` 现在只运行 10 个核心 scope，不导入或启动
watcher/probe；`--historical` 是显式的 watcher/probe 历史入口，只运行原有
`watcher-core-and-live-negative` scope。canonical result consumer 严格区分默认与历史 manifest，
并保留原 watcher core、native probe、M-1B/M-1C 事实和 fail-closed 行为。宿主能力不满足冻结的
Codex/protocol 声明时，historical runner 返回固定 `HOST_CAPABILITY_UNAVAILABLE`，不改写为通过。

## 证据

- Execution bundle digest: `06095243b2199672243b559e0af2798fb9e051e33281775b98bc68c8b16ac48a`
- Candidate output bundle digest: `911a6cf373adfa5dafce5570c05d1c6fad70f34bcc590a7b39f3a230ab132c97`
- Default verifier: 386 tests, 10 scopes, result manifest `d78cca617aa689111b0ebd6039618be14d0aef3373186563fe7074ece6ff4f77`
- Historical verifier: 47 tests, 1 scope, result manifest `3c2fd7370fc0d6de736250c46402ecbe76a7147128a3fc27dbfaa90154584518`
- Historical watcher result digest (two byte-identical runs): `ebd72ba949f1c99d21f7e3e278fbbfa22a4102572229c7f0acc543d8ae6ccf18`
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
