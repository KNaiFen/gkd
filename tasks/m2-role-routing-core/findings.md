# 验收整改：GKD-M2-A 角色与路由核心

## 当前轮次

- 结论：实现整改完成，宿主握手仍阻塞
- PR：https://github.com/KNaiFen/gkd/pull/6
- 审查锚点：固定 head `cd8c89899039070c29b2c5209e7c5afaefba0616`
- 审查范围：M2-A 完整任务、固定 head 实现、回归测试与交付证据
- 已解决：F-001、F-002、F-003
- 未解决：F-004

## F-001：迁移回滚冻结会删除唯一原始 backup

- 状态：已整改，待独立复验
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

- 状态：已整改，待独立复验
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

## F-004：fresh trusted custom-role handshake 尚未建立

- 状态：仍阻塞
- 严重程度：阻塞
- 返工责任：执行 session
- 对应要求：requirements AC12；plan Acceptance 91-92；delivery Handshake Boundary
- 证据：`evidence/m2-role-routing-core/role-handshake.json` 的 `customRoleActivationProven=false`、`childTerminalObserved=false`、`parentTerminalObserved=false`，仅观察到 `thread.started`、`turn.started`、`item.completed`、`turn.completed`；交付正确保持 `blocked`。
- 当前行为与影响：当前宿主运行事实没有证明真实 `gkd_executor` custom-role activation，不能把 M2-A 标为 `role_routing_core_ready`，也不能启动 M2-B 或 automatic route。
- 必须达到的结果：在 F-001 至 F-003 修复并通过 deterministic/L2 合同后，重新执行一次允许的、隔离的 fresh-runtime short handshake；只有可信 host event 同时绑定预期角色、模型/effort/sandbox、bundle/role/config digest、child/parent terminal 且 path-free 时，才可改为 ready。宿主仍不给出可信事实时继续 `blocked`，不得用 fixture、自述或候选文件升级。
- 修改边界：不得修改生产配置、AIO、auto route 或运行真实一小时等待；只允许一次短时隔离握手与其最小化机器证据。
- 测试与文档：保留当前 blocked 证据；成功或再次 blocked 都要写入新的 delivery 与 evidence，明确宿主事实。
- 复验方式：独立 fresh runtime 审查完整事件与绑定 digest；任何缺失 child/parent terminal 或 custom-role activation 证据都保持阻塞。
- 执行回应：在 F-001 至 F-003 和全部 deterministic/L2 合同通过后执行了唯一一次隔离 fresh-runtime 尝试。宿主产生 5 个事件和 1 个 thread identity，但以 400 `invalid_request_error` 拒绝 ChatGPT-account runtime 中的 `gpt-5.6-sol`，退出码 1；未发生 custom-role activation，也没有 child/parent terminal。最小 path-free 证据记录 `CUSTOM_ROLE_MODEL_UNSUPPORTED`，不保留 prompt/response 文本，不使用 self-report、fixture 或候选文件升级结论。因此 M2-A outcome 继续为 `blocked`，PR 必须保持 Draft。

## 本轮边界

- 必须处理：F-001、F-002、F-003；F-004 必须重新尝试或如实保持阻塞。
- 不要顺带处理：M2-B 真实一小时等待、production install、AIO adoption、GitHub settings、里程碑 3/4/5、旧 watcher 或大型依赖构建。
- 可以自主决定：在不改变 requirements/plan 用户锁定行为的前提下选择 provider 锚定和 migration recovery 的最小实现方式。

再次交付前，执行 session 必须仅在本任务 worktree 处理上述 finding，新增针对性回归，重新运行 M2-A 与保留回归，更新 `delivery.md`/evidence，推送新的固定 head 并停在独立验收前。PR 仍不得由执行 session 自行验收或合并。

## CI 或环境问题

无 configured checks；事实仍为 `required_checks_not_configured_bootstrap`，不构成 CI 成功。

## 建议项

- 无。
