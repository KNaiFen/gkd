# GKD-M-1A：multiagentv2 原生 D2 能力探测

## 任务身份

- 状态：`awaiting_manual_execution`
- 执行路线：人工开启的顶层执行 session
- 推荐执行模型：GPT-5.6 Sol，`xhigh`
- 仓库：`KNaiFen/gkd`
- 分支：`task/m-1-native-d2-probe`
- 固定 base SHA：`b3ad757ca96980e4f7fff4c3096f5e1ca13f56e9`
- 本机 worktree：`/Users/knaifen/Documents/Codex/gkd-worktrees/m-1-native-d2-probe`
- 冻结计划：`GKD 本体实施计划 v1`
- 计划 SHA-256：`38f299619cd5adc4edb17259b6fc621d13209ed0678c8a5cfcd93e078ac0383b`
- 覆盖范围：里程碑 -1 中原生 multiagentv2 D2 能力门，不实现外部 watcher

## 授权与边界

用户已明确授予 `gkd_core_implementation`。本任务允许：

1. 修改当前 GKD task worktree 中的版本化探测脚本、测试、证据和本任务文档。
2. 只读检查本机 Codex 版本、model catalog、effective feature/config 和生成的 app-server 协议。
3. 使用临时目录、临时配置覆盖和一次性测试 thread/agent；测试 agent 必须显式指定 GPT-5.6 Sol、`xhigh`、`fork_turns="none"`，且只执行固定探测 fixture。
4. 向本任务分支提交并推送，创建或更新任务 PR，读取该 PR 的标准 GitHub Actions 结果。

本任务禁止：

1. 修改生产 `~/.codex` 中任何文件；12 小时等待上限由用户在启动 fresh session 前手动配置。
2. 修改 AIO Coding Hub、`KNaiFen/gkd-sandbox`、其他仓库或 GitHub 设置。
3. 实现外部 app-server watcher、GKD bundle、Skills、roles、installer 或后续里程碑功能。
4. 调用付费 Responses API，读取私有 session 数据库/rollout JSONL，抓取完整对话正文，或把认证信息写入仓库、日志和 artifact。
5. 让子代理承担调查、设计、编码、判断或交付。测试子线程只可执行预先写明的等待/终态/故障 fixture。
6. 合并 PR、创建 tag/Release、安装依赖、运行构建或产生大型 cache/build 产物。

若发现必须扩大范围、修改冻结计划或触碰禁止面，停止并在 `delivery.md` 记录 blocker，不自行扩张。

## 启动前置门

执行 session 开始后先验证：

1. 当前目录、branch、HEAD 和 `origin` 与任务身份完全一致。
2. worktree 除本任务已有交接提交外没有未知修改。
3. effective agent tool 的单次 `wait_agent` 上限至少为 `43,200,000 ms`。若工具 schema 仍限制为更短值，立即返回 `environment_blocked`；禁止用多次短等待替代。
4. effective model 为 GPT-5.6 Sol、reasoning effort 为 `xhigh`。无法证明时记录为环境阻塞，不降级到默认 worker。
5. 所有探测输出经过敏感数据检查；不得记录 token、cookie、Authorization header、完整用户路径配置或对话正文。

## 目标

用可复现证据回答：当前 Codex/multiagentv2 原生能力是否完整满足 GKD D2 合同。结论只能是：

- `native_supported`：下列所有合同均有正向和必要负向证据；
- `native_insufficient`：至少一项明确失败或原生能力缺失；
- `environment_blocked`：当前环境无法执行关键探测，不能把 unknown 写成 supported。

本任务不允许输出 `external_watcher_supported`，因为外部 watcher 尚未实现。

## 必测合同

1. `single_long_wait`：parent 对同一测试 child 只调用一次 `wait_agent(timeout_ms=43200000)`，child 终态能提前返回；不得短轮询。
2. `normal_final_wakeup`：child 正常 final 通过 multiagentv2 原生 mailbox/final-status 唤醒 parent，无外部 steer。
3. `hourly_internal_watchdog`：至少 65 分钟的健康 active child 期间，系统内部至少执行一次健康检查，且不要求 parent model 醒来。
4. `healthy_zero_parent_context`：上述健康检查不在 parent thread 中新增 model message、tool result、commentary、状态摘要或轮询记录。只用结构化 app-server thread/item 类型与计数证明，不读取私有 JSONL/数据库或保存正文。
5. `long_tool_is_healthy`：child 已登记的长工具调用不能仅因 `updatedAt` 一小时未变化被误判 stalled。
6. `abnormal_wakeup`：stalled、missing、systemError 或编排器故障至少有受支持的原生异常路径唤醒 parent，并给出可分类证据；缺任一类必须标记 fail/unknown。
7. `wrong_turn_rejected`：任何面向 active parent 的异常注入/恢复操作必须绑定 expected turn；错误 expectedTurn 被拒绝，不能投递到其他 turn。若原生系统没有等价能力，标记 fail。
8. `child_interrupt_parent_safe`：错误 active child 可被终止或隔离，但 parent 不被 interrupt，也不会被启动并发 turn。若原生系统没有等价能力，标记 fail。
9. `orchestrator_failure_wakeup`：编排器/连接/订阅失败会以 terminal 工具错误唤醒 parent，而不是永久静默。
10. `twelve_hour_deadline`：配置和协议能证明单次等待 deadline 为 12 小时；用参数化 fake clock/短时同路径测试证明 deadline 逻辑，不要求真实空等 12 小时。不得仅凭配置文本宣称通过。

`native_supported` 要求十项全部为 pass。原生能力缺少内部 watchdog、CAS 异常投递或故障唤醒中的任何一项时，应诚实返回 `native_insufficient`，后续由主会话创建外部 watcher 任务。

## 实施要求

1. 先读取完整 `AGENTS.md`、本文件和冻结计划；只按需读取 AIO 的 `GKD-001`、`GKD-003`、`GKD-006` 决定，AIO 全程只读。
2. 优先使用 Python 标准库或 shell 构建小型探测 harness，不安装依赖。所有时间参数可注入，自动测试使用 fake clock/短延迟，真实健康静默测试独立运行 65 分钟。
3. 原始结构化响应只保存完成判断所需的字段和摘要；对 item 类型/计数可生成 digest，禁止保存 conversation body。
4. 证据必须区分“配置声明”“协议表面”“真实行为”。仅发现 schema/event 名称不能证明 runtime 行为通过。
5. 每个合同在 `evidence/native-capability-matrix.md` 中记录 `pass|fail|unknown`、复现命令、证据路径、Codex版本和解释。证据文件不得包含本机凭据。
6. 真实 65 分钟测试启动后保持单次 parent wait；健康期间不发进度消息、不查询 child、不读取 thread。若用户主动询问状态，只报告测试仍在运行，不额外轮询。
7. 对探测 harness 添加可在秒级完成的自测试，覆盖deadline fake clock、字段裁剪/脱敏、错误分类和 supported 判定的 fail-closed 规则。
8. 不为了得到“支持”结论修改平台、注入未授权 hook 或把外部 watcher 行为算作原生能力。

## 允许的主要文件

- `probes/multiagentv2/**`
- `tests/probes/**`
- `evidence/m-1-native-d2/**`
- `evidence/native-capability-matrix.md`
- `tasks/m-1-native-d2-probe/execution.md`
- `tasks/m-1-native-d2-probe/delivery.md`
- 为忽略临时探测输出而进行的最小 `.gitignore` 修改

若需要修改其他产品文件，视为范围扩大并停止。

## 验证

至少完成并记录：

1. `git diff --check`。
2. 探测 harness 的秒级自测试，禁止生成 `__pycache__` 或大型临时产物。
3. 一次正常 child final 的单次长等待测试。
4. 一次至少 65 分钟的健康 long-tool 静默测试。
5. 所有可安全复现的异常、错误 expectedTurn、编排器失败和deadline短时同路径测试。
6. 仓库敏感数据扫描；只报告文件与规则，不回显命中值。
7. `native-capability-matrix.md` 十项均有状态，任何 unknown 都阻止 `native_supported`。

## 交付

执行 agent 完成后必须：

1. 填写 `delivery.md`，包含结论、完整 head SHA、PR编号/URL、文件清单、验证命令与结果、十项矩阵摘要、残余风险和下一步建议。
2. 使用简短中文提交说明提交所有任务变更，推送 `task/m-1-native-d2-probe`。
3. 创建或更新任务 PR，但不得合并。
4. 若 PR 尚无 required checks，明确记录 `required_checks_not_configured_bootstrap`，不得把它表述为 CI 成功。
5. 停止并把控制权交还主会话；不要自行开始外部 watcher 或里程碑 0。
