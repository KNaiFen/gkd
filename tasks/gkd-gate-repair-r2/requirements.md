# GKD Gate Repair R2 Requirements

## Goal

修复跨进程任务的 wall-clock 逆序、planning 文档 digest 刷新死锁和 delivery result manifest 绑定不足，同时保持本次 self-hosting 任务可由合并前的 trusted-main validator 读取和验收。R2 必须让 O4 能在 accepted merge 后从全新任务恢复。

## User Decisions

- 本任务从 trusted main `62ea7d9` 建立；O4/O4-R1、GKD-GATE-REPAIR attempt 0 和 R1 的拒绝记录均只读保留，不得手改或复活。
- 只允许一个精确 `gkd_executor`、一个独立 `gkd_acceptor` 和 trusted main 合并/收尾；不使用 nested agent、fallback 或同 attempt 重试。
- 只改 GKD canonical 源码、独立 schema/合同测试和本任务记录；不改生产 `~/.codex`、AIO、GitHub settings/Secrets、付费 runner、tag/Release 或已发布资产。

## Scope

- 以现有 `history.revision` 的连续、不可篡改序列作为生命周期逻辑顺序，取消对 wall-clock 文本排序的正确性依赖。保留所有 UTC 审计字段，但不得给 event 或 task state 添加 logical clock 字段。
- 增加 canonical `planning` 文档刷新 transition：它以 CAS 一次性重算 requirements、plan、implementation 和 plan material digest，只在 planning 允许；进入 awaiting_claim、implementing 或更后阶段后，任何文档漂移仍 fail-closed。R2 自身不得调用该新 transition，以保持旧 validator 可读。
- 对自动路线 delivery 增加固定预提交 `tasks/<task>/result-manifest.json` sidecar。新 `deliver` 和新 acceptance/rework 从既有 task path、delivery implementation head 和 candidate output bundle digest 派生并校验 sidecar，不向 `lifecycle.delivery` 添加字段。sidecar 必须是 canonical regular JSON，绑定任务、仓库、base SHA、implementation head、candidate output bundle digest、canonical verifier result/evidence digest。
- 同步 delivery CLI、服务、acceptance/rework、独立 result-manifest schema、packaging expected-set、bundle manifest/lock、README/操作契约和最小合同测试；R2 的 task-state schema 与 R2 delivery record 保持旧 validator 已支持的形状。

## Non-Goals

- 不实现 O4 watcher historical lane、O5 runtime fixture、O6 optional pack、O7 contract index 或 O8 文档整理。
- 不重写 GitHub adapter、自动路由、watcher、结果 scope 或发布流程；不通过放宽检查、吞掉错误、猜测缺失事实或删除负向测试达成通过。
- 不新增生产迁移、外部依赖或 GitHub 配置。

## Acceptance Criteria

1. 合同测试证明 history revision 连续时，等时或回拨的 UTC event 时间不再使新 validator 拒绝；revision/head/record tamper 仍拒绝。R2 本身的 state 不含新 event key 或新 delivery key，合并前 trusted main `status/doctor/rework` 可读取。
2. planning 阶段的 canonical refresh 能同步三份文档 digest 和 material digest；planning 外的 drift 仍在状态写入前失败，且 refresh 不留下部分状态。
3. 自动 delivery 缺少 sidecar、sidecar 非 canonical、路径、任务、base、implementation head、bundle、result/evidence digest 任一漂移均拒绝且不推进 revision；成功交付只保存现有 delivery record 字段，新 acceptance/rework 能从 fixed implementation head 重新验证 sidecar。
4. R2 的所有实现、schema、packaging expected-set、bundle manifest/lock、candidate output 和 sidecar 在 delivery document 前完成；delivery coordination commit 是 candidate 最后一个提交，fixed head、bundle digest、sidecar 和 delivery state 一致。
5. task-core、runtime bridge、rework、结果消费者、packaging 和 mutation/negative 合同通过；独立 acceptor 使用仓库相对 `.gkd/policy.json` 获得 exact-head CI 终态。
6. 不引入绝对路径、用户名、凭据、新依赖或生产/AIO/GitHub settings 副作用。

