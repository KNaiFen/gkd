# GKD-O4-R6 Implementation

## Internal Design

将 default 与 historical 建模为显式 lane。manifest 将 lane/profile 与完整 scope 集合一起固定：default 只声明 core scopes；historical 声明 watcher scope 与 optional host-capability 结果。fixed-tree consumer 先校验 schema、已知 lane/profile、完整无重复 scope，再校验 test IDs、base/head 和 digest；不得从旧全局 `SCOPES` 推断 default 必需项。旧无 lane/profile manifest 仅经明确 legacy strict path 验证。

default 不导入 `gkd_watchdog` 或 `probes/app-server-watcher`；historical 才运行 preserved contracts，并保留 M-1B 47 项及 M-1C `unsupported` 可追溯性。

## Execution Details

第一步执行 bridge execution context 提供的精确 status/doctor argv，禁止裸 `gkd-task` 或从 cwd 推断参数。修改前建立 default/historical 基线，最小分层；优先移植已拒绝 R5 中仍适用的 producer/runner 差异，不重复已合并 compatibility consumer。冲突或真实平台缺口须 fail-closed 记录。final implementation commit 必须含实际 verifier result/evidence/result-manifest；delivery 后停止。
