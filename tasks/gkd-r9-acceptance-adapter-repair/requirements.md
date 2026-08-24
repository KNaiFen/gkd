# GKD Acceptance Adapter Delivery Repair

## Goal

交付可安装 GitHub acceptance adapter，并提供不会误用 delivery CAS 的 executor 合同。

## User Decisions

- 用户授权修复流程并继续 AIO adoption。
- R7/R8 均已由 task core block，未创建 PR merge 或 receipt；R9 从 clean main 独立实现。

## Scope

- 新增 GitHub-only canonical acceptance adapter、fake-gh contracts、gkd-execute delivery sequence 指引/测试、manifest 与 gkd-accept 文档。

## Non-Goals

- 不修改 AIO、production、workflow/settings、tag/Release、task lifecycle、route/claim/bridge 或历史 receipt。

## Acceptance Criteria

- [ ] adapter 正确映射 REST merged、canonical newline、exact-head squash merge 与 exit-75 reconciliation。
- [ ] fake-gh 测试覆盖 snapshot/merge、无 credential/stderr、head drift和不确定 merge。
- [ ] executor 在 delivery document commit 后以其 full head 调用 `gkd-task deliver`，由 CLI 创建最终 state。
- [ ] full verifier、diff check 与 fixed-head `GKD Verify` 通过。
