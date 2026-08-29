# GKD Python 3.9 Compatibility R2 Retrospective

## What Worked

- R2 沿用独立 task/offer/claim/acceptance 边界，未复用 R1 的 runtime 或 lifecycle。
- 先修正 Python 3.9 兼容面，再补 fresh bridge claim-to-deliver 正反合同，最终同时覆盖系统 Python 3.9.6 与开发 Python 3.14.6。
- 内置完整 TOML fallback 保留用户配置语义，并把许可、source manifest、lock 和测试纳入同一候选。

## Problems Found

- 首个 `GKD-PY39-COMPAT` attempt 在 claim 后无终态卸载；R1 完成 437 项验证但 delivery 仍因 `CLAIM_RECEIPT_UNAVAILABLE` 被拒绝。两次失败都按 fail-closed block 保存，未补造 delivery 或 receipt。
- 首轮 Python 3.9 verifier 暴露了基线已有的随机 capability 测试参数转义缺陷（以 `-` 开头的值被 `git grep` 当作选项）；该问题属于测试基础设施，修正后完整重跑通过，未扩大为产品语义变更。

## Follow-Up

- 新的 gate-repair executor 必须在 system Python 3.9 下先完成 status/doctor 和真实 delivery smoke，再提交结果；不能只报告完整 verifier。
- Python 3.9 兼容任务不吸收逻辑时钟、planning refresh 或 delivery sidecar 变化；这些仍由独立 R6 负责。
