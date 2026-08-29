# GKD Gate Repair R3 Plan

## Goal

以既有 revision、planning refresh 和由实际验证产物驱动的 delivery sidecar，完成可自举的 GKD 门禁修复。

## User Decisions

- 基线为 trusted main `b1adc67`；R3 accepted merge 前 O4 保持暂停。
- 一个精确 executor、一个独立 acceptor、trusted main 合并；不复用旧 attempt。
- 生产、AIO、GitHub settings/Secrets、runner、tag/Release 与已发布 bundle 继续隔离。

## Behavior And Defaults

- history revision 是唯一逻辑顺序；UTC 仍记录审计时间而不参与顺序判断。
- planning-refresh 是显式 planning-only 的单 writer/CAS 事务。
- 自动 delivery 将 result-manifest sidecar 放入 final implementation commit，并从真实 canonical results/evidence 文件验证全部 digest。delivery document commit 只新增 delivery.md，紧随该 implementation commit。
- task-state shape 保持旧 validator 可读；新行为由新服务在 merge 后为未来任务提供。

## Scope

- 更新 gkd_task model/documents/service/CLI/acceptance 与独立 result-manifest schema。
- 将真实 results/evidence 解析接入 delivery 与复核合同，更新 packaging expected-set、bundle lock 和使用说明。

## Non-Goals

- 不改变默认 verifier scope、watcher/probe、GitHub adapter、role route 或 release policy。
- 不让手动 route 隐式获得 automatic bundle/result 语义。

## Acceptance Criteria

- revision 顺序、planning refresh、真实 results/evidence digest 验证、sidecar ancestor 和 post-delivery drift 均有稳定正反合同。
- R3 fixed state 通过 old trusted status/doctor/rework 前置，完整 verifier、bundle verify、fixed-head CI 和独立 acceptance 在同一 head 成功。

## Compatibility

- 保留 UTC、revision/CAS、phase matrix、delivery document、implementationHead 和 candidateOutputBundleDigest 字段。
- 旧 state 只读不迁移；R3 本身不使用新的 refresh transition 或新 state fields。

## Security And Data

- results/evidence 只经 canonical regular-file 解析，sidecar只保存 digest、SHA 和 task identity；不保存路径、prompt、transcript 或凭据。
- 失败快速返回，不写半状态；不接受未绑定或不可复现的 digest。

## Migration

- accepted merge 后，O4 从该 merge SHA 新建任务；所有旧 rejected attempts 继续归档。

## Public Interfaces

- `gkd-task planning-refresh` 和 automatic delivery 的 results/evidence/sidecar 参数提供稳定帮助文本；acceptance/rework 在新 bundle 中验证同一固定绑定。

## Execution Route

- trusted main 负责 plan/authorization/offer/claim；executor 先完成全部实现、bundle、真实 verifier/evidence、sidecar，再提交唯一 delivery document 并 deliver。
- acceptor 使用 exact full head 和相对 `.gkd/policy.json` 运行 CI，所有门禁通过后才 narrow accept。

## External Side Effects

- 允许隔离 worktree/branch/PR、runtime/evidence 和只读 CI；禁止生产、AIO、settings、Secrets、runner、tag/Release 写入。

## Action Mode

`implement_and_merge_on_acceptance`

## Implementation Notes

- 先复核 R2 的 old acceptance ancestry 和 unbound digest finding，再实现最小兼容改动。
- 最终 implementation commit 必须含 source、schema、tests、bundle/lock、sidecar；其直接下一提交只能是 delivery.md，之后立即 deliver 并停止。
