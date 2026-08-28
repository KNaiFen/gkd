# GKD Gate Repair Requirements

## Goal

修复 GKD 任务协调层在跨进程执行时暴露的三个门禁缺陷：生命周期事件的 wall-clock 逆序、规划文档 digest 在受控变更后的刷新死锁、delivery 与 candidate result manifest 的绑定不足。修复必须保持单一事实源、单 writer、固定 head 和 fail-closed 语义，并让后续 O4 可以从新任务重新开始。

## User Decisions

- 本任务从 trusted main 当前基线 `69cd40d` 建立，作为 O4 重启前置任务；不得手改或复活已阻塞的 O4/O4-R1 状态。
- 只允许一个精确的 `gkd_executor` 实施和交付，一个独立的 `gkd_acceptor` 按固定 head 验收；trusted main 负责合并、记录和清理。
- 只修改 GKD canonical 源码、schema、合同测试和本任务记录；不修改生产 `~/.codex`、AIO、GitHub settings/Secrets、付费 runner、tag/Release 或已发布资产。
- 新机制必须通用、可移植，不得写死仓库、用户名、本机绝对路径、运行时身份或凭据。

## Scope

- 为任务生命周期增加持久化的逻辑顺序或等价的跨进程时间绑定，使事件在相同或回拨的 wall-clock 下仍能被确定性验证；保留现有 UTC 时间字段供审计，并为旧状态提供明确的兼容或迁移边界。
- 增加受信任的规划文档刷新边界：在 `planning` 阶段由 canonical 服务一次性重新计算 requirements、plan、implementation 的实际 digest 和 plan material digest，并通过事务更新状态；进入 `awaiting_claim`、`implementing` 或更后阶段后，文档 digest 必须保持不可变，漂移仍 fail-closed。
- 将 delivery 的 candidate result manifest 纳入 canonical 绑定。manifest 必须是规范 JSON，明确绑定任务、base/head、执行 bundle（自动路线时）、candidate output bundle digest、scope/result manifest digest 及其生成事实；`deliver` 只能接受与固定 head、当前 claim 和实际文件内容一致的 manifest，不再信任无法验证的自由文本声明。
- 同步 task-state schema、CLI/服务接口、acceptance/rework 路径、README 或操作契约，以及覆盖正常和负向场景的最小合同测试；不得削弱现有 claim、activation、delivery-document、结果消费者和 fixed-head 门禁。

## Non-Goals

- 不改变 watcher/probe 的验证范围，不实现 O4 本身，也不提前实现 O5-O8。
- 不重写 GitHub adapter、自动路由、watcher 协议、结果 scope 业务逻辑或发布流程；只在必要处接入新的绑定字段和校验。
- 不通过放宽校验、吞掉错误、自动猜测时间、接受旧 digest 或删除负向测试来规避已有失败。
- 不要求生产安装、AIO 迁移、GitHub 外部设置或新的第三方依赖。

## Acceptance Criteria

1. 合同测试证明两个独立进程使用相同、回拨或边界 wall-clock 时，生命周期 history 仍按持久化逻辑顺序验证；篡改顺序、逻辑计数或绑定事实会稳定返回明确错误。
2. 合同测试证明 planning 阶段修改 requirements/plan/implementation 后，只有 canonical 刷新事务能使状态恢复一致并继续审批；进入 implementing 后同样修改仍返回 `DOCUMENT_DIGEST_DRIFT` 或等价 fail-closed 错误，且不产生部分状态。
3. 自动路线的 delivery 缺少 manifest、manifest 非 canonical、任务/base/head/claim/bundle/result digest 任一不匹配时均拒绝且不推进 revision；匹配的 manifest 在预提交的 delivery 文件边界内成功交付。手动路线的既有最小语义保持兼容，但不得绕过已有文档和 fixed-head 校验。
4. `status`、`doctor`、`rework` 和独立 acceptance 能读取新状态；旧的已接受任务要么继续有效，要么由明确、可测试的迁移路径升级，不能静默改变历史事实。
5. 相关 task-core、runtime-bridge、rework、结果消费者和 schema 合同通过；候选 bundle、manifest/lock、delivery 记录和测试摘要的 digest/固定 head 一致。
6. 变更不引入绝对路径、凭据、新外部依赖或生产/AIO/GitHub settings 副作用；失败、取消和重试路径不留下不可恢复的 coordination 半状态。
