# GKD-O4-R5 Requirements

## Goal

完成 O4 的 watcher/probe 历史 lane 隔离，并使 canonical result consumer、delivery、acceptance 与 rework 按 result manifest 的显式 lane/profile 校验完整 scope 集合。默认 verifier 不得加载 watcher scope，historical lane 必须独立、可追溯且 fail-closed。

## User Decisions

- 本任务从 trusted main `edf0f5c316d828594df58197c043cbc7ee74defb` 建立，execution bundle 固定为 `b0174e6c154c22dd73975857e084e26d095f7fb73e5b80588bb7a8a8f697a618`。
- O4、R1、R2、R3、R4 lifecycle 都只读归档；R2 diff 可只读参考，禁止复用其 task、offer、claim、runtime、branch、PR、delivery 或 result artifacts。
- 只允许一个精确 `gkd_executor` 交付、一个独立 `gkd_acceptor` 验收和 trusted main 合并/清理。executor 必须通过 `/usr/bin/python3 -B /private/var/folders/dv/7psz5djd3537ghdrhkpzy7dw0000gn/T/gkd-o4-r2-execution-bundle/source/gkd/bin/gkd-task` 调用 task CLI，不依赖 PATH。
- 不修改生产 `~/.codex`、AIO、GitHub settings/Secrets、付费 runner、tag/Release 或已发布资产；不删除 watcher/probe 源码、历史 evidence 或行为测试。

## Scope

- 默认 `scripts/gkd-verify` 仅运行十个 core scopes；historical watcher verifier 是显式入口，可独立运行 preserved 47 watcher contracts，并显式记录 optional host-capability probe 的 `unsupported`。
- result manifest 明确记录已知 lane/profile 与完整 scope 集合；consumer、delivery artifact validation、acceptance 和 rework 从 fixed tree 严格验证该声明，而不以旧全局 scope 集合推断 default 必需项。
- 未知 lane/profile、lane-scope mismatch、scope/test ID 缺失/未知/重复、base/head/verifier/result/evidence digest drift 都在状态写入前拒绝。
- 更新 README、测试入口、schema、manifest/lock 和正反合同；保留现有 `gkd_watchdog` API、`gkd-watchdog-mcp` CLI、M-1B evidence schema 和 M-1C 结论。

## Non-Goals

- 不重写 watcher 协议、MCP adapter、app-server 控制逻辑、native probe 或其安全/清理语义。
- 不删除 fixtures/evidence、不启用 automatic route、不拆 O5-O8，也不再改变 R6 或 Python 3.9 runtime 契约。

## Acceptance Criteria

1. default verifier 在 Python 3.9.6/3.14.6 均只产出十个 core scopes 和可校验 default lane/profile manifest。
2. historical lane 独立运行 watcher contracts 并产出可校验 historical lane/profile；无 host capability 时稳定记录 `unsupported`，不伪造 success。
3. consumer、delivery、acceptance 与 rework 都接受由明确 lane/profile 完整定义的 scope 集合；unknown lane/profile 及所有 scope/test/digest drift 继续 fail-closed。
4. watcher/native/M-1B/M-1C 测试覆盖不下降，两次 historical evidence 字节一致；完整 verifier、bundle、fresh claim-to-deliver、fixed-head CI 和 independent acceptance 都通过。
5. 不引入绝对本机路径、用户名、凭据、新依赖或未授权外部副作用。
