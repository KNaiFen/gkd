# P2 激活交接流程修复 R2 Bootstrap 需求

## Goal

消除 trusted-main spawn 后依赖第二条 Agent 消息传递 sealed execution context 的流程堵塞，使一次受信启动 transition 同时生成 context、绑定 host spawn acknowledgement 并完成 bridge claim 所需输入。

## User Decisions

- 固定基线为 `2f02f19`；实现前必须解析并记录完整 base SHA。
- automatic attempt 0 和 R1 均已受信 block；不得复用其 task、offer、claim、runtime、candidate、executor 或未提交 patch。
- 当前宿主未暴露 direct `spawn_agent` surface，本任务使用一次性 manual bootstrap execution exception；不得创建或补造 claim、activation、delivery receipt。
- 保留独立验收、fixed-head CI 和 explicit merge；生产、AIO、settings、Secrets、runner、tag/Release 不变。

## Scope

- 在 trusted-main-only bridge 层增加一次性 handoff 对象或等价最小接口：prepare 同时封存 execution context、spawn request、offer/envelope/route/bundle/role/config/CAS 绑定和 claim transition 所需私有状态。
- host adapter 只提交一次真实 direct spawn acknowledgement；handoff 自身完成 claim，不让 Agent 填写 expected head/revision、envelope、nonce、offer、claimId 或机器 JSON。
- context 必须在 envelope 消费前生成；claim 后不得调用 `execution_context(envelope_id)` 或依赖第二条 Agent activation 消息。
- focused contracts 覆盖成功路径、single consume、ack 缺失/重复/task-name mismatch、preclaim race、envelope replay、bundle/policy drift 与 claim CAS drift。
- 保持旧 `TrustedMainRuntimeBridge.prepare/claim/execution_context`、公开 `automatic-*` CLI、candidate claim、wait CLI 的兼容和 fail-closed 行为。

## Non-Goals

- 不修改 Codex 外部运行时、用户级 `~/.codex` 或创建 IPC、daemon、签名、密钥基础设施。
- 不实现 P3 delivery/CI/accept/rework facade，不迁移文档 renderer、project stage 或 P5 低层 CLI 退场。
- 不读取或应用 attempt 0 的未提交 patch。

## Acceptance Criteria

1. 新 handoff 在 claim 前生成并封存完整 execution context，host acknowledgement 后可一次性完成 claim，调用者无需第二条 activation 消息或手填 CAS/JSON。
2. handoff 任一重复、缺失、错 task name、错 bundle/role/config、错 route、错 policy 或错 CAS 都 fail closed，且不产生第二个 claim、orphan receipt 或 fallback。
3. 输出不含 capability、agent/thread 私有身份、conversation、prompt、transcript、credential 或绝对 production path。
4. Python 3.9.6 与 3.14.6 默认 core、runtime-bridge/task-core focused contracts、bundle/project verify、fixed-head CI 与独立 acceptance 通过。
