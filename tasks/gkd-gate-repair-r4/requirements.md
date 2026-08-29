# GKD Gate Repair R4 Requirements

## Goal

以无自引用、self-hosting-compatible 的 result manifest sidecar 完成 GKD 逻辑时间、planning digest refresh 和 automatic delivery 绑定门禁修复，并解除 O4 重启前置阻塞。

## User Decisions

- 本任务从 trusted main `6f74ce9` 建立；旧 O4、attempt 0、R1、R2、R3 均为只读历史，不复用其协调记录。
- 一个精确 `gkd_executor`、一个独立 `gkd_acceptor`、trusted main 合并/收尾；不使用 nested agent、fallback 或旧 attempt 重试。
- 范围仅限 GKD canonical、合同测试和任务记录；生产、AIO、GitHub settings/Secrets、付费 runner、tag/Release、已发布资产不变。

## Scope

- 以现有 history revision 作为逻辑顺序，不再用 UTC 文本排序拒绝 task state；不添加 task history/delivery key。
- 提供 planning-only、CAS 事务化的 planning-refresh，刷新三份规划文档 digest 与 material digest；R4 自身不得调用该 transition。
- automatic delivery 要求 `tasks/<task>/result-manifest.json` 位于 state 既有 `implementationHead` 的 fixed tree，并且是该 implementation commit 的改动之一；该 commit 必须是 delivery.md commit 的直接父提交。sidecar 不得包含或声明 implementation SHA。
- sidecar 只绑定任务、仓库、task branch/path、base SHA、candidate output bundle、canonical verifier result digest 与 evidence digest。`deliver` 读取实际 canonical results/evidence regular files，以结构化解析器重算上述 digest/事实并校验 sidecar；新 acceptance/rework 从 state implementation head 定位 sidecar并复核该链。
- 同步 service/CLI/model/acceptance/schema、packaging expected set、bundle/lock、使用说明和正反合同。R4 自身 task state 保持当前 trusted-main validator 可读。

## Non-Goals

- 不实现 O4-O8，不改变 watcher、CI adapter、route、release 或手动 delivery 语义。
- 不通过让 sidecar 自报 commit SHA、放宽旧 acceptance ancestry、接受自声明 digest 或虚构 evidence 来通过。
- 不新增依赖、生产迁移或外部设置。

## Acceptance Criteria

1. event UTC 等时/回拨由 revision 顺序验证；revision/head/record tamper 拒绝，R4 candidate state 可由 current trusted main status/doctor/rework 读取。
2. planning-refresh 仅 planning 可用并原子刷新所有 digest；其他 phase 的文档漂移/refresh 尝试 fail-closed。
3. automatic deliver 对 missing/noncanonical results/evidence/sidecar、任务/base/bundle/result/evidence drift、sidecar不在implementation tree、sidecar不属于implementation commit改动均拒绝且不写 revision。
4. final implementation commit 包含代码、schema、tests、lock、results/evidence 绑定 sidecar；其直接下一提交只增加 delivery.md，state implementationHead 精确等于该父提交，delivery 后没有候选提交。
5. task-core、runtime bridge、rework、packaging/mutation/negative contracts、完整 verifier、bundle verify、相对 policy 的 exact-head CI 与独立 acceptance 都在同一 fixed head 通过。
6. 不引入绝对路径、凭据、新依赖或生产/AIO/GitHub settings 副作用。
