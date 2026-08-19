# GKD-M2-A F-004 v4 Live Probe 交付

## 结果

- Outcome: `blocked`
- F-005: 保持已整改，本轮未修改 activation/claim/recovery
- F-004: 唯一正常环境 live probe 未产生 `gkd_executor` activation 或 child terminal
- Error: `CUSTOM_ROLE_ACTIVATION_MISSING`
- Fixed base: `839974fbcd9114e5a5ad3b8fa1d4c58e68cb90ea`
- Synchronized main: `302fab499f86ebbc1fe23602ba28670b27132692`
- Live authorization head: `26b8e9c185a0bdf365266efdb45f42260c8922b3`
- Implementation/evidence commit: `58155234713e146b321267b1c56468bc1951d561`
- PR: [KNaiFen/gkd#6](https://github.com/KNaiFen/gkd/pull/6)，保持 Draft

本交付不宣称 `role_routing_core_ready`，不启用 automatic route，不进入 M2-B，不验收或合并。v4 live 授权已消耗，禁止再次调用。

## 冻结命令

live parent 使用正常用户 `CODEX_HOME`、provider、auth 和 model routing；项目级 `.codex/agents/gkd_executor.toml` 固定 child 为 `gpt-5.6-sol` / `xhigh` / `workspace-write`。执行命令为：

```text
codex exec --ephemeral --json \
  --cd "$GKD_PROBE_REPO" \
  --sandbox workspace-write \
  -c 'approval_policy="never"' \
  -c 'agents.enabled=true' \
  -c "$GKD_PROJECT_TRUST" \
  '<固定握手 Prompt>'
```

命令不包含 `--strict-config`、`--ignore-user-config`、parent `--model`、parent effort override、`--ask-for-approval`、alternate `CODEX_HOME`、角色替换或 fallback。

## 启动门

- Authorization head/local/upstream/remote/PR: 全部 `26b8e9c185a0bdf365266efdb45f42260c8922b3`
- Worktree/probe repo: clean
- Login: 正常 ChatGPT 登录态，只读取 `codex login status`
- Codex version/digest: `codex-cli 0.147.0` / `19c4f144c5226a9f17c58e6f0fa854843b0f77a6eb420f40e2745a12f10f5d37`
- Generated project/role TOML strict parse: `true` / `true`
- Project trust / agents enabled / role definition accepted: `true` / `true` / `true`
- Non-strict no-transport / live command parse: `true` / `true`
- Before live model invocations / attempts: `0` / `0`
- Production/AIO protection digest: matched recorded values

新的临时 Git repo 由 `handshake_preflight.py` 生成，preflight 绑定 exact bundle/role/config/project/Skill digest。no-transport 只作为静态启动边界，不作为 activation。

## Host Evidence

- Codex exit code: `0`
- Attempts/model invocations: `1` / `1`
- Parent turn entered/terminal: `true` / `true`
- Activated roles: `[]`
- Unexpected roles: `[]`
- Downgrade/fallback observed: `false` / `false`
- Child terminal: `false`
- Host error: `null`
- Observed collaboration tool: `wait`，receiver thread 与 agent state 均为空

结构化事件序列为 `thread.started`、`turn.started`、`item.started:collab_tool_call:wait`、`item.completed:collab_tool_call:wait`、`item.completed:agent_message`、`turn.completed`。证据只使用事件类型、tool/status、hashed parent identity 和 terminal 事件；没有读取或使用 Agent 消息正文、固定 terminal marker、自述、fixture 或候选输出。由于没有 spawn、child identity 或 custom-role activation，parent terminal 不能补足缺失的 child 事实。

第一次 live 包装器准备因二进制路径解析错误，在操作系统创建进程前以 `PermissionError` 结束；两个输出文件均为零字节，没有 Codex 子进程、模型调用、live-call 元数据或已消耗 attempt。清理空文件并改用 preflight 同一 `discover_codex()` 后，只执行了一次真实 `codex exec`。没有第二次 Codex 调用、重试、降级或 fallback。

原始 JSONL、stderr、临时 repo、调用元数据和临时输出均已删除。生产配置、AIO 和临时 repo 在真实调用前后未漂移。

## Digests

- Bundle version: `0.0.0-dev.0`
- Bundle content: `c6cb148b8ff57838fea23100968d241e003307e5284b49f67a95582e3728c4f6`
- M2 evidence: `c905be8cb97e54e7e5eca0e23ad5e383e1f414bae386c412b1e004e5bc32df25`
- Evidence file SHA-256: `10e196a0b542b0c341d84109105f2c84a980b4112ab44e992cbd2f6ab9638a86`
- Preflight: `01c910ce24e9a62c90a361fdcf98df2259cbd8e5dfe4fe1836855ef59def10ea`
- Handshake: `fbacd3ff2dcf8b6068e2505450520ffaae0c04f47a0f730868cc48d3a171434c`
- Handshake file SHA-256: `2ab481dbad40480331c87416ebeb0c9cf13b5908105f0507810eebad96953923`
- Executor role/config/project config: `7eeca24f18113f1c58d8cf7a712d431e790f721d5dba8cd0706cdfefe1033d16` / `10c0675808974609242280367f2e7aea07e61dd839a1ec2e244d53a9b6c74e3e` / `9a9bc7db827ea68cf4ba6761902e91ce4982fbaec25b8d68b70c4c790cef35d0`
- Executor context: `89ed5ac0e9e641cabeebfbfb790912f6058adcc6b55f86a43a1c36db835b36dc`
- Executor Skills: `gkd-ci-monitor` `45589e31a888437774b67c9c20be2ab4075c48bbb9de918f8ad7c068c82dc7a0`; `gkd-execute` `d7d61e528d5d32f67ea69152193ecaaef7a2aaa6ac4ff12972c866f312806524`; `gkd-local-verify` `3ec80b83782c7e1ff69d7fb72e6fb1665c6a5add66d97c19dd235908c33d6ad3`

v3 strict compatibility failure和更早的隔离模式 HTTP 400 均继续保留在 handshake 的历史证据字段中，不用于补足本轮 host facts。

## 验证

| Contract | Result |
| --- | ---: |
| M2-A role/routing | 65/65 |
| M1 task-core | 104/104 |
| Foundation | 53/53 |
| Watcher core | 47/47 |
| Watcher live-negative | 15/15 |

最终实现上两个独立系统临时根生成的 M2 evidence 逐字节一致；既有回归 219/219 通过。两次安装 inventory 均为 49 文件。生产保护面保持 2289 entries / `db47d57e24c9a23f185ecafad1ac0d9bb8c7b4fa5c930b1b3a6abfb2776dcd6d`，AIO 保护面保持 8 entries / `21c4d0c64f9ceacfc0e18a38084422982bb6f2134ce57b316e5f2cb9d1f26b58`。未运行历史 watcher live probe、真实一小时等待、大型构建或依赖安装。

## 停止边界

PR #6 保持 OPEN/Draft。仓库无 configured checks，事实为 `required_checks_not_configured_bootstrap`，不构成 CI 成功。F-004 尚缺可信 `gkd_executor` activation 与 child terminal；本轮授权不可重用，需由独立 main/acceptance 决定后续计划。M2-A 保持 manual-only，禁止 acceptance/merge、M2-B、automatic route、生产安装、AIO 修改和后续里程碑。
