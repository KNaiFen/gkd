# Open Items

- [x] `gkd_core_implementation` 已于2026-08-18明确授权；按hybrid B从里程碑-1人工执行交接开始。
- [x] 已创建 `KNaiFen/gkd` 与 `KNaiFen/gkd-sandbox`；源码基线已推送，sandbox保持空仓库。
- [x] `GKD-M-1A` 在 `codex-cli 0.147.0` 输出版本绑定的 `native_insufficient`；fixed head `bd8332a` 已独立验收并通过PR #1合并为 `0cc09e9`。
- [x] `GKD-M-1B` PR #2 新固定head `98df6ba122d9fe8aed230094ed806010e7002aa7` 已通过独立验收并squash merge为 `1d303456f2afcaa4e5fd0353232e30c5c6b63a33`；结论仅为 `core_ready_for_live_gate`。
- [x] `GKD-M-1C` fixed head `4332cea7aecc7540640add626ddca6b9b3d8cbad` 的 `unsupported` 已通过独立验收并由PR #3 squash merge为 `afacf490aee948a0e70910304976da6c667375fa`；auto route保持禁用，manual-only继续生效。
- [x] `GKD-M0-A` PR #4首轮验收的metadata mode、evidence终态顺序和跨机器污染扫描3项finding已由 `3bab17697735adcf85e1214d6580966a7e896f47` 修复并重新取证。
- [x] `GKD-M0-A` 新固定head `68c418aef398dd6c2a3576c330d744e5d351acfa` 已通过独立终验并squash merge为 `2207645ab7a3bfc4b0ad4a15cf4bbe743612933c`；结论仅为 `canonical_foundation_ready`。
- [x] 里程碑0的正式范围已由M0-A全部覆盖；未定义、未批准具体范围的M0-B占位不再作为任务。
- [x] M0-A终态验收已落盘；任务worktree、本地分支和远端分支均已删除并回填实际清理结果。
- [ ] 在目标 fresh runtime 证明 `wait_agent(timeout_ms=3600000)` 被实际工具接受、child final 可提前返回，并用确定性/fake-clock 合同验证最多12轮静默重等与单一timeout；当前工具层只声明360,000ms，门禁未通过前不得使用更短循环替代。
- [ ] 规划并确认里程碑1首个任务 `GKD-M1-A`，继续由人工顶层execution session执行。
- [ ] GKD release candidate通过后，另行取得生产 `~/.codex` 安装授权。
- [ ] 生产bundle可用后，另行批准AIO接入与旧实现迁移；不得由GKD本体授权推断。
