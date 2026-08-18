# Open Items

- [x] `gkd_core_implementation` 已于2026-08-18明确授权；按hybrid B从里程碑-1人工执行交接开始。
- [x] 已创建 `KNaiFen/gkd` 与 `KNaiFen/gkd-sandbox`；源码基线已推送，sandbox保持空仓库。
- [x] `GKD-M-1A` 在 `codex-cli 0.147.0` 输出版本绑定的 `native_insufficient`；fixed head `bd8332a` 已独立验收并通过PR #1合并为 `0cc09e9`。
- [x] `GKD-M-1B` PR #2 新固定head `98df6ba122d9fe8aed230094ed806010e7002aa7` 已通过独立验收并squash merge为 `1d303456f2afcaa4e5fd0353232e30c5c6b63a33`；结论仅为 `core_ready_for_live_gate`。
- [x] `GKD-M-1C` fixed head `4332cea7aecc7540640add626ddca6b9b3d8cbad` 的 `unsupported` 已通过独立验收并由PR #3 squash merge为 `afacf490aee948a0e70910304976da6c667375fa`；auto route保持禁用，manual-only继续生效。
- [x] `GKD-M0-A` 已由implementation/evidence commit `f2cf2b7ab2706c41a3e80dfaf191e8fdac7a28cd` 产出 `canonical_foundation_ready` 并交付PR #4；生产受保护表面前后不变，未修改AIO。
- [ ] main对PR #4新固定head执行独立验收；验收前不得合并、开始M0-B或里程碑1。
- [ ] GKD release candidate通过后，另行取得生产 `~/.codex` 安装授权。
- [ ] 生产bundle可用后，另行批准AIO接入与旧实现迁移；不得由GKD本体授权推断。
