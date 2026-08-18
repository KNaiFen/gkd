# Open Items

- [x] `gkd_core_implementation` 已于2026-08-18明确授权；按hybrid B从里程碑-1人工执行交接开始。
- [x] 已创建 `KNaiFen/gkd` 与 `KNaiFen/gkd-sandbox`；源码基线已推送，sandbox保持空仓库。
- [x] `GKD-M-1A` 在 `codex-cli 0.147.0` 输出版本绑定的 `native_insufficient`；fixed head `bd8332a` 已独立验收并通过PR #1合并为 `0cc09e9`。
- [x] `GKD-M-1B` PR #2 新固定head `98df6ba122d9fe8aed230094ed806010e7002aa7` 已通过独立验收并squash merge为 `1d303456f2afcaa4e5fd0353232e30c5c6b63a33`；结论仅为 `core_ready_for_live_gate`。
- [x] `GKD-M-1C` fixed head `4332cea7aecc7540640add626ddca6b9b3d8cbad` 的 `unsupported` 已通过独立验收并由PR #3 squash merge为 `afacf490aee948a0e70910304976da6c667375fa`；auto route保持禁用，manual-only继续生效。
- [ ] 执行 `GKD-M0-A`：在指定worktree按 `tasks/m0-canonical-foundation/execution.md` 建立development bundle基础、单一权威VISION和文档分层并交付PR #4；不得修改生产 `~/.codex` 或AIO。
- [ ] GKD release candidate通过后，另行取得生产 `~/.codex` 安装授权。
- [ ] 生产bundle可用后，另行批准AIO接入与旧实现迁移；不得由GKD本体授权推断。
