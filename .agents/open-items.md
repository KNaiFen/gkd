# Open Items

- [x] `gkd_core_implementation` 已于2026-08-18明确授权；按hybrid B从里程碑-1人工执行交接开始。
- [x] 已创建 `KNaiFen/gkd` 与 `KNaiFen/gkd-sandbox`；源码基线已推送，sandbox保持空仓库。
- [x] `GKD-M-1A` 在 `codex-cli 0.147.0` 输出版本绑定的 `native_insufficient`；fixed head `bd8332a` 已独立验收并通过PR #1合并为 `0cc09e9`。
- [x] `GKD-M-1B` 已实现版本绑定 core、MCP 长阻塞 adapter 与真实 subprocess fake app-server 合同测试；implementation/evidence head 为 `b441562f02c069bbcca7aaff25c6d79eaf1fae63`，结论仅为 `core_ready_for_live_gate`。
- [ ] 建立独立 `GKD-M-1C` fresh-session live gate，验证真实 Codex/MCP 接线、正常 final 去重、异常 steer、父上下文 trace 与长连接行为；通过前保持 manual-only，禁止 D1 回退。
- [ ] GKD release candidate通过后，另行取得生产 `~/.codex` 安装授权。
- [ ] 生产bundle可用后，另行批准AIO接入与旧实现迁移；不得由GKD本体授权推断。
