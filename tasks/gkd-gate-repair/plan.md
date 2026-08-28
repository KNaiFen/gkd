# GKD Gate Repair Plan

## Goal

把生命周期排序、规划文档刷新和交付结果绑定收敛为三个由 canonical 服务生成和验证的门禁，使跨进程 GKD 任务可以恢复、返工并在固定事实上交付。

## User Decisions

- 以 trusted main `69cd40d` 为完整基线，独立任务完成后才重启 O4。
- 使用一个精确 `gkd_executor`、一个独立 `gkd_acceptor` 和 trusted main 合并；不启用 nested agent、fallback 或 automatic route 的替代入口。
- 不触碰生产、AIO、GitHub settings/Secrets、付费 runner、tag/Release 和已发布 bundle。

## Behavior And Defaults

- 每个事务事件具有由持久化状态派生的单调逻辑顺序；wall-clock 只作为审计时间，时间回拨不能使状态不可读。
- planning 文档刷新是显式、幂等、CAS 保护的 canonical transition；它只在 planning 阶段写入 digest，审批/授权只绑定刷新后的 plan material digest。
- 自动 delivery 必须提交并校验规范 result manifest；manifest 与 candidate output、固定 head、claim/执行 bundle 和实际 manifest 文件 digest 双向绑定。校验失败不写状态。
- 默认继续 fail-closed；不为旧调用者隐式生成或猜测缺失的机器事实。

## Scope

- 调整 `gkd_task` model/canonical/service/CLI、task-state schema 与相关文档。
- 新增最小逻辑时钟、planning refresh、delivery manifest 合同及 mutation/negative tests。
- 更新 acceptance/rework 对新字段和新文件边界的读取与校验，保持现有结果消费者和 fixed-head 语义。

## Non-Goals

- 不实现 watcher historical lane、O5 runtime fixtures、O6 optional pack、O7 contract index 或 O8 文档整理。
- 不改变已有外部 API 的业务含义，不改 GitHub 查询策略，不增加生产迁移或发布操作。

## Acceptance Criteria

- 新旧状态的 schema、model validator、事务和 CLI 都有可复核的正向/负向合同。
- 回拨时间、requirements digest drift、manifest digest/head/claim/bundle mismatch 均在状态写入前失败。
- 自动 delivery 的成功样例能被独立 acceptor 从干净 trusted checkout 重放；拒绝样例保留原始固定 head 和 finding。
- bundle manifest/lock 由 canonical 构建刷新，`git diff --check`、固定 head verifier 和独立 acceptance 通过。

## Compatibility

- 保留现有 UTC 字段、revision/CAS、task-state phase 矩阵、delivery document 绑定和 O3 canonical result consumer。
- 对没有新逻辑字段的历史状态提供显式版本判断或一次性 canonical migration；禁止在普通读取中修改文件。
- 保持 `gkd-task` 原有命令错误码风格；新增参数必须有稳定帮助文本并拒绝歧义组合。

## Security And Data

- manifest 和逻辑时钟只记录 digest、枚举、固定 head、逻辑序号和脱敏状态，不记录 prompt、transcript、凭据或本机路径。
- 所有输入在边界验证，文件必须是 canonical regular file；异常不吞掉，事务失败保持原状态和可恢复 journal。

## Migration

- executor 在隔离 candidate worktree 中运行完整本地合同；合并后只更新未发布 development bundle 和 project staging 事实。
- O4 必须从本任务 accepted merge 的完整 SHA 重新 bootstrap；旧 O4/O4-R1 的 blocked/rejected 记录只读保留。

## Public Interfaces

- 为 planning 文档刷新和 delivery result manifest 提供明确的 `gkd-task` 服务/CLI 入口或等价稳定参数；帮助文本说明 phase、CAS、文件边界和必需 digest。
- `gkd-task status/doctor/rework`、`gkd-role`、`gkd-ci-monitor` 和 O3 result schema 的既有调用继续可验证新状态。

## Execution Route

- trusted main 完成 requirements-ready、plan-approve、authorization、route、offer、claim 和 bridge handoff。
- 精确角色只能是 `gkd_executor`；executor 运行本地合同、生成 candidate output、提交 delivery manifest/document，并以 CLI 完成交付状态。
- 独立 `gkd_acceptor` 在显式 full head 上复核所有要求和固定头 CI；只有 trusted main 可 merge、closeout、更新持久记录和清理临时根。

## External Side Effects

- 允许一个隔离 task worktree/branch/PR、候选 bundle/evidence 临时根和只读 CI 查询。
- 禁止生产 `~/.codex`、AIO、GitHub settings/Secrets、付费 runner、tag/Release 和未批准的外部写入。

## Action Mode

`implement_and_merge_on_acceptance`

## Implementation Notes

- 先从现有 `advance_state`、`read_state`、`TaskService.propose_plan/requirements_ready/deliver`、acceptance/rework 和 schema 建立基线，再做最小字段和命令改动。
- 明确 manifest 的 canonical 文件格式、改变路径集合、digest 计算顺序和自动/手动路线差异；为逻辑顺序与 document refresh 添加 mutation kill tests，防止只改生产代码而合同未覆盖。
