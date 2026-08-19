# GKD-M2-A 执行复盘

## 进度结论

里程碑 0、里程碑 1 和 M2-A 已完成。M2-A 固定 head
`b579926aaff50d40b462e7f21cf91c9709eeb3a3` 已由独立 main 验收并以
`9351d628d198ec8638311901cf288abadc643a42` 合并。当前唯一下一项是人工顶层
M2-B；route 仍为 `manual_only`，生产安装、AIO 接入、里程碑 3 和 automatic
route 均未开始。

## 子代理与角色实现的实际偏移

### 计划内行为

- M2-A 始终由人工顶层 GPT-5.6 Sol/xhigh session 实现，没有让未来的
  `gkd_executor` 自举本任务。
- `gkd_executor` 只用于用户授权的短时握手诊断；它不是 M2-A 的实现 worker，
  也没有接管验收、合并或清理。
- F-005 最终采用最小的 trusted-main 工作流权限边界。它连接可信 host facts、
  activation、exact claim 和 delivery，但不声称同一 OS 用户进程隔离，因此不
  引入签名、daemon、IPC 或密钥。

### 已收敛的历史试错

- 早期嵌套 `codex exec` 使用过 `--ignore-user-config`、parent model/effort
  override、strict-config 和 trust override。这些路径分别触发了 ChatGPT
  account 模型拒绝、用户配置未知字段和项目信任问题；最终交付已删除这些
  诊断参数，改用正常本机配置、受信项目和 rollout 事实归一化。
- 一度把 parent 的 wait-only stdout 或未 spawn 归类成角色能力失败；完整 session
  rollout 后确认实际 exact spawn、child activity 和双 terminal 存在。最终证据只
  接受事件绑定事实，不接受 Agent 自述、fixture 或候选输出。
- 首次 ready 交付曾缺少 activation → claim 的可消费正向链，独立验收发现后补上
  `TrustedMainActivationAuthority` 和对应负向合同，随后才允许合并。

### 不应继续的方向

- 不要复活 external watcher、generic worker fallback、短 wait 拼接、第二个
  executor 或嵌套执行链。
- 不要把工作流权限边界扩展成同用户安全产品，也不要为解决长上下文而新增
  profile、daemon、IPC、签名或全局上下文工程。

## 后续最小路线

1. 从本地已同步的 `main`（当前收尾 head `902001a...`，其功能合并父提交为
   `9351d628...`）新建独立人工 M2-B worktree；固定
   M2-A bundle digest `5b115a918d8a5241551b0be8dac657a448e1b912815493e1988007b1f4ed1880`。
2. 在 fresh runtime 只验证实际接受 `wait_agent(timeout_ms=3600000)`、child
   early-final、最多 12 个静默 interval、deadline 单一 timeout，以及固定 bundle
   digest 绑定。工具上限不足一小时就保持 blocked，不改成短循环。
3. M2-B 通过后才重新评估 automatic route；在此之前继续人工交接。M3/4/5 的
   专用 executor 只有在角色、offer/claim 和一小时等待门均有固定证据后才可启动。

## 长上下文治理

- 当前事实以 `acceptance.md`、`.agents/context.md`、`.agents/decisions.md`、
  `.agents/open-items.md` 和固定 Git head 为准；不以本次对话中的旧状态叙述为准。
- 每个里程碑合并后立即做一次 records-only 收尾：同步 main、写终态、清理候选
  worktree/分支，再创建下一任务。执行 session 只负责交付，不负责验收或收尾。
- 后续 session prompt 只携带固定 head、任务目标、停止条件和必要证据路径；历史
  blocked 轮次只链接，不复制进新的执行入口。
