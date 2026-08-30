# GKD O4 Lane Manifest Compatibility R3 Requirements

## Goal

让 fixed-tree result consumer、delivery、acceptance 和 rework 能严格识别 manifest 的显式 lane/profile 与完整 scope 集合，为后续 O4 historical lane 隔离建立可由当前 trusted acceptance 升级的兼容基础。本任务自身继续产出当前旧完整 default scope 集合。

## User Decisions

- 基线为 trusted main `5708aaf990564b07c258bdc34682249df1b5b5f6`，execution bundle 为 `65354c4a94abad709be30e8c154cb671c75631b1bc3dc13a5fddfa1d634fdaa3`。
- O4、compatibility attempt 0/R1/R2 是只读历史；本任务新建 task、offer、claim、runtime、branch、worktree 和 PR，不复用任何 lifecycle 或 artifacts。R2 的 `executor_preclaim_race` 只通过主编排的预建 acknowledgement 与 spawn 后直接 bridge claim 处理，不放宽 task 状态机。
- 一个精确 executor、一个 independent acceptor，trusted main 合并清理；executor 必须使用 bridge 的 trusted-main-only execution context argv；不修改生产/AIO/settings/Secrets/runner/tag/Release。

## Scope

- 为 canonical result manifest 增加严格、版本化的 lane/profile 语义，以及明确 default/historical scope profile 的 consumer validation。
- delivery artifact validation、acceptance 与 rework 从 final implementation tree 使用同一 manifest validator。
- 对 unknown lane/profile、lane-scope mismatch、scope/test ID 缺失/未知/重复、base/head/verifier/result/evidence digest drift 加入正反合同，保持无半状态 fail-closed。
- 本任务不得从 default `gkd-verify` 移除 watcher scope、不得新增 historical runner、不得改变默认 scope 产物；只用 fixtures/synthetic manifests 覆盖 future profiles。
- 更新 schema、README、manifest/lock 和相关测试。

## Non-Goals

- 不实施 O4 watcher/probe 隔离，不重写 watcher/probe，不删除历史 evidence，不修改 R6/Python 3.9 契约，不进入 O5-O8。

## Acceptance Criteria

1. 当前 default verifier 的实际 scope 集合与 result artifacts 保持旧语义，当前 accepted bundle 可对本任务 delivery 执行 trusted acceptance。
2. consumer 对已知 default/historical manifest profile 都严格可验证；对 unknown/mismatch/missing/duplicate/tamper/drift 都拒绝且不写状态。
3. Python 3.9.6 与 Python 3.14.6 完整 verifier、bundle、fresh delivery、fixed-head CI 和 independent acceptance 都通过。
4. 不引入绝对路径、凭据、新依赖或未授权外部副作用。
