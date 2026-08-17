# Open Items

- [x] `gkd_core_implementation` 已于2026-08-18明确授权；按hybrid B从里程碑-1人工执行交接开始。
- [x] 已创建 `KNaiFen/gkd` 与 `KNaiFen/gkd-sandbox`；源码基线已推送，sandbox保持空仓库。
- [x] `GKD-M-1A` 在 `codex-cli 0.147.0` 输出版本绑定的 `native_insufficient`；fixed head `bd8332a` 已独立验收并通过PR #1合并为 `0cc09e9`。
- [ ] 建立 `GKD-M-1B` 外部app-server watcher人工执行任务，先实现版本绑定core、MCP长阻塞adapter与fake app-server合同测试；真实fresh-session集成另设完成门。
- [ ] D2实施先验证multiagentv2原生12小时等待；不足时实现外部app-server watcher；两者失败保持manual-only，禁止D1回退。
- [ ] GKD release candidate通过后，另行取得生产 `~/.codex` 安装授权。
- [ ] 生产bundle可用后，另行批准AIO接入与旧实现迁移；不得由GKD本体授权推断。
