# GKD-M-1C：外部 app-server watcher live gate

## 给执行 session 的唯一入口

在新的顶层 Codex session 中打开本 worktree，然后只发送：

> 读取 `tasks/m-1-external-watcher-live-gate/execution.md`，严格按文档执行 GKD-M-1C。你是人工开启的顶层执行 session，不是 main，也不是默认 subagent；完成后停在 PR ready 和固定 head 交付，不得合并或开始后续里程碑。

执行 session 必须使用 GPT-5.6 Sol、`xhigh`。无法确认模型或 reasoning effort 时停止，不得降级。

## 任务身份

- 状态：`awaiting_manual_execution`
- 执行路线：人工开启的独立顶层 execution session
- 仓库：`KNaiFen/gkd`
- 分支：`task/m-1-external-watcher-live-gate`
- Draft PR：`https://github.com/KNaiFen/gkd/pull/3`
- 固定 base SHA：`c438855961760707c119cb172be97ae9030a4508`
- 本机 worktree：`/Users/knaifen/Documents/Codex/gkd-worktrees/m-1-external-watcher-live-gate`
- 前置候选：PR #2 head `98df6ba122d9fe8aed230094ed806010e7002aa7`
- 前置 merge：`1d303456f2afcaa4e5fd0353232e30c5c6b63a33`
- 前置结论：`core_ready_for_live_gate`，不是 `external_watcher_supported`
- 冻结计划：`GKD 本体实施计划 v1`

## 授权与硬边界

用户已授予 `gkd_core_implementation`，并批准原生 D2 不足时使用外部 app-server watcher。本任务允许：

1. 修改当前 task worktree 中最小 live probe/adapter、watcher 修复、合同测试、任务文档和脱敏证据。
2. 启动实际 `codex app-server`、临时 MCP server 和隔离的 fresh Codex canary session；只为 live gate 启动受控 canary child，不得把实现、审查或方案判断委派给 child。
3. 使用命令行 `-c`、临时目录和进程级环境覆盖，不写生产配置文件。Codex 正常创建自身 session/runtime 状态不视为安装，但禁止直接读取或编辑其私有存储。
4. 在固定任务分支提交、推送、更新 PR，并读取该 PR 的状态。

本任务禁止：

1. 修改或安装到生产 `~/.codex`，修改全局 `config.toml`、Skills、roles、plugins、MCP 配置或用户凭据。
2. 读取 session 数据库、rollout JSONL、对话正文、Cookie、Token、Authorization、私钥或其他敏感值；不得把原始 app-server/MCP payload 写入证据。
3. 修改 AIO Coding Hub、`KNaiFen/gkd-sandbox`、GitHub settings、Secrets、runner、付费 API 或 Responses API。
4. 用 fake app-server、纯 mock、手填 JSON、Agent 自述或 M-1B 的 hermetic 结果代替本任务要求的 live 事实。
5. 为追求通过而放宽固定 digest、thread/session/turn 绑定、expected-turn CAS、健康静默、数据最小化或 fail-closed 规则。
6. 合并 PR、启用 auto route、安装生产 watcher、开始里程碑 0，或把 `core_ready_for_live_gate` 改写成 live 成功。

若真实 Codex 接线要求材料性新架构、生产配置写入、私有状态读取或计划外权限，输出 `unsupported` 并交付证据，不得自行扩权。

## 目标结果

本任务只能输出二选一终态：

- `external_watcher_supported`：本文件全部 required live gate 由实际 Codex/app-server/MCP 证据证明。
- `unsupported`：任何 required live gate 失败、无法稳定复现、只能靠未批准能力实现，或证据不足。

禁止 `partial_supported`、`likely_supported`、`supported_with_assumptions`。即使输出 `unsupported`，仍应提交可复现 probe、脱敏证据和明确失败边界，供 main 固定 head 验收；auto route 保持禁用，manual handoff 继续可用。

## 启动前置门

1. 核对 worktree、branch、origin、固定 base 和 PR；不得在 main 工作。
2. fetch `origin/main`。main 只允许比固定 base 多 M-1C 登记类 `.agents` 提交；合入并记录实际 synced main SHA。出现产品代码或未知修改时停止。
3. worktree 必须干净；确认 `codex-cli 0.147.0`、GPT-5.6 Sol、`xhigh`、M-1B runtime digest `ea75b7760483b70be4535b2d966e1ccd92035f6c71362a79f2cb2d54d0088bcf`。
4. 先独立运行 M-1B 的 47 项 hermetic/subprocess contracts；失败时不得开始 live canary。
5. 所有 live 命令必须有显式进程、session、thread 和 turn 清理路径；先生成随机的非敏感 task/offer/session 标识，禁止复用真实业务任务。

## 确定性 probe 要求

必须由仓库内固定脚本完成接线、状态判断、脱敏和证据生成。Agent 只选择已定义场景并审查结果，不得手填结果 JSON。

1. probe 输入使用版本化 schema；固定 executable/argv，禁止 `shell=True`，禁止请求传入任意命令、路径或 steer 文本。
2. probe 只保存 allowlist 元数据：场景、相对时间、thread/turn/session 的单向摘要、方法/事件枚举、字段存在性、计数、固定 runtime digest 和最终分类。
3. 禁止保存 prompt、response、tool arguments、tool result 正文、raw notification、raw remote error、本机绝对路径和环境变量值。
4. 证据必须可重复生成；允许墙钟时间、进程 ID 和随机 canary ID 不同，但规范化摘要必须稳定。
5. 每个场景有总 deadline、无输出窗口和清理 deadline；任一子进程、MCP call 或 canary child 残留即失败。
6. live 时序可使用显式 test mode 缩短健康间隔和终态 deadline，但必须走同一生产代码路径；请求仍设置 `maxWaitMs=43_200_000`，并另证 `tool_timeout_sec=43200` 被真实 fresh session 接受。不得声称做过 12 小时墙钟 soak。

## Required live gate

以下每项都必须 pass 才能输出 `external_watcher_supported`：

1. **实际接线与跨进程可见性**：fresh Codex parent 通过真实 MCP transport 调用 watcher；watcher 的独立 app-server 连接能用 `includeTurns=false` 精确读取绑定 parent/child，并验证 child thread、parent thread、session 和 active turn 归属。不得通过时间、cwd 或“唯一最近 thread”猜测身份。
2. **健康静默**：受控 child 在至少两个加速健康周期内保持 active。单一 MCP call 持续 pending；每次 tick 不产生 MCP progress/result/log，不触发 parent model continuation，也不向 parent 添加额外 message/tool-result。证据只允许记录帧类型与计数，不读取正文。
3. **正常终态去重**：child 正常 final 后，parent 只被恢复一次；watcher 返回 `normal_terminal`，不调用 `turn/interrupt`、`turn/steer` 或 `turn/start`。必须区分 native mailbox/final 唤醒与 watcher tool completion，证明没有双重 parent continuation。
4. **异常顺序与作用域**：构造安全、确定、可清理的真实异常 child。watcher 只 interrupt 已绑定 child，观察精确 child/turn 终态确认后，只向绑定 parent active turn 发送一次固定 `gkd_watchdog_event`；顺序必须为 child interrupt -> bound terminal confirmation -> expected-turn steer，且从不 interrupt parent。
5. **expected-turn CAS**：使用错误 `expectedParentTurnId` 的 live 场景必须被拒绝；不重试、不搜索其他 parent/turn、不调用 `turn/start`，最终分类为 `parent_steer_rejected`。
6. **编排器故障唤醒**：在健康等待中确定性终止 watcher 所拥有的 app-server/MCP transport，parent 必须在有界时间收到 terminal tool error 并恢复；所有 worker 与子进程被回收，不永久静默。
7. **12 小时合同组合证据**：真实 fresh session 接受 43,200 秒 MCP tool timeout，live call 使用 43,200,000ms 上限并可因事件提前结束；M-1B 同一生产状态机的 fake-clock 12 小时单发 deadline 仍通过。该组合不等于 12 小时 soak，报告必须如实命名。
8. **父上下文 trace**：为 healthy、normal、abnormal、orchestrator-failure 各生成 allowlist frame-count trace，证明健康 tick 为零父上下文；禁止把“用户界面没显示 commentary”当证据。
9. **数据与清理**：证据和错误无正文、凭据、绝对路径、任意 steer 文本；临时配置、进程、worktree 外文件和 canary child 全部清理，生产配置 hash/mtime 不变。

任何平台行为无法安全制造第 4 项真实异常时，结论必须是 `unsupported`；不得用 fake fixture 顶替，但可以把无法制造的原因和已通过项保存在证据中。

## 实现与测试范围

允许的主要文件：

- `probes/app-server-watcher/**`
- `tests/watchdog/live/**` 及必要的现有 watcher tests
- `src/gkd_watchdog/**` 的最小 live 接线修复
- `evidence/m-1-external-watcher-live-gate/**`
- `tasks/m-1-external-watcher-live-gate/**`
- `.agents/**` 状态更新

要求：

1. Python 标准库优先；不得安装依赖、构建 Rust/Tauri、创建大型 cache 或运行与本任务无关的项目测试。
2. live probe 自身必须有 unit/subprocess negative tests，至少覆盖身份歧义、schema/version 漂移、正文泄漏、错误 expected turn、重复 terminal、超时和清理失败。
3. 如果修复 watcher core，必须重跑全部 M-1B contracts，并新增能使旧实现失败的回归测试。
4. 测试输出和 `delivery.md` 只能引用规则、文件、摘要和枚举，不回显命中的敏感值。

## 交付与暂停点

1. 生成 `evidence/m-1-external-watcher-live-gate/live-results.json` 及必要的 allowlist trace；机器结果只能由 probe 写入。
2. 生成 `delivery.md`，记录：二选一 outcome、实现/证据 commit、最终 head、PR、runtime/schema、每项 live gate、命令、规范化 digest、残余风险、生产配置不变证明和清理结果。
3. `git diff --check`；运行全部相关短时测试。不得运行大型本地构建。
4. required checks 未配置时记录 `required_checks_not_configured_bootstrap`，不得声称 CI 成功。
5. 使用简短中文提交说明，推送任务分支，将 PR 解除 Draft，确认 worktree clean。
6. 回报完整 40 位 head SHA、实现/证据 commit、outcome、测试数、证据 digest、PR 状态和未通过门。
7. 停止。不得合并 PR、修改生产配置、启用 auto route、创建后续任务或继续里程碑 0。
