# GKD 工作流精简优化总计划

**制定日期：** 2026-08-28
**依据：** [GKD 工作流精简审查报告](gkd-workflow-simplification-review-2026-08-28.md)
**执行方式：** 每个任务独立固定基线，由 `gkd_executor` 交付，由独立 `gkd_acceptor` 验收；失败尝试保留终态，不沿旧 head 洗绿。
**当前基线：** `efa2d378fe4736663e192058cc0a0b33ebf896eb`

## 目标与不变项

目标是在不削弱用户控制、可恢复长任务、固定 head 证据、可移植性、资源保护和发布自验证的前提下，收窄默认上下文、安装面和验证成本。

以下能力在整个优化期间保持为核心，不得作为“精简”删除：

- `gkd_task` planning/authorization、offer/claim、CAS/journal、delivery/rework/acceptance；
- `gkd_role` route/wait/bridge、精确 executor/acceptor、project staging 与 bundle digest 绑定；
- fixed-head `gkd-ci-monitor`、完整历史 checkout、`.gkd/policy.json` 绑定和 exact PR/head 检查；
- production migration/recovery/doctor、legacy schema read/reject 入口；
- finalization/release self-verification、manifest/lock/schemas/evidence；
- `sitecustomize.py` 与 `usercustomize.py` 两个不同启动阶段的边界。

不在本计划授权范围内：生产 `~/.codex` 写入、AIO 普通产品改动、GitHub settings/Secrets/付费 runner、tag/Release、计划外仓库或绝对路径。

## 目标形态

默认 core bundle 只承载以下闭环：

```text
foundation
  -> task state + authorization + offer/claim + delivery/rework
  -> role routing + trusted bridge + one-hour wait
  -> fixed-head CI monitor + independent acceptor
  -> finalization/release self-verification
```

默认 Skills 收窄为：`gkd-main`、`gkd-execute`、`gkd-local-verify`、`gkd-ci-monitor`、`gkd-accept`。

按需能力保留但移出默认上下文：

| Pack | 内容 | 使用时机 |
|---|---|---|
| CI advice | resource class/preset、scanner、recommendations、`gkd-optimize-ci`、`gkd_ci_reviewer` | 资源受限或需要 runner/成本建议时 |
| Review | review core、adapter、remediation、跨仓库 fixture、`gkd-review-remediation` | 明确发起 review/remediation 时 |
| Compatibility | legacy migration、旧 schema 矩阵、生产迁移辅助 | 版本升级或恢复时 |
| Historical verification | watcher/probes、live-negative、历史 evidence/fixture | 发布候选或平台能力变更时 |

## 分阶段执行清单

每项完成定义为：候选 fixed head 交付、独立验收通过并按仓库规则合并；若验收拒绝，则创建新 revision/epoch，保留旧失败事实。

### O1：无调用代码与测试表达清理

- **范围：** 移除确认无调用的 5 个 helper（或将仅测试需要的 helper 移到 tests）；参数化 foundation mode drift 测试，不改变边界断言。
- **不做：** 不删 task/role/release API，不改 manifest 语义，不碰 watcher 行为。
- **验收：** core verifier、相关 mutation、两次字节一致 evidence、candidate bundle digest；确认无外部 Python 调用者。
- **依赖：** 无。完成后再进入 O2。

### O2：持久上下文去重与状态校正

- **范围：** 清理 `.agents/context.md` 的过期/矛盾状态和重复 AIO C 条目；把当前事实、下一任务、历史决策分层。
- **不做：** 不复制 host-level 子代理回收 hook，不修改 GKD bundle 或生产安装。
- **验收：** 文档链接、日期、当前发布 pin、未授权边界和 open item 一致；不产生代码行为变化。
- **依赖：** O1 完成后执行。

### O3：验证结果复用

- **范围：** 建立单一 canonical scope runner；`gkd-verify` 产生固定 scope/test ID/result/environment 摘要，evidence runner 消费结果并只补充边界快照。
- **保留：** protected surface、temporary/output、digest 和 evidence 写入校验。
- **验收：** core scopes 结果与现有行为一致；重复执行只作为显式 evidence lane；双运行结果字节一致。
- **依赖：** O1、O2。

### P0：Python 3.9 executor runtime baseline

- **范围：** 系统移除 shipped/reachable Python 3.10/3.11 API 依赖；建立带上游许可的 payload 内置 TOML compatibility facade；以实际 system Python 3.9 完整运行 verifier、bundle、core CLI 与适用 historical lane。
- **不做：** 不把解释器绝对路径、pip dependency 或外部 runtime 固化为产品条件；不改 logic clock、planning refresh、delivery sidecar、state schema 或 O4 行为。
- **验收：** Python 3.9 与开发解释器均通过完整 verifier/bundle；严格配对、TOML parity/invalid input、watcher/probe import 和 CLI 分类有正反合同；manifest/lock/许可/最低版本文档一致。
- **依赖：** O3。完成后才可建立独立 GKD-GATE-REPAIR-R6。

### O4：watcher/probe 历史 lane 隔离

- **范围：** 从默认 `gkd-verify` 移出 `src/gkd_watchdog`、`scripts/gkd-watchdog-mcp`、`probes/app-server-watcher` 及其 47 项默认合同，新增显式 `historical-watcher`/`host-capability` lane。
- **保留：** 历史 evidence、M-1C `unsupported` 事实、watcher 行为测试；当前 role/wait/bridge 合同继续在 core。
- **验收：** 默认 verifier 不导入 watcher/probe；显式 lane 可独立运行且证据可追溯；发布/平台变更仍能调用该 lane。
- **依赖：** O3、P0 与独立 GKD-GATE-REPAIR-R6 accepted merge。

### O5：runtime fixture 与测试输入拆分

- **范围：** 将 4 个仅测试/演练 fixture 移出 production/core runtime 安装面，保留 schema 和 release traceability；更新 source、manifest、lock、fixture digest 与测试入口。
- **验收：** core 安装无 fixture；release-verification/test bundle 可复现读取 fixture；manifest/lock/traceability 自洽，旧发布资产不被修改。
- **依赖：** O3、O4。

### O6：默认角色与 optional pack 拆分

- **范围：** 默认 executor 只注入 `gkd-execute`、`gkd-local-verify`、必要时的 `gkd-ci-monitor`；将 `gkd-optimize-ci`、`gkd-review-remediation`、resource/scanner/review adapter 分到按需 pack，保留 CLI 和迁移禁用重复 Skill 的机制。
- **验收：** 新 bundle 的 role/context/manifest/lock digest 一致；核心 executor/acceptor route 不受影响；按需 pack 可显式 stage 并通过自身 verifier。
- **依赖：** O5。

### O7：contract 索引与重复断言收敛

- **范围：** delivery contract 消费 task-core 结果，只保留 document/head/environment 特有检查；watchdog 采用唯一 test ID 到多个 contract ID 的反向索引；foundation mode 测试保持边界但合并实现。
- **验收：** contract 覆盖率不下降，重复行为只执行一次；证据仍能按 contract 查询；失败定位包含 test ID、scope 和固定 head。
- **依赖：** O3、O4、O6。

### O8：兼容矩阵降频与发布边界评估

- **范围：** 每种公开旧格式在 core 保留一个 read 与一个 reject/restore 正例，完整历史矩阵移到 release-upgrade lane；评估 `gkd-finalize`/`gkd-release` 合并为共享 engine、保留兼容 CLI alias 的可行性。
- **不做：** 在明确 major-version 放弃承诺前，不删除 legacy read/reject/migrate，也不直接删除任一 release 模块。
- **验收：** 版本升级 lane 可复现；核心 PR 时间下降且兼容承诺有明确证据；若合并 engine，先单独形成 ADR 和迁移任务。
- **依赖：** O6、O7。

## 执行门禁与停止条件

1. 每项任务从当前 trusted main 的完整 SHA 建立 requirements/plan/execution，并通过 `gkd-task` 状态机完成 bootstrap、requirements-ready、plan-approve、authorize、offer、claim。
2. 自动执行只使用一个精确 `gkd_executor`；executor 只交付，不验收、不合并、不清理。主会话在固定等待门禁下等待终态。
3. 交付后由独立 `gkd_acceptor` 在干净同步 checkout 使用显式 full head 验收；CI 只监控该固定 head。
4. 任何 `rejected`、`blocked`、`error`、head drift、CAS/digest mismatch 都写入 task/evidence，停止当前 attempt；不得在同一 attempt 重试或补造成功 receipt。
5. 每项合并后同步 `.agents/context.md`、`.agents/decisions.md`、`.agents/open-items.md`，再以新主线 SHA 启动下一项。

## 总体成功标准

- 核心 task/role/wait/fixed-head/acceptance/release 行为与当前已发布承诺保持一致；
- 默认安装与默认 verifier 不再包含可选 CI 建议、review/remediation、历史 watcher/probe 和测试 fixture；
- 重复行为断言合并为一次执行，证据仍可按 scope/test ID/contract ID 追溯；
- 每项变更均有独立 candidate bundle、完整 SHA、可复核 verifier/CI/acceptance 证据；
- 生产 `~/.codex`、AIO、settings、Secrets、付费 runner 和既有 release 资产无计划外变化。

## 当前启动项

O1-O3 与 P0 已完成。P0 的首个 attempt 与 R1 均按 fail-closed block 保存；R2 已通过独立验收并 merge `360ba876c83bed4c2b4fcea98a172eefe94838a5`，Python 3.9.6/3.14.6 双解释器 439 项验证和真实 claim-to-deliver 均闭合。GKD-GATE-REPAIR-R6 已通过独立验收并 merge `f248962d9c223ba6c73c07e23a873fddb5fad1b0`，逻辑顺序、planning refresh 与 delivery result-manifest 绑定门禁均已落地。`GKD-O4-WATCHER-HISTORICAL-LANE-R2` 的分层实现、双解释器 verifier 与 fixed-head CI 均通过，但旧 result consumer 将 watcher scope 误作默认强制集合，导致 acceptance/rework 以 `INVALID_VERIFIER_RESULTS` / `CANDIDATE_INVALID` 拒绝且无法写入 rework。当前启动项为全新 `GKD-O4-WATCHER-HISTORICAL-LANE-R3`：只补足 lane-aware result consumer/acceptance，不得复用 R2 lifecycle 或扩大到 O5。
