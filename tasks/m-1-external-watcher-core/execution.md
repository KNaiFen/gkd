# GKD-M-1B：外部 app-server watcher core

## 任务身份

- 状态：`awaiting_manual_execution`
- 执行路线：人工开启的顶层执行 session
- 推荐执行模型：GPT-5.6 Sol，`xhigh`
- 仓库：`KNaiFen/gkd`
- 分支：`task/m-1-external-watcher-core`
- Draft PR：`https://github.com/KNaiFen/gkd/pull/2`
- 固定 base SHA：`9aec60a40572b7c0705049dbce3199d004049c81`
- 本机 worktree：`/Users/knaifen/Documents/Codex/gkd-worktrees/m-1-external-watcher-core`
- 冻结计划：`GKD 本体实施计划 v1`
- 计划 SHA-256：`af094a027b8e95cb4010118535031e94db8edc2631e91024676d3eaaff8edc30`
- 前置证据：`GKD-M-1A` / PR #1 / merge `0cc09e9c794f73876c84dd63effe87fde355add8`
- 覆盖范围：实现版本绑定的 watcher core、app-server client、长阻塞 MCP adapter 与 fake app-server 合同测试；不宣称 live D2 已通过

## 授权与边界

用户已明确授予 `gkd_core_implementation`，并批准原生不足时使用外部 app-server watcher。本任务允许：

1. 修改当前 GKD task worktree 中 watcher core、MCP adapter、测试、fixture、证据和任务记录。
2. 只读运行 `codex --version`、生成 app-server schema，并用命令行 `-c` 临时覆盖验证配置解析。
3. 使用 Python 标准库、临时目录、fake app-server subprocess 和注入式 fake clock 完成秒级/分钟级测试。
4. 提交并推送任务分支，创建或更新任务 PR，读取该 PR 的现有 GitHub 状态。

本任务禁止：

1. 修改生产 `~/.codex`、安装生产 MCP server、启动真实执行子代理或修改当前 session 的工具配置。
2. 修改 AIO Coding Hub、`KNaiFen/gkd-sandbox`、其他仓库、GitHub设置、Secrets或runner。
3. 调用付费 Responses API，读取私有 session 数据库/rollout JSONL，抓取或保存 Agent 对话正文。
4. 调用 `thread/read(includeTurns=true)`；若无法在不获取正文的条件下取得必要事实，必须 fail-closed 并留给 M-1C 解决。
5. 让子代理承担调查、设计、编码、测试或判断；本任务不需要任何子代理。
6. 声称 `external_watcher_supported`、启用 auto route、开始里程碑0、合并PR或创建tag/Release。
7. 安装依赖、运行构建、产生大型cache/build目录，或接受来自模型请求的任意shell命令/自然语言steer内容。

发现必须扩大范围或改变用户可见合同，停止并在 `delivery.md` 记录 blocker。

## 已固定事实

1. `codex-cli 0.147.0` 的原生 `wait_agent` 最大为3,600,000ms，不能拼接成D2；`GKD-M-1A` 结论为 `native_insufficient`。
2. M-1A relevant app-server schema digest 为 `ea75b7760483b70be4535b2d966e1ccd92035f6c71362a79f2cb2d54d0088bcf`，暴露 `thread/list`、`thread/read`、`thread/status/changed`、`turn/completed`、`turn/interrupt`、`turn/steer`。
3. `turn/steer` 要求 `threadId`、`expectedTurnId`、`input`；`turn/interrupt` 要求 `threadId`、`turnId`。
4. 本机临时配置解析已接受 MCP `tool_timeout_sec = 43200`。这只证明配置表面，不证明真实连接能保持12小时。
5. OpenAI公开文档没有给出上述app-server内部schema或长时MCP保证；实现必须绑定本机生成schema并对未知版本fail-closed。

## 目标结果

本任务只能输出：

- `core_ready_for_live_gate`：core和adapter通过全部hermetic合同测试，可进入独立M-1C fresh-session验证；
- `blocked`：协议或运行时事实不足，无法在批准边界内构造安全adapter。

不得输出 `external_watcher_supported`。真实Codex/MCP接线、正常child final、异常steer和父上下文trace属于下一任务。

## 固定架构合同

### 单一阻塞工具

1. 暴露一个窄MCP tool，例如 `gkd_watch_agent`。一次 `tools/call` 最长等待43,200,000ms，内部每3,600,000ms执行健康检查；测试可注入更短值和fake clock。
2. 健康检查期间不返回tool result、不发送progress notification、不写stdout/stderr日志，也不生成可进入parent上下文的中间帧。
3. 只有child正常终态、批准的异常、12小时deadline、取消、协议错误或编排器错误才产生一次最终响应/错误。
4. 正常终态不得调用 `turn/steer`；由watcher观察 `turn/completed`/终态后结束单一MCP call。M-1C负责验证与native mailbox的去重。

### 请求与结果

请求必须是版本化、严格校验的结构化对象，至少绑定：

- `schemaVersion`
- `taskId`、`offerId`、`sessionId`
- `childThreadId`、`childTurnId`
- `parentThreadId`、`expectedParentTurnId`
- `runtimeEvidenceDigest`
- `maxWaitMs`、`healthIntervalMs`

未知字段、空ID、超长值、错误类型、`maxWaitMs > 43_200_000`、`healthIntervalMs <= 0`、父子ID相同或缺少digest必须在启动app-server前拒绝。运行时command、路径、steer文本不得由tool请求提供。

结果只允许固定枚举及非敏感摘要，例如：`normal_terminal`、`abnormal_child`、`deadline`、`cancelled`、`parent_steer_rejected`、`protocol_error`、`orchestrator_error`。结果绑定原请求身份与runtime evidence digest，不包含对话正文、raw payload、完整schema或本机绝对路径。

### app-server 边界

1. 使用无 `shell=True` 的固定argv启动/连接 `codex app-server`；命令来源由受信安装配置提供，不接受模型输入。
2. 实现有界JSON-RPC请求ID、单writer、响应关联、notification处理、EOF/超时/畸形JSON/未知ID/重复响应检测和确定性关闭。
3. 启动时核对Codex版本与relevant schema digest；不一致返回 `protocol_error`，不得猜字段或继续控制thread。
4. 健康检查只读取不含turn正文的thread/status事实。禁止 `includeTurns=true`；不可证明stalled时，active child保持healthy，不能仅凭 `updatedAt` 一小时不变interrupt。
5. `systemError`、`notFound`、明确errored/interrupted及连接/协议失败按固定分类处理。未知状态fail-closed为错误，不静默当健康。

### 异常控制

1. 只有请求中已绑定的child thread/turn可被interrupt；不得interrupt parent。
2. 需要异常唤醒时，先对仍处于错误active状态的child执行 `turn/interrupt`，观察确认后再对绑定parent调用 `turn/steer`。
3. steer input由固定 `gkd_watchdog_event` schema和枚举原因生成；不得包含请求提供的任意自然语言。必须携带task/offer/session/runtime digest，不包含正文。
4. `expectedParentTurnId` 不匹配时禁止重试、查询其他turn或调用 `turn/start`；返回 `parent_steer_rejected`。
5. MCP tool无论steer成功与否都必须终止自身调用；连接/进程崩溃必须转为terminal工具错误，不能永久静默。

## 实现要求

1. 使用 `src/gkd_watchdog/**`（或同等单一package）、窄入口脚本及 `tests/watchdog/**`；不建立尚未批准的完整bundle/installer。
2. 仅使用Python标准库；I/O、clock、sleeper、transport和command resolver必须可注入。生产路径禁止随机sleep和真实小时等待。
3. MCP stdout只能输出协议帧；日志默认关闭，错误日志必须脱敏且只到stderr。健康tick在stdout/stderr均为零输出。
4. canonical JSON、digest、ID校验、状态转换和最终结果由代码生成；测试或Agent不得手填机器状态作为通过证据。
5. fake app-server必须是实际subprocess/stdio JSON-RPC fixture，不只是mock函数返回；状态机单元测试可使用内存transport。
6. 保存的transcript只包含方法名、请求ID、枚举状态、字段存在性和digest；不得保存raw arguments、thread/turn正文或凭据。
7. 代码注释只解释非显然的不变量，例如单writer、CAS拒绝和为何active stale不能视为stalled。

## 必测合同

至少覆盖：

1. 12小时deadline使用fake clock只发一次终态；每小时tick不会产生MCP progress/result/log。
2. 正常terminal立即结束且不steer。
3. active child跨多个小时tick仍健康，包括 `updatedAt` 不变化；无明确stalled信号不interrupt。
4. explicit systemError/notFound/errored触发固定异常分类；错误active child按child interrupt -> parent expected-turn steer顺序。
5. 错误expected turn被拒绝且无重试、无其他parent、无 `turn/start`。
6. app-server EOF、启动失败、畸形JSON、未知响应ID、重复响应、schema digest漂移均在有界时间终止。
7. 请求未知字段、注入shell参数、任意steer文本、父子ID相同、超限deadline和缺失digest在副作用前拒绝。
8. 取消只影响本watch和绑定child策略，不interrupt parent。
9. 两个并发watch实例保持各自请求ID/身份，不交叉投递；单实例只有一个writer。
10. MCP initialize、tools/list、tools/call、成功响应和JSON-RPC error framing通过subprocess集成测试。
11. `tool_timeout_sec = 43200` 临时配置解析成功被记录为声明证据，不被标为live通过。
12. 敏感数据fixture证明token/cookie/Authorization/私钥样式和本机路径不会进入结果、transcript或错误。

关键门需要negative/mutation测试，确保去掉expected-turn、schema digest、零健康输出或deadline单发保护时测试会失败。

## 允许的主要文件

- `src/gkd_watchdog/**`
- `scripts/gkd-watchdog-mcp` 或等价窄入口
- `tests/watchdog/**`
- `evidence/m-1-external-watcher-core/**`
- `tasks/m-1-external-watcher-core/**`
- 最小 `.gitignore` 和 `.agents/**` 状态更新

若需要修改M-1A证据、未来bundle/installer或其他产品面，停止并报告。

## 验证与交付

1. `git diff --check`。
2. 所有unit/property/subprocess合同测试在秒级或短分钟内完成，不安装依赖、不产生bytecode/build/cache。
3. 重复测试/证据生成除允许时间戳外确定一致。
4. 敏感数据扫描只报告规则和文件，不回显值。
5. PR没有required checks时记录 `required_checks_not_configured_bootstrap`，不得声称CI成功。
6. 填写 `delivery.md`：outcome、implementation/evidence head、PR、文件、命令、合同矩阵、协议/version digest、残余风险和M-1C建议。
7. 使用简短中文提交说明提交、推送并将PR解除Draft；不得合并或开始M-1C。
