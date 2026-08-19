# 验收整改：GKD-M2-A 角色与路由核心

## 当前轮次

- 结论：F-001 至 F-005 均已整改，等待独立验收
- PR：https://github.com/KNaiFen/gkd/pull/6
- 本轮整改起点：固定 head `ba9c7fe5c51a54cfb2ff6eb634f5e0374e122d0b`
- 审查范围：M2-A 完整任务、固定 head 实现、回归测试与交付证据
- 已解决：F-001、F-002、F-003、F-004、F-005
- 未解决：无；M2-B 一小时门禁不属于本任务

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

- 状态：已整改，回归通过，等待独立验收
- 严重程度：阻塞
- 返工责任：执行 session
- 对应要求：requirements AC4；plan Behavior 35-37、Security 110-118
- 历史证据（已修复）：旧 `gkd-role`/`gkd-task` CLI 接受调用者提供的 provider command/digest，旧测试以临时 fixture provider 作为成功 activation，且 activation 时间未绑定 offer window。
- 当前行为与影响：字段、角色和 bundle digest 虽然严格校验，但“谁有资格写 host-runtime-event”没有被 trusted main、授权或固定 provider 身份锚定；同一用户/执行 session 可以自行选择 provider 并生成满足 schema 的激活事实，旧激活也没有 freshness 检查。这不能证明 exact custom-role activation，也不能满足 stale/candidate-created evidence 必须拒绝的合同。
- 必须达到的结果：只有 trusted main/host-owned、与本 bundle/任务授权和确切 offer/envelope 绑定的 provider 才能写入 activation；provider 身份和 digest 不得由候选执行者自由选择；activation 必须在 offer 有效窗口内且不可重放；candidate-created provider、stale provider、cross-task/cross-role/digest drift 均在 claim 前失败。
- 修改边界：仅 activation provider API、offer/authorization/runtime 绑定和对应 schema/tests；不得放宽 capability、CAS、lock、journal、claim receipt 或 delivery/acceptance 约束，不得写生产 `~/.codex`。
- 测试与文档：新增任意临时 provider、provider digest 未锚定、activation 早于 offer/晚于 expiry、跨任务/重放的负向测试；记录 trusted provider 的实际来源与证据等级。
- 复验方式：从全新临时 runtime/home 运行完整 activation -> claim；尝试替换 provider、伪造 digest、使用过期 activation，均应在 claim commit 前失败；成功路径只能消费由受信 host 生成的固定 activation。
- 执行回应：canonical role source 固定声明 `codex-host-runtime` provider contract，provider digest 由 locked bundle catalog 派生；role/task CLI 不接受调用者选择 provider command、provider digest 或 bundle root。`TrustedMainActivationAuthority` 只接收已验证的 host facts 并绑定 exact task/offer/envelope/role/config/bundle/window；provider 在同一 task lock/journal/claim-receipt 流程中一次性消费。CLI 与无 provider 的默认 library 路径仍在写入前返回 `TRUSTED_ACTIVATION_BOUNDARY_UNAVAILABLE`。任意 provider、伪造 digest、过期、跨任务、跨角色、replay 与 recovery 回归均保留。

## F-003：等待状态机忽略 deadlineAt

- 状态：已整改，回归通过，等待独立验收
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
- 证据：`evidence/m2-role-routing-core/role-handshake.json` schema v2 绑定 deterministic preflight、role/config/bundle/project/Skill/AGENTS digest 与 host facts；`m2-contracts.json` 绑定同一 handshake。用户在精确 fresh Git root 通过正常 Codex trust UI 后，parent rollout 记录包含唯一 `agents.spawn_agent`，参数精确为 `agent_type=gkd_executor`、`task_name=gkd_executor_handshake`、`fork_turns=none`；对应 `sub_agent_activity` 提供实际 child thread identity，只有该 exact child rollout 中的 terminal marker 被接受。规范化 facts 计算 spawn 参数、child binding、alternate role/downgrade/fallback、child/parent terminal 和 Codex exit code，不再硬编码安全结论。v3 strict 失败、隔离模式 HTTP 400 与早期 stdout wait-only 只保留在明确 historical 字段。
- 当前行为与影响：F-004 的 custom-role activation/child-parent terminal 合同已满足；M2-A 可交付 `role_routing_core_ready`，但 route 仍强制 `manual_only`，不能启动 M2-B 或 automatic route。
- 必须达到的结果：确定性 preflight 负责生成物与 digest，host rollout 负责 parent turn、唯一 exact `gkd_executor` spawn、无 fallback 和 child/parent terminal；本轮两类证据均通过。
- 修改边界：使用正常本机 Codex 登录态和受信项目路径下 fresh Git repo 内的项目级 `.codex/agents`/`.codex/skills`。不得设置 alternate `CODEX_HOME`、读取/复制认证材料、写生产配置、修改 AIO、启用 auto route 或运行真实一小时等待。
- 测试与文档：保留旧 blocked/diagnostic 证据作为历史；session rollout 原文不进入仓库，只提交最小 path-free facts。fresh probe repo 已清理；宿主自动维护的 `~/.codex/sessions` 原始 rollout 未删除，以遵守本轮不得清理生产 Codex 状态的边界。
- 复验方式：独立读取授权 probe 的 parent/child rollout 记录，抽取 function-call 名称、exact role 参数、sub-agent activity、task-complete marker、exit code 和 hashed thread identity；不使用 prompt 正文、自述或 fixture 补足事实。
- 历史执行回应：隔离模式命令固定 parent `--model gpt-5.6-sol` 并使用 `--ignore-user-config`，宿主在 parent turn 前以 HTTP 400 `invalid_request_error` 拒绝 ChatGPT account 使用该模型，Codex exit 1；分类 `HOST_MODEL_UNSUPPORTED_FOR_CHATGPT_ACCOUNT`。该事实不再代表 v3 正常 provider/routing 环境，但继续作为历史负向证据。
- 历史 v3 静态执行回应：live command 已删除 `--ignore-user-config`、parent `--model` 和 parent effort override，保留 ephemeral、strict-config、JSONL、workspace-write、`approval_policy="never"`、project trust、`agents.enabled=true` 与固定 prompt；child TOML 仍固定 Sol/xhigh/workspace-write。tests-only preflight 使用 `command -v codex`，不设置 alternate `CODEX_HOME`，并在调用前后核对生产保护面和临时 repo。正常用户配置 strict parse 先于 project role discovery 失败，脱敏分类 `USER_CONFIG_PARSE_FAILED`；未运行 `codex exec` 模型 turn，未消耗新 live attempt，生产配置未改变。
- 历史 v4 静态执行回应：live command 进一步删除 `--strict-config`，继续使用正常 `CODEX_HOME`、provider/auth/model routing，并保留 ephemeral、JSONL、workspace-write、`approval_policy="never"`、project trust、`agents.enabled=true` 与固定 prompt。生成 project config 与 role TOML 由 `tomllib` 严格解析并与 canonical source 精确比较；非 strict app-server 到达预期 no-transport，且无 trust disabled、malformed role/project 或其他 fatal startup。该边界只记为项目角色定义已接受，不升级为 custom-role activation。
- 历史 v4 live 执行回应：授权锚点、本地/upstream/远端/PR head、工作树、Codex executable digest、静态 preflight、零调用计数和生产/AIO digest 全部先通过。随后从新临时 repo 使用冻结命令执行一次真实 `codex exec`，未使用 strict/ignore-user-config、parent model/effort override、降级、角色替换或 fallback。宿主完成 parent turn 并 exit 0，但 stdout 事件中只有无目标的 collab `wait`，未启动任何角色；该诊断已被完整 rollout 事实取代。
- 历史 v5 计划回应：v4 stdout 只证明 parent 未遵循 Prompt，不能作为 custom role 实现阻塞。任务级合同改为本 execution session 自主完成静态检查、短时 probe、JSONL 诊断和有界重试；最终交付 head 才固定。
- 历史 v5 静态诊断：nested fresh Git repo 即使位于当前 worktree 下，Codex 仍明确报告该新 Git 根未受信并禁用其 `.codex` 层；用户随后在该精确目录通过正常 Codex trust UI 选择继续并退出，execution session 未写入、读取或回滚配置。
- 历史 v5 live 诊断：早期 stdout 只有空目标 `wait` 或 parent shortcut，分别分类为 orchestration miss；这些结果已被同一授权 test-session 的完整 parent/child rollout 事实取代。
- v5 live 结论修正：用户在精确 probe Git 根选择正常 Codex trust UI 的 `Yes, continue` 后退出交互提示。最新 trusted-path parent rollout 实际记录了 `agents.spawn_agent` function call，随后 child activity、child `task_complete` marker 和 parent `task_complete` marker；session 记录比 stdout JSONL 更完整，wait output 的“interrupted by new input”不影响两个独立 task-complete 事实。`normalize_rollout_facts` 要求唯一 exact spawn 和 exact child identity，只保留 path-free event/role/terminal/exit facts；wrong task/fork、unrelated terminal、multiple spawn、wrong identity 与 fallback 均有负向合同，F-004 关闭。

## F-005：activation → claim 缺少可信 main 正向桥接

- 状态：已整改，回归通过，等待独立验收
- 严重程度：已关闭
- 返工责任：执行 session
- 对应要求：requirements AC4；plan Behavior And Defaults、Security And Data；execution Required Contracts
- 历史证据（已取代）：旧安装态 writer 可由候选公开导入并自行构造 `host-runtime-event`；后续移除所有 writer 虽使候选 fail-closed，却也使可信 main 无法完成正向 claim。
- 当前行为与影响：canonical payload 提供 `TrustedMainActivationAuthority` 与一次性 provider。trusted main 根据已验证的 host facts 写最小 activation record，随后 exact offer/envelope claim 消费 activation receipt，并可完成 delivery。候选公开 `gkd-role activation-record`、`gkd-task claim --activation-id` 和普通无 provider `TaskService` 仍在任何 activation/runtime/claim/tracked 写入前 fail-closed。
- 威胁模型：这是 trusted main 与 candidate 支持路径之间的工作流权限边界，不是同一 OS 用户进程间的安全隔离。恶意 monkeypatch、私有 API 调用或直接改 runtime 文件明确为非目标；未实现签名、daemon、IPC、密钥或额外安全基础设施。
- 测试与文档：完整临时任务正向合同覆盖 main-owned activation receipt → exact offer/envelope claim → claim-indexed receipt → delivery。保留 missing/candidate-written、stale window、replay、cross-task、cross-role、digest drift、并发单赢家、receipt recovery 及候选 CLI/library fail-closed；`FixtureEvidenceProvider`、`make_fixture_evidence` 和 tests-only seam 不进入 canonical payload、manifest 或安装 inventory。
- 复验方式：运行 role-routing activation/packaging 合同并检查候选失败前后的 Git head、revision 和 runtime bytes；成功路径只能显式传入 trusted-main provider。

## 本轮边界

- 必须处理：收紧 F-004 rollout 归一化，并按简化威胁模型补齐 F-005 trusted-main activation → claim → delivery 正向桥接；F-001/F-003 保留回归，F-002 的 provider/freshness 绑定不得回退。
- 不要顺带处理：M2-B 真实一小时等待、production install、AIO adoption、GitHub settings、里程碑 3/4/5、旧 watcher 或大型依赖构建。
- 可以自主决定：在不改变 requirements/plan 用户锁定行为的前提下选择 provider 锚定和 migration recovery 的最小实现方式。

本轮禁止新 Codex live probe 或模型 turn，只离线读取并归一化既有授权 test-session rollout。只有需要超出上述简化威胁模型、修改生产/AIO 或运行 M2-B 时才允许 blocked。

## CI 或环境问题

无 configured checks；事实仍为 `required_checks_not_configured_bootstrap`，不构成 CI 成功。

## 建议项

- 无。
