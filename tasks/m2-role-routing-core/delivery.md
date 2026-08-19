# GKD-M2-A F-004 v4 静态整改交付

## 结果

- Outcome: `blocked`
- F-005: 保持已整改，本轮未修改 activation/claim/recovery
- F-004: v4 正常环境静态 preflight 已通过；等待对本交付 fixed head 的一次独立 live probe 授权
- Fixed base: `839974fbcd9114e5a5ad3b8fa1d4c58e68cb90ea`
- Synchronized main: `302fab499f86ebbc1fe23602ba28670b27132692`
- Implementation/evidence commit: `0d670351c2412c98a84756047020499c4fc522f9`
- PR: [KNaiFen/gkd#6](https://github.com/KNaiFen/gkd/pull/6)，保持 Draft

本交付不宣称 `role_routing_core_ready`，未请求或执行新的 live probe，不启用 automatic route，不进入 M2-B，不验收或合并。

## v4 冻结命令

live parent 继续使用正常用户 provider、auth 和 model routing；项目级 `.codex/agents/gkd_executor.toml` 固定 child 为 `gpt-5.6-sol` / `xhigh` / `workspace-write`。冻结命令为：

```text
codex exec --ephemeral --json \
  --cd "$GKD_PROBE_REPO" \
  --sandbox workspace-write \
  -c 'approval_policy="never"' \
  -c 'agents.enabled=true' \
  -c "$GKD_PROJECT_TRUST" \
  '<固定握手 Prompt>'
```

命令不包含 `--strict-config`、`--ignore-user-config`、parent `--model`、parent effort override、`--ask-for-approval`、alternate `CODEX_HOME`、角色替换或 fallback。精确参数向量以 `--help` 解析通过，未调用模型。

## 静态预检

- Codex resolution/version: `command-v` / `codex-cli 0.147.0`
- Codex executable digest: `19c4f144c5226a9f17c58e6f0fa854843b0f77a6eb420f40e2745a12f10f5d37`
- Generated project config parsed: `true`
- Generated role config parsed: `true`
- Project trust / agents enabled: `true` / `true`
- Project role definition accepted: `true`
- Normal environment reached no-transport: `true`
- Custom-role activation proven: `false`
- Live command parsed: `true`
- Model invocations / live attempts consumed: `0` / `0`
- Production configuration unchanged: `true`
- Probe repo clean/unchanged: `true` / `true`

生成的 project config 与 `gkd_executor.toml` 由 Python `tomllib` 严格解析，并与 canonical source 精确比较。正常环境用非 strict `codex app-server --listen off` 加显式 project trust 和 `agents.enabled=true` 到达唯一接受的 no-transport 边界；trust disabled、malformed role/project config 与其他 fatal startup 均 fail-closed。no-transport 只证明静态启动到达边界，不作为真实 custom-role activation 或 terminal 证据。

v3 strict 失败保留为 `historicalCompatibilityEvidence`：`codex-cli 0.147.0 --strict-config` 因正常用户字段 `disable_response_storage` 在 project discovery 前返回 `USER_CONFIG_PARSE_FAILED`，对应旧 preflight digest `b66d0f9b5fd215441c9875e45a9a5799c8b65a4490896b648eec8e98149734b7`，模型调用和已消耗 live attempt 均为 0。此前隔离模式 HTTP 400 `HOST_MODEL_UNSUPPORTED_FOR_CHATGPT_ACCOUNT` 继续保留为 `historicalNegativeEvidence`，handshake digest 为 `78f213622874a4e09836a9f9d395647146f17019339841ac52cbdb267483623c`。

## Digests

- Bundle version: `0.0.0-dev.0`
- Bundle content: `c6cb148b8ff57838fea23100968d241e003307e5284b49f67a95582e3728c4f6`
- M2 evidence: `94b75a697855f436daf9ef5e0e514b4b6bce1fad0ccf627fb077f87d8da69d1e`
- Evidence file SHA-256: `180075b79dbaa087228d2aba279f0d3635779dc6bbc8ca6db4e0727847a758dc`
- Preflight: `9352fee0803e2975c1880f31f35069e39f43962d7cfcb81fbf83b8747fc08246`
- Handshake: `9e4781d2b6053c7075f6add038243c02a9062e15e0720a7f485ef17291e8a18a`
- Handshake file SHA-256: `75fb6fa7c58633b994c565495518dad9754f39bd9fd5f3c12d9dff3b0f928e1d`
- Executor role/config/project config: `7eeca24f18113f1c58d8cf7a712d431e790f721d5dba8cd0706cdfefe1033d16` / `10c0675808974609242280367f2e7aea07e61dd839a1ec2e244d53a9b6c74e3e` / `9a9bc7db827ea68cf4ba6761902e91ce4982fbaec25b8d68b70c4c790cef35d0`
- Executor context: `89ed5ac0e9e641cabeebfbfb790912f6058adcc6b55f86a43a1c36db835b36dc`
- Executor Skills: `gkd-ci-monitor` `45589e31a888437774b67c9c20be2ab4075c48bbb9de918f8ad7c068c82dc7a0`; `gkd-execute` `d7d61e528d5d32f67ea69152193ecaaef7a2aaa6ac4ff12972c866f312806524`; `gkd-local-verify` `3ec80b83782c7e1ff69d7fb72e6fb1665c6a5add66d97c19dd235908c33d6ad3`
- Full role/Skill/context digest inventory remains in `contract-results.json`; canonical bundle bytes and manifest did not change.

## 验证

| Contract | Result |
| --- | ---: |
| M2-A role/routing | 64/64 |
| M1 task-core | 104/104 |
| Foundation | 53/53 |
| Watcher core | 47/47 |
| Watcher live-negative | 15/15 |

两个独立系统临时根生成的 M2 evidence 逐字节一致；既有回归 219/219 通过。两次安装 inventory 均为 49 文件。生产保护面保持 2289 entries / `db47d57e24c9a23f185ecafad1ac0d9bb8c7b4fa5c930b1b3a6abfb2776dcd6d`，AIO 保护面保持 8 entries / `21c4d0c64f9ceacfc0e18a38084422982bb6f2134ce57b316e5f2cb9d1f26b58`。临时 repo、fixture、测试输出和 Python cache 均已清理；未运行模型 turn、历史 watcher live probe、真实一小时等待、大型构建或依赖安装。

## 停止边界

PR #6 保持 OPEN/Draft。仓库无 configured checks，事实为 `required_checks_not_configured_bootstrap`，不构成 CI 成功。当前唯一开放条件是用户对新的完整 fixed head 单独授权一次正常登录态 live probe；只有 host evidence 证明 parent turn、唯一 `gkd_executor` activation、无替换/降级/fallback、child terminal 与 parent terminal，F-004 才可升级。M2-A 保持 manual-only，并停在新的静态 fixed-head 交付。
