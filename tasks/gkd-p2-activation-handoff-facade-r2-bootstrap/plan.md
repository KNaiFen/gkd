# P2 激活交接流程修复 R2 Bootstrap 实施计划

## Goal

把 activation context 从“claim 后再请求的消息”改为 trusted main 在 spawn 前生成并封存、由同一 handoff transition 消费的事实。

## Design

- 复用现有 `TrustedMainRuntimeBridge.prepare`、`execution_context`、`claim`、`validate_spawn_result`、activation authority 和 task service，不复制 task state schema。
- 新高层入口在 prepare 返回后、envelope 仍可读时立即取得 execution context，并固定 offer 后 head/revision。
- 返回只读、single-consume 的 trusted-main handoff；host 读取 spawn request 和 sealed context，随后只把一次真实 acknowledgement 交回该对象。
- handoff 内部持有 expected CAS、envelope 和 activation nonce，claim attempt 开始即消费；无论成功或 fail-closed，均禁止重放同一对象。
- 保留旧低层方法作为兼容和诊断面，不修改公开 candidate 权限。

## Verification

- 新 focused tests 直接证明 claim 前 context、一次 acknowledgement 成功、claim 后不重读 envelope、single consume 和全部 drift/mismatch 负例。
- 更新 manifest/lock、project inventory、README/Skill 仅限实际接口变化需要的最小范围。
- 使用 `scripts/gkd-verify --base-sha <full-base-sha>` 分别在 Python 3.9.6 与 3.14.6 运行；生成 canonical result/evidence，创建或更新 PR，等待 fixed-head CI。

## Bootstrap Exception

本任务由独立人工顶层 execution session 在专用 worktree 实现并停在 fixed-head PR；没有 offer/claim/activation/delivery state。executor 不验收、不合并、不清理。该例外在本任务合并后终止。

## External Side Effects

只允许任务 branch/worktree、commit、push、PR、fixed-head CI、verifier/evidence 和验收合并；禁止 production/AIO/settings/Secrets/runner/tag/Release。
