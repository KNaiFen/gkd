# 验收与收尾：GKD-M2-A 角色与路由核心

## 最终结果

- 结果：完成
- 功能 PR：[KNaiFen/gkd#6](https://github.com/KNaiFen/gkd/pull/6)
- 被验收 head：`b579926aaff50d40b462e7f21cf91c9709eeb3a3`
- 必需 CI：无 configured checks；事实为 `required_checks_not_configured_bootstrap`，不视为 CI 成功
- merge commit：`9351d628d198ec8638311901cf288abadc643a42`
- 日期：2026-08-20

## 验收结论

- AC：M2-A 70/70；M1 task-core 104/104；foundation 53/53；watcher core 47/47；watcher live-negative 15/15。两次 M2 evidence、`m2-contracts.json` 与 `contract-results.json` 均逐字节一致，候选树与 squash merge tree 一致。
- F-001 至 F-005：全部整改并独立复核通过。F-004 的 host 事实绑定唯一 exact `gkd_executor` spawn、实际 child identity、child/parent terminal 与 exit code；F-005 的 trusted-main activation → exact claim → delivery 正向桥接与候选 fail-closed 路径均符合交付合同。
- 接受的偏移或风险：M2-A 仍只输出 `manual_only`。真实 `wait_agent(timeout_ms=3600000)` 和 child early-final 属于 M2-B，未在本任务中运行；无 configured checks 不被描述为成功；同一 OS 用户主动篡改不属于本任务威胁模型。
- 历史整改：首轮 F-001 至 F-004 和后续 F-005 轮次保留在 `findings.md`；早期隔离模式、strict-config、parent model override、wait-only stdout 等只作为历史诊断，不影响最终 host rollout 归一化结论。
- 结论证据：`delivery.md`、`findings.md`、`evidence/m2-role-routing-core/role-handshake.json`、`evidence/m2-role-routing-core/m2-contracts.json` 及固定 head 的实时 GitHub PR 状态。

## 长期记录

- 知识库与现行合同：`.agents/context.md`、`.agents/decisions.md`、`.agents/open-items.md` 已回填 M2-A 合并事实、子代理实现偏移和后续门禁。
- PENDING：保留 M2-B 一小时 fresh-runtime 门；在该门通过前不得启用 automatic route。
- 遗留风险：当前运行时工具层若实际只接受 `360000ms`，M2-B 必须 fail-closed，不能用更短循环冒充一小时；M2-B 还必须把固定 bundle digest 作为可验证证据输入。

## 归档与清理

- 归档路径：任务资料保留在 `tasks/m2-role-routing-core/`，本仓库没有 Trellis `task.py` 归档入口，未伪造 archive 状态。
- `archive --no-commit`：未运行；本仓库无对应脚本。
- `validate --all`：未运行；本仓库无对应脚本。
- records-only PR：不适用；本记录随 main 收尾提交。
- worktree：`/Users/knaifen/Documents/Codex/gkd-worktrees/m2-role-routing-core` 已确认 clean、与 merge tree 一致，随后删除。
- 本地/远端分支：`task/m2-role-routing-core` 已删除；远端同名分支已删除；本地远端跟踪引用已 prune。仅保留 `main`。
