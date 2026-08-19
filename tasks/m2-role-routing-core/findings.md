# 验收整改：GKD-M2-A 角色与路由核心

## 当前轮次

- 结论：F-005 已整改；F-004 v5 进行中，v4 wait-before-spawn 重新分类为 probe orchestration miss
- PR：https://github.com/KNaiFen/gkd/pull/6
- 本轮 live 授权锚点：固定 head `26b8e9c185a0bdf365266efdb45f42260c8922b3`
- 审查范围：M2-A 完整任务、固定 head 实现、回归测试与交付证据
- 已解决：F-001、F-003
- 部分解决：F-002 的调用者自选 provider 和 freshness 问题已处理；真实 host attestation 仍由 F-004 阻塞
- 未解决：F-004

## F-001：迁移回滚冻结会删除唯一原始 backup

- 状态：已整改，独立复验通过
- 严重程度：阻塞
- 返工责任：执行 session
- 对应要求：requirements AC7；plan Migration 135-136；execution Required Contracts 155-157
- 证据：`canonical/payload/lib/gkd_role/migration.py:237-254`；独立临时目录复现 `MIGRATION_FROZEN` 后 `home_exists=false`、`backup_count=0`、仅留下 freeze 文件
- 当前行为与影响：回滚本身失败时，代码写出 `MIGRATION_FROZEN`，但无条件 `finally` 删除 `backup`。冻结结果不再保留可恢复的原始 home，违反 exact preimage / freeze safely，并可能造成临时迁移数据丢失。
- 必须达到的结果：回滚不确定时保留原始 backup、stage 和机器可读 freeze 所需的恢复材料；成功恢复时原始 home 与所有受保护字节逐字节一致；任何路径都不静默删除唯一 preimage。
- 修改边界：仅迁移事务、恢复清理和对应测试；保持临时目标限制、同事务 legacy role 替换、重复迁移幂等和生产边界不变。
- 测试与文档：新增注入 rollback `os.replace` 失败的回归，断言 home/backup/freeze 的可恢复状态；更新 delivery 的实际验证。
- 复验方式：在独立临时 home 运行 staged、old_moved、new_moved 及 rollback-failure 场景；检查原始文件 digest、backup 保留和 freeze JSON。
- 执行回应：`apply_migration` 现在只在未冻结路径清理 stage/backup。rollback rename 失败时保留原始 backup 与 stage，并在 freeze 记录中绑定 plan、before、backup 和 stage digest。新增 staged、old_moved、new_moved 及 rollback-failure 注入合同；rollback-failure 断言 backup 字节等于原始 preimage、stage 存在且 freeze digest 一致。

## F-002：activation provider 没有可信根或新鲜度绑定

- 状态：部分整改；可信写入者问题转 F-005
- 严重程度：阻塞
- 返工责任：执行 session
- 对应要求：requirements AC4；plan Behavior 35-37、Security 110-118
- 证据：`canonical/payload/lib/gkd_role/cli.py:76-113` 接受调用者提供的任意候选外绝对 provider 与 digest；`canonical/payload/lib/gkd_task/cli.py:123-131,176-208` 在 claim/recovery 中同样接受调用者提供的 provider digest；现有 `tests/role_routing/test_activation.py:190-213` 明确把临时目录中的 fixture provider 作为成功 host activation。`record_activation` 也未将 activation 时间与 offer/envelope 的有效窗口绑定。
- 当前行为与影响：字段、角色和 bundle digest 虽然严格校验，但“谁有资格写 host-runtime-event”没有被 trusted main、授权或固定 provider 身份锚定；同一用户/执行 session 可以自行选择 provider 并生成满足 schema 的激活事实，旧激活也没有 freshness 检查。这不能证明 exact custom-role activation，也不能满足 stale/candidate-created evidence 必须拒绝的合同。
- 必须达到的结果：只有 trusted main/host-owned、与本 bundle/任务授权和确切 offer/envelope 绑定的 provider 才能写入 activation；provider 身份和 digest 不得由候选执行者自由选择；activation 必须在 offer 有效窗口内且不可重放；candidate-created provider、stale provider、cross-task/cross-role/digest drift 均在 claim 前失败。
- 修改边界：仅 activation provider API、offer/authorization/runtime 绑定和对应 schema/tests；不得放宽 capability、CAS、lock、journal、claim receipt 或 delivery/acceptance 约束，不得写生产 `~/.codex`。
- 测试与文档：新增任意临时 provider、provider digest 未锚定、activation 早于 offer/晚于 expiry、跨任务/重放的负向测试；记录 trusted provider 的实际来源与证据等级。
- 复验方式：从全新临时 runtime/home 运行完整 activation -> claim；尝试替换 provider、伪造 digest、使用过期 activation，均应在 claim commit 前失败；成功路径只能消费由受信 host 生成的固定 activation。
- 执行回应：canonical role source 固定声明 `codex-host-runtime` provider contract，provider digest 由 locked bundle catalog 派生；role/task CLI 不再接受调用者选择的 provider command、provider digest 或 bundle root。当前无可信宿主适配器时 `activation-record` 固定 fail-closed。Activation 同时绑定 offer 创建/过期时间，v2 claim 持久绑定 activation/envelope，recover、delivery 与 acceptance 重验 exact task/offer/envelope/role/config/bundle/window。新增任意临时 provider、伪造 catalog digest、过期 activation、跨任务/跨角色和 replay 负向合同；L2 正向路径仅使用测试内 host seam，不作为 F-004 可信证据。

## F-003：等待状态机忽略 deadlineAt

- 状态：已整改，待独立复验
- 严重程度：阻塞
- 返工责任：执行 session
- 对应要求：requirements AC6；plan Behavior 38-43；execution Required Contracts 152-154
- 证据：`canonical/payload/lib/gkd_role/waiting.py:35-38` 只校验 `deadlineAt` 的算术关系；`canonical/payload/lib/gkd_role/waiting.py:58-85` 的 `healthy_timeout` 分支从不比较 `observedAt` 与 `deadlineAt`。独立复现以 `startedAt=00:00`、`observedAt=13:00` 的首个健康 timeout 仍返回 `wait_again`，并将 `deadlineAt` 保留为 `12:00`。
- 当前行为与影响：超过 12 小时仍可产生静默 re-wait，违反 12-hour termination contract；M2-B 可能在 deadline 后继续等待。
- 必须达到的结果：任一健康 timeout 在或超过 deadline 时只产生一次 `deadline_timeout`、一次 bound interrupt 和 terminal state；deadline 前的 1-11 个完整 interval 才能返回 `wait_again`；重复/延迟 observation 不得绕过截止点。
- 修改边界：仅 wait state transition、schema/状态事实和 fake-clock tests；保持原生 `timeout_ms=3600000`、同一 agent、healthy timeout 静默和最多 12 个 interval。
- 测试与文档：新增首个 observation 已过 deadline、同一 timestamp 重放、超过 deadline 的 child/error/user intervention 场景；更新 M2 evidence/contract 结果。
- 复验方式：fake clock 覆盖 00:00 至 12:00+；检查每条决定的 outcome、interrupt once、terminal/state digest 及禁止继续 wait。
- 执行回应：`healthy_timeout` 现在先比较绝对 `deadlineAt`；任一在或超过 deadline 的 observation 直接固定 `completedIntervals=12`、写入唯一 terminal 并返回一次 bound interrupt。deadline 前仍要求下一个完整小时，重复 timestamp 失败。新增首个 observation 为第 13 小时、延迟 observation、重复 timestamp 与 terminal 后重放合同；原生 `timeoutMs=3600000`、同 agent、1-11 次静默 re-wait 和 child/error/user intervention 语义保持不变。

## F-004：fresh trusted custom-role handshake

- 状态：已通过；host rollout 记录补足 stdout 压缩遗漏的 spawn/terminal 事实
- 严重程度：已关闭
- 返工责任：执行 session
- 对应要求：requirements AC12；plan Acceptance 91-92；delivery Handshake Boundary
- 证据：`evidence/m2-role-routing-core/role-handshake.json` schema v2 绑定 deterministic preflight、role/config/bundle/project/Skill/AGENTS digest 与 host facts；`m2-contracts.json` 绑定同一 handshake。用户在精确 fresh Git root 通过正常 Codex trust UI 后，parent rollout 记录包含唯一 `agents.spawn_agent`，`agent_type=gkd_executor`、`task_name=gkd_executor_handshake`、`fork_turns=none`；sub-agent activity 绑定 child thread；child 与 parent rollout 各有独立 `task_complete` terminal marker；Codex exit code 为 0。规范化 facts 为 `spawnCount=1`、`activatedRoles=[gkd_executor]`、无 unexpected/downgrade/fallback、child/parent terminal 均 true。v3 strict 失败、隔离模式 HTTP 400 与早期 stdout wait-only 均保留为历史诊断事实，不用于否定本次 rollout 证据。
- 当前行为与影响：F-004 的 custom-role activation/child-parent terminal 合同已满足；M2-A 可交付 `role_routing_core_ready`，但 route 仍强制 `manual_only`，不能启动 M2-B 或 automatic route。
- 必须达到的结果：确定性 preflight 负责生成物与 digest，host rollout 负责 parent turn、唯一 exact `gkd_executor` spawn、无 fallback 和 child/parent terminal；本轮两类证据均通过。
- 修改边界：使用正常本机 Codex 登录态和受信项目路径下 fresh Git repo 内的项目级 `.codex/agents`/`.codex/skills`。不得设置 alternate `CODEX_HOME`、读取/复制认证材料、写生产配置、修改 AIO、启用 auto route 或运行真实一小时等待。
- 测试与文档：保留旧 blocked/diagnostic 证据作为历史；session rollout 原文不进入仓库，只提交最小 path-free facts。fresh probe repo 已清理；宿主自动维护的 `~/.codex/sessions` 原始 rollout 未删除，以遵守本轮不得清理生产 Codex 状态的边界。
- 复验方式：独立读取授权 probe 的 parent/child rollout 记录，抽取 function-call 名称、exact role 参数、sub-agent activity、task-complete marker、exit code 和 hashed thread identity；不使用 prompt 正文、自述或 fixture 补足事实。
- 历史执行回应：隔离模式命令固定 parent `--model gpt-5.6-sol` 并使用 `--ignore-user-config`，宿主在 parent turn 前以 HTTP 400 `invalid_request_error` 拒绝 ChatGPT account 使用该模型，Codex exit 1；分类 `HOST_MODEL_UNSUPPORTED_FOR_CHATGPT_ACCOUNT`。该事实不再代表 v3 正常 provider/routing 环境，但继续作为历史负向证据。
- v3 静态执行回应：live command 已删除 `--ignore-user-config`、parent `--model` 和 parent effort override，保留 ephemeral、strict-config、JSONL、workspace-write、`approval_policy="never"`、project trust、`agents.enabled=true` 与固定 prompt；child TOML 仍固定 Sol/xhigh/workspace-write。tests-only preflight 使用 `command -v codex`，不设置 alternate `CODEX_HOME`，并在调用前后核对生产保护面和临时 repo。正常用户配置 strict parse 先于 project role discovery 失败，脱敏分类 `USER_CONFIG_PARSE_FAILED`；未运行 `codex exec` 模型 turn，未消耗新 live attempt，生产配置未改变。当前不具备请求下一次 live 授权的条件。
- v4 静态执行回应：live command 进一步删除 `--strict-config`，继续使用正常 `CODEX_HOME`、provider/auth/model routing，并保留 ephemeral、JSONL、workspace-write、`approval_policy="never"`、project trust、`agents.enabled=true` 与固定 prompt。生成 project config 与 role TOML 由 `tomllib` 严格解析并与 canonical source 精确比较；非 strict app-server 到达预期 no-transport，且无 trust disabled、malformed role/project 或其他 fatal startup。该边界只记为项目角色定义已接受，不升级为 custom-role activation。生产配置与临时 repo 前后不变，模型调用与 live attempt 仍为 0；当前具备提交新的静态 fixed head 并等待一次独立 live 授权的条件。
- v4 live 执行回应：授权锚点、本地/upstream/远端/PR head、工作树、Codex executable digest、静态 preflight、零调用计数和生产/AIO digest 全部先通过。随后从新临时 repo 使用冻结命令执行一次真实 `codex exec`，未使用 strict/ignore-user-config、parent model/effort override、降级、角色替换或 fallback。宿主完成 parent turn 并 exit 0，但事件中只有无目标的 collab `wait`，未启动任何角色；因此 `activatedRoles=[]`、`childTerminalObserved=false`、`parentTerminalObserved=true`。Agent 消息正文未参与判断。没有第二次调用；原始 JSONL、stderr、临时 repo 和调用元数据已删除，生产/AIO 与 repo 均未漂移。
- v5 计划回应：v4 只证明 parent 未遵循 Prompt，不能作为 custom role 实现阻塞。任务级合同改为本 execution session 自主完成静态检查、短时 probe、JSONL 诊断和有界重试；最终交付 head 才固定。用户通过正常 trust UI 建立该精确 repo 的信任后，live command 收敛为 `codex exec --json <fixed-prompt>`，Prompt 明确先调用结构化事件实际使用的 `spawn_agent` 并指定唯一 `gkd_executor`，spawn 成功后才允许 wait。
- v5 静态诊断：nested fresh Git repo 即使位于当前 worktree 下，Codex 仍明确报告该新 Git 根未受信并禁用其 `.codex` 层；该次仅运行 app-server，`modelInvocations=0`、`liveAttemptsConsumed=0`。用户随后在该精确目录通过正常 Codex trust UI 选择继续并退出，用户配置保护面 digest 因该外部动作从 `db47d57e...` 变为 `f1b9cb27...`；execution session 未写入、读取或回滚配置。最终 static/live 命令不传 trust、sandbox、approval、agents-enabled 或 parent model/effort override，并以用户动作后的 digest 为调用期非漂移基线。
- v5 live 诊断 1：首轮正常环境 parent exit 0 并 terminal，但结构化事件再次只有空 receiver/state 的 `wait`，没有 spawn 或 child。宿主事件将实际工具名记录为无 namespace 的 `wait`；该轮分类为 `PROBE_ORCHESTRATION_MISS_WAIT_BEFORE_SPAWN`，不作为 custom role 拒绝。下一轮 Prompt 使用同一实际命名层的 `spawn_agent`/`wait` 并固定 FIRST/SECOND 顺序。
- v5 live 诊断 2-3：第二轮使用实际 `spawn_agent`/`wait` 名称与 FIRST/SECOND 顺序后仍仅产生空目标 `wait`；第三轮完全移除 wait 指令后，parent 直接输出 terminal marker 且没有任何 collab tool event。两轮均 exit 0、无 spawn/alternate role/fallback，分别分类为 `PROBE_ORCHESTRATION_MISS_WAIT_BEFORE_SPAWN` 和 `PROBE_ORCHESTRATION_MISS_PARENT_SHORTCUT`。最终合理 Prompt 修正把委派本身定义为不可由 parent 自行完成的成果，并要求 spawn 不可用时显式失败、禁止无目标 wait。
- v5 live 结论修正：用户在精确 probe Git 根选择正常 Codex trust UI 的 `Yes, continue` 后退出交互提示。最新 trusted-path parent rollout 实际记录了 `agents.spawn_agent` function call，随后 child activity、child `task_complete` marker 和 parent `task_complete` marker；session 记录比 stdout JSONL 更完整，wait output 的“interrupted by new input”不影响两个独立 task-complete 事实。新增 `normalize_rollout_facts` 只保留 path-free event/role/terminal/exit facts，F-004 关闭。

## F-005：安装态 activation writer 仍可由候选进程直接调用

- 状态：已整改，安装态与库级路径均 fail-closed；可信宿主边界仍未提供
- 严重程度：阻塞
- 返工责任：执行 session
- 对应要求：requirements AC4；plan Behavior 35-37、Security And Data；execution Required Contracts
- 证据：`canonical/payload/lib/gkd_role/activation.py:70-119` 的 `record_activation` 接受调用者构造的 expected/observation/nonce 并写入同权限 runtime；`canonical/payload/lib/gkd_role/activation.py:125-151` 的 `ActivationEvidenceProvider` 只校验记录字段和 catalog digest；`tests/role_routing/test_activation.py:63-75` 直接调用该安装态函数作为成功 host activation。独立临时 runtime 复现未调用 host adapter 或 `gkd-role activation-record`，仅使用候选选择的 `agentId` 调用函数，即得到 `activation_recorded`，随后 claim 返回 `implementing`。
- 当前行为与影响：CLI 的 `ACTIVATION_PROVIDER_UNAVAILABLE` 只封住命令行入口；executor 等权限进程仍能 import bundle 中的 writer，自行构造满足 schema 的 `host-runtime-event`。固定 provider 名称/digest 只能约束字段，不能证明记录由 trusted main/host 写入。这违反 candidate-written evidence 必须在 claim commit 前失败的合同。
- 必须达到的结果：canonical/installable payload 不得暴露候选可调用并能生成可信 activation 的 writer。测试 host seam 必须只存在于 tests，不能进入 manifest 或安装 inventory。真实成功路径必须由候选无法调用或伪造的 host/main 边界产生最小 receipt；若当前宿主没有这种边界，安装态 activation/claim 必须 fail-closed，不得以普通 Python API、CLI 包装或同权限文件冒充。
- 修改边界：仅 activation authority/writer/receipt 边界及测试；不得放宽 task CAS、lock、journal、claim receipt、delivery/acceptance、F-004 host evidence 或 manual-only 路由。若无法在批准范围内建立候选不可访问的宿主边界，停止并提交具体 plan delta。
- 测试与文档：新增 executor-equivalent 独立子进程测试，尝试 import/call canonical 或 installed payload 中全部 activation 写入路径，必须在写记录或 claim commit 前失败；断言测试 seam 不在 manifest、bundle 和 installed inventory。保留 freshness、replay、cross-task/role/digest 测试。
- 复验方式：从 clean temporary runtime，以 executor 等权限进程尝试构造完整 observation、直接调用 writer、替换 receipt 和重放；均须失败。真实正向 claim 只能在已证明候选不可伪造的 host receipt 存在时通过。
- 执行回应：canonical payload 已移除 `gkd_role.activation.record_activation`、`ActivationEvidenceProvider`、`RuntimeStore.write_activation`、`FixtureEvidenceProvider` 与 `make_fixture_evidence`；两类 fixture seam 分别位于 `tests/role_routing` 和 `tests/task_core`，不进入 source、manifest、bundle 或安装 inventory。正常公开 CLI/library v2 claim/recovery 在无真实 host attestation 时统一返回 `TRUSTED_ACTIVATION_BOUNDARY_UNAVAILABLE`，并新增 runtime/tracked bytes 不变断言。未增加 monkeypatch/subclass 防御、daemon、IPC 或签名协议；CAS、锁、journal、recovery、freshness、replay、cross-task/cross-role、digest drift 回归全部保留。plan delta 仍为 `candidate-inaccessible-host-attestation-required`。

## 本轮边界

- 必须处理：仅继续 F-004；F-005 保持已整改，不再修改 activation/claim/recovery 设计。F-001/F-003 只需保留回归；F-002 的 provider/freshness 修复不得回退。
- 不要顺带处理：M2-B 真实一小时等待、production install、AIO adoption、GitHub settings、里程碑 3/4/5、旧 watcher 或大型依赖构建。
- 可以自主决定：在不改变 requirements/plan 用户锁定行为的前提下选择 provider 锚定和 migration recovery 的最小实现方式。

本轮只处理 F-004。当前 Prompt 已授权必要的短时本机 Codex 验证和有限诊断重试；只有正常 Codex 在正确工具名和合理诊断后仍返回可复现硬错误，或需要越过生产/AIO/M2-B 边界时才允许 blocked。

## CI 或环境问题

无 configured checks；事实仍为 `required_checks_not_configured_bootstrap`，不构成 CI 成功。

## 建议项

- 无。
