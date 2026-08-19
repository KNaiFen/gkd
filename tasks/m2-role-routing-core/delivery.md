# GKD-M2-A F-004 v3 静态整改交付

## 结果

- Outcome: `blocked`
- F-005: 保持已整改，本轮未修改 activation/claim/recovery
- F-004: 生产使用环境握手合同与静态 preflight 已实现；正常用户配置 strict parse 失败，未启动 live probe
- Fixed base: `839974fbcd9114e5a5ad3b8fa1d4c58e68cb90ea`
- Synchronized main: `302fab499f86ebbc1fe23602ba28670b27132692`
- Implementation/evidence commit: `a88d271bff30f1611eedd27ffd1c91b04d9f1dcc`
- PR: [KNaiFen/gkd#6](https://github.com/KNaiFen/gkd/pull/6)，保持 Draft

本交付不宣称 `role_routing_core_ready`，不请求或执行新的 live probe，不启用 automatic route，不进入 M2-B，不验收或合并。

## v3 合同

live parent 改用正常用户 provider、auth 和 model routing；项目级 `.codex/agents/gkd_executor.toml` 继续固定 child 为 `gpt-5.6-sol` / `xhigh` / `workspace-write`。冻结命令为：

```text
codex exec --ephemeral --strict-config --json \
  --cd "$GKD_PROBE_REPO" \
  --sandbox workspace-write \
  -c 'approval_policy="never"' \
  -c 'agents.enabled=true' \
  -c "$GKD_PROJECT_TRUST" \
  '<固定握手 Prompt>'
```

命令不包含 `--ignore-user-config`、parent `--model`、parent effort override、`--ask-for-approval`、alternate `CODEX_HOME`、角色替换或 fallback。`--help` 参数解析通过，未调用模型。

确定性 preflight 负责 bundle/role/config/project/Skill digest、请求的 child 配置、project trust、role discovery、临时 repo 和生产配置非漂移。未来 host evidence 只负责 parent turn、按名启动唯一 `gkd_executor`、无其他角色/fallback、child terminal、parent terminal、exit code 和脱敏错误；不要求 JSONL 回显 GKD digest。

## 当前阻塞

- Codex resolution: `command-v`
- Codex executable digest: `19c4f144c5226a9f17c58e6f0fa854843b0f77a6eb420f40e2745a12f10f5d37`
- Static failure: `USER_CONFIG_PARSE_FAILED`
- Redacted error: `Codex rejected the normal user configuration: Error: <home>/.codex/config.toml:4:1: unknown configuration field disable_response_storage`
- Live command parsed: `true`
- User configuration parsed: `false`
- Project role discovered: `false`
- Model invocations: `0`
- Live attempts consumed: `0`
- Production configuration unchanged: `true`
- Probe repo clean/unchanged: `true` / `true`

失败发生在 project trust/custom-role discovery 之前。生产配置只由正常 Codex 启动和保护面 digest 检查读取，未打印、复制或修改；未读取认证材料或私有 session。没有通过删除 `--strict-config`、修改生产 `~/.codex` 或重新引入隔离配置绕过该事实。因此当前尚不具备针对新 fixed head 请求一次 live probe 的条件。

此前隔离模式 HTTP 400 `HOST_MODEL_UNSUPPORTED_FOR_CHATGPT_ACCOUNT` 保留为 `historicalNegativeEvidence`，其 handshake digest 为 `78f213622874a4e09836a9f9d395647146f17019339841ac52cbdb267483623c`；它不再代表 v3 正常 provider/routing 环境。

## Digests

- Bundle version: `0.0.0-dev.0`
- Bundle content: `c6cb148b8ff57838fea23100968d241e003307e5284b49f67a95582e3728c4f6`
- M2 evidence: `c03e0d9ac134de617f050d315d06c21f7fe1189f9bc1437db39aad7ffe1e3c43`
- Evidence file SHA-256: `a0864195aa8a0523f960aac96a3b44b3c4c7aaf9047a17ebab0adaf67ab1869f`
- Preflight: `b66d0f9b5fd215441c9875e45a9a5799c8b65a4490896b648eec8e98149734b7`
- Handshake: `63b748a7f67bbf63f5d6826c55459217252933881e47dcbfc168705eb8667a7e`
- Handshake file SHA-256: `dbc063257079c896d1af0df3654d0b74ee8f9dad08257d98667de23537f44a20`
- Executor role/config/project config: `7eeca24f18113f1c58d8cf7a712d431e790f721d5dba8cd0706cdfefe1033d16` / `10c0675808974609242280367f2e7aea07e61dd839a1ec2e244d53a9b6c74e3e` / `9a9bc7db827ea68cf4ba6761902e91ce4982fbaec25b8d68b70c4c790cef35d0`
- Executor context: `89ed5ac0e9e641cabeebfbfb790912f6058adcc6b55f86a43a1c36db835b36dc`
- Executor Skills: `gkd-ci-monitor` `45589e31a888437774b67c9c20be2ab4075c48bbb9de918f8ad7c068c82dc7a0`; `gkd-execute` `d7d61e528d5d32f67ea69152193ecaaef7a2aaa6ac4ff12972c866f312806524`; `gkd-local-verify` `3ec80b83782c7e1ff69d7fb72e6fb1665c6a5add66d97c19dd235908c33d6ad3`
- Full role/Skill/context digest inventory remains in `contract-results.json`; canonical bundle bytes and manifest did not change.

## 验证

| Contract | Result |
| --- | ---: |
| M2-A role/routing | 63/63 |
| M1 task-core | 104/104 |
| Foundation | 53/53 |
| Watcher core | 47/47 |
| Watcher live-negative | 15/15 |

两次独立 M2 evidence 逐字节一致；既有回归 219/219 通过。两次安装 inventory 均为 49 文件。生产保护面保持 2289 entries / `db47d57e24c9a23f185ecafad1ac0d9bb8c7b4fa5c930b1b3a6abfb2776dcd6d`，AIO 保护面保持 8 entries / `21c4d0c64f9ceacfc0e18a38084422982bb6f2134ce57b316e5f2cb9d1f26b58`。临时 repo、fixture、测试输出和 Python cache 均已清理；未运行模型 turn、历史 watcher live probe、真实一小时等待、大型构建或依赖安装。

## 停止边界

PR #6 保持 OPEN/Draft。仓库无 configured checks，事实为 `required_checks_not_configured_bootstrap`，不构成 CI 成功。当前唯一开放的 F-004 启动门是正常用户配置必须先通过当前 Codex 的 strict parser，并在同一 invocation 中证明 project trust 与 `gkd_executor` discovery；此前不得授权或运行 live probe。M2-A 保持 manual-only，并停在新的静态 fixed-head 交付。
