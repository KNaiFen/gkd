# Open Items

- [x] `gkd_core_implementation` 已于2026-08-18明确授权；按hybrid B从里程碑-1人工执行交接开始。
- [x] 已创建 `KNaiFen/gkd` 与 `KNaiFen/gkd-sandbox`；源码基线已推送，sandbox保持空仓库。
- [x] `GKD-M-1A` 在 `codex-cli 0.147.0` 输出版本绑定的 `native_insufficient`；fixed head `bd8332a` 已独立验收并通过PR #1合并为 `0cc09e9`。
- [x] `GKD-M-1B` PR #2 新固定head `98df6ba122d9fe8aed230094ed806010e7002aa7` 已通过独立验收并squash merge为 `1d303456f2afcaa4e5fd0353232e30c5c6b63a33`；结论仅为 `core_ready_for_live_gate`。
- [ ] 执行 `GKD-M-1C`：在指定worktree按 `tasks/m-1-external-watcher-live-gate/execution.md` 完成真实 Codex/app-server/MCP live gate 并交付PR #3；输出必须为 `external_watcher_supported` 或 `unsupported`，证据不足保持manual-only。
- [ ] GKD release candidate通过后，另行取得生产 `~/.codex` 安装授权。
- [ ] 生产bundle可用后，另行批准AIO接入与旧实现迁移；不得由GKD本体授权推断。
