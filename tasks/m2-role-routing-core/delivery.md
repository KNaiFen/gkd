# GKD-M2-A F-004 v5 交付

## 结果

- Outcome: `role_routing_core_ready`
- F-001/F-002/F-003/F-005: 已整改，本轮未修改其业务设计
- F-004: 已通过 trusted custom-role handshake
- Fixed base: `839974fbcd9114e5a5ad3b8fa1d4c58e68cb90ea`
- Implementation commit: `8f2ac63b4fcf5bc3c9741be362fd041e3ff5de38`
- Evidence commit: 本次最终 evidence/delivery commit（完整 SHA 在提交后回填）
- PR: [KNaiFen/gkd#6](https://github.com/KNaiFen/gkd/pull/6)，交付后标记 Ready

本交付只表示 M2-A role/routing core ready，route 仍为 `manual_only`。不宣称 M2-B 一小时等待、automatic route、生产安装、AIO 接入或里程碑 3；本 session 不验收、不合并、不清理 worktree/branch。

## Handshake

用户在 fresh probe Git 根通过正常 Codex trust UI 选择 `Yes, continue` 后退出提示。执行 session 未写入或回滚生产 `~/.codex`；该用户动作使调用前保护 digest 从历史 `db47d57e...` 变为 `f1b9cb277305039196067cb6621ecc2c50b09b0349824bc04ff684be775c1232`。

静态命令为：

```text
cd "$GKD_PROBE_REPO"
codex exec --json '<固定握手 Prompt>'
```

无 `--strict-config`、`--ignore-user-config`、parent model/effort/sandbox/approval/agents/trust 覆盖或 alternate `CODEX_HOME`；项目 `.codex/config.toml` 启用 agents，`.codex/agents/gkd_executor.toml` 固定 child 为 `gpt-5.6-sol` / `xhigh` / `workspace-write`。

确定性 preflight 证明 `tomllib` 解析、project role discovery、非 strict no-transport、role/config/bundle/project/Skill/AGENTS digest、CLI 参数解析、clean repo 和生产/AIO 非漂移。用户 trust UI 后的最新 parent rollout 记录证明：

- 唯一 `agents.spawn_agent`，`agent_type=gkd_executor`、`task_name=gkd_executor_handshake`、`fork_turns=none`；
- 唯一 child activity 绑定 hashed child thread，无 alternate role/downgrade/fallback；
- child `task_complete` marker 为 `GKD_EXECUTOR_CHILD_TERMINAL`；
- parent `task_complete` marker 为 `GKD_PARENT_TERMINAL`；
- Codex exit code `0`。

stdout 曾把 function-call 链压缩为 wait-only；经用户授权读取对应 test-session rollout 后确认其完整 function-call 记录。证据生成器只保留 path-free event types、hashed thread identities、exact role、terminal 和 exit facts，不保留 prompt/session 正文。宿主自动维护的原始 `~/.codex/sessions` 未删除，以遵守不得清理生产 Codex 状态的边界；其内容未复制到仓库 evidence。

## Digests

- Bundle version: `0.0.0-dev.0`
- Bundle content: `c6cb148b8ff57838fea23100968d241e003307e5284b49f67a95582e3728c4f6`
- M2 evidence digest: `47d78f5460f5dfdf81866296b95c9c58709b94dee4d19cd25790da01c28ce649`
- M2 evidence file SHA-256: `9810beb93dbc5f7275eb0a68b023e291d34703d4e68ffa0e55f4c32632027d29`
- Handshake digest: `101be87f86a78111b47152a0056006343786f60872bbaad8a0c1f5cdaa97387c`
- Handshake file SHA-256: `e6afb79ac18a57f8c533a50238f180b418fe9052040f02ff4907b47c66773542`
- Preflight digest: `7777c1ded263c51cdf22ee54d58660d2f763fe96d13e7f9558ac262ad162cfa0`
- Codex: `codex-cli 0.147.0`; executable SHA-256 `19c4f144c5226a9f17c58e6f0fa854843b0f77a6eb420f40e2745a12f10f5d37`
- Role/config/project config: `7eeca24f18113f1c58d8cf7a712d431e790f721d5dba8cd0706cdfefe1033d16` / `10c0675808974609242280367f2e7aea07e61dd839a1ec2e244d53a9b6c74e3e` / `9a9bc7db827ea68cf4ba6761902e91ce4982fbaec25b8d68b70c4c790cef35d0`
- Probe AGENTS instructions: `777519597b1a4ca62ee662bfdbe03760ffe64eed6cd6066b0d4b4585011a41da`
- Skills: `gkd-ci-monitor` `45589e31a888437774b67c9c20be2ab4075c48bbb9de918f8ad7c068c82dc7a0`; `gkd-execute` `d7d61e528d5d32f67ea69152193ecaaef7a2aaa6ac4ff12972c866f312806524`; `gkd-local-verify` `3ec80b83782c7e1ff69d7fb72e6fb1665c6a5add66d97c19dd235908c33d6ad3`
- Executor context: `89ed5ac0e9e641cabeebfbfb790912f6058adcc6b55f86a43a1c36db835b36dc`

历史 v3 `USER_CONFIG_PARSE_FAILED`、隔离模式 HTTP 400、v4 stdout orchestration miss 均保留在 handshake/finding 历史字段，不用于补足本次 host facts。

## 验证

| Contract | Result |
| --- | ---: |
| M2-A role/routing | 67/67 |
| M1 task-core | 104/104 |
| Foundation | 53/53 |
| Watcher core | 47/47 |
| Watcher live-negative | 15/15 |

M2 evidence 在两个独立系统临时根逐字节一致；每次临时根结束为空。两次安装 inventory 均为 49 文件。生产/AIO 保护面在本 session 调用期间未漂移，除用户主动 trust UI 造成的已记录生产 Codex digest 变化外，没有执行 session 写入。未安装依赖、未运行大型构建、未运行历史四场景 live probe、未等待真实一小时。

## PR 与停止边界

最终 push 后核对本地 HEAD、upstream、origin branch 和 PR #6 head 完全一致；PR 从 Draft 标记 Ready。PR 无 configured checks，事实仍为 `required_checks_not_configured_bootstrap`，不伪装为 CI 成功。

停止于独立验收前：不验收、不合并、不清理 worktree/branch、不启动 M2-B、不启用 automatic route、不修改生产 `~/.codex` 或 AIO，不进入后续里程碑。
