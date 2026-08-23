# GKD Acceptance Adapter And Delivery Repair

## Goal

交付可安装 GitHub acceptance adapter，并修正 executor 的 delivery CAS 指引，确保唯一 executor 能把 implementation、delivery document 与 final task state 按既有 sequencing contract 完成。

## User Decisions

- 用户授权修复 GKD 流程并继续 AIO adoption。
- R7 因 executor 将 implementation head 用作 deliver CAS 值而在无 PR/CI/merge 的情况下被 task core block；不得重用其 claim、代码或 receipt。
- 使用已发布 `v0.1.4` bundle；真实 merge 只能由 `gkd-task accept --merge` 触发。

## Scope

- 提供可安装、GitHub-only、canonical JSON GitHub acceptance adapter，正确归一化 REST merged PR 状态并支持 existing exit-75 reconciliation。
- 用 fake `gh` 测试 snapshot、canonical newline、exact-head squash merge、merged REST state 与不确定 merge。
- 修订 `gkd-execute` 指引和测试，使 delivery document commit 成为 `gkd-task deliver --expected-head`，且 final state 由 CLI 生成。
- 更新 manifest 和最小 trusted-main acceptance 文档。

## Non-Goals

- 不修改 task lifecycle、route/claim/bridge 实现，不补造 R6/B2/R7 receipt，不修改 AIO、production、workflow/settings、tag 或 Release。

## Acceptance Criteria

- [ ] installed adapter 的 snapshot/merge I/O 满足 task core response contract，REST `merged: true` 映射为 `state: merged`。
- [ ] fake-gh 测试覆盖 exact expected head、squash/match-head command、canonical newline、merge indeterminate 及无 credential/stderr 回显。
- [ ] executor 指引明确并测试 implementation commit、delivery document commit、deliver final state 的三步固定顺序。
- [ ] 完整 verifier、diff check 和 fixed-head `GKD Verify` 通过；本任务的 executor 形成 canonical delivery 而不由 main 代写。

