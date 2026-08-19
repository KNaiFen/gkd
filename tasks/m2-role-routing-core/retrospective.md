# GKD-M2-A 执行复盘

## 进度结论

里程碑 0、里程碑 1、M2-A 和 M2-B 已完成。M2-A 固定 head
`b579926aaff50d40b462e7f21cf91c9709eeb3a3` 已由独立 main 验收并以
`9351d628d198ec8638311901cf288abadc643a42` 合并。用户随后明确确认 M2-B 的
一小时等待与 child early-final 已验证可用并免于重新取证。manual 仍为默认，
但里程碑 3、4、5 现在可以显式使用专用 `gkd_executor` automatic route；生产
安装和 AIO 接入仍未授权。

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

1. 从同步 main 规划里程碑 3 的首个任务，并按已有 hybrid B 授权显式请求
   automatic route；不再创建 M2-B worktree。
2. main 只能启动一个 `gkd_executor`，绑定 exact bundle、role/config、offer/claim、
   activation 和 M2-B gate；executor 不验收、不合并、不清理，也不派生替代 worker。
3. 每次健康等待只调用 `wait_agent(timeout_ms=3600000)`；超时后立即重等，最多
   12轮。终态、错误、用户介入或deadline结束循环，不使用短wait或外部watcher。

## 长上下文治理

- 当前事实以 `acceptance.md`、`.agents/context.md`、`.agents/decisions.md`、
  `.agents/open-items.md` 和固定 Git head 为准；不以本次对话中的旧状态叙述为准。
- 每个里程碑合并后立即做一次 records-only 收尾：同步 main、写终态、清理候选
  worktree/分支，再创建下一任务。执行 session 只负责交付，不负责验收或收尾。
- 后续 session prompt 只携带固定 head、任务目标、停止条件和必要证据路径；历史
  blocked 轮次只链接，不复制进新的执行入口。
