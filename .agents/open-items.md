# Open Items

- [x] `gkd_core_implementation` 已于2026-08-18明确授权；按hybrid B从里程碑-1人工执行交接开始。
- [x] 已创建 `KNaiFen/gkd` 与 `KNaiFen/gkd-sandbox`；源码基线已推送，sandbox保持空仓库。
- [x] 已建立并执行里程碑-1原生D2探测任务；`GKD-M-1A` 在 `codex-cli 0.147.0` 输出版本绑定的 `native_insufficient`，PR #1 等待验收。
- [ ] 本任务验收后，根据固定原生不足证据另建外部app-server watcher任务；当前任务不得自行开始。
- [ ] D2实施先验证multiagentv2原生12小时等待；不足时实现外部app-server watcher；两者失败保持manual-only，禁止D1回退。
- [ ] GKD release candidate通过后，另行取得生产 `~/.codex` 安装授权。
- [ ] 生产bundle可用后，另行批准AIO接入与旧实现迁移；不得由GKD本体授权推断。
