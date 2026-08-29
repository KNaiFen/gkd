# GKD Gate Repair R5 Requirements

## Goal

恢复 GKD payload 在实际 executor Python 3.9 环境中的可执行性，并完成跨进程逻辑顺序、planning 文档 digest refresh 和无自引用 automatic delivery result-manifest 绑定门禁，使 O4 可以从 accepted merge 重新启动。

## User Decisions

- 本任务从 trusted main `2b8cdf0` 建立；O4、attempt 0、R1-R4 均是只读历史，禁止复用其 offer/claim/activation/delivery/PR。
- 一个精确 `gkd_executor`、一个独立 `gkd_acceptor`、trusted main 合并/收尾；不使用 nested agent 或 fallback。
- 旧 payload 在 executor Python 3.9 下无法执行 `status` 是本任务范围内的已知 bootstrap 缺陷。实施前唯一一次 precheck 可使用 trusted main 已验证的兼容解释器；补丁后必须在实际系统 Python 3.9 下重新验证，不将本机解释器路径写入 payload 或通用契约。
- 只修改 GKD canonical、合同测试和任务记录；生产、AIO、GitHub settings/Secrets、付费 runner、tag/Release、已发布资产保持不变。

## Scope

- 移除或替换 payload 中所有必要的 Python 3.10-only `zip(..., strict=True)` 用法，使用 Python 3.9 标准库可执行且同样 fail-closed 的显式严格配对校验；正常 task 状态不能再被伪装为 `FILESYSTEM_ERROR`。
- 使用 history revision 而不是 UTC 文本排序验证逻辑顺序，不向 event 或 delivery record 添加字段。
- 增加 planning-only、CAS 原子的 planning-refresh，刷新 requirements/plan/implementation 与 material digest；R5 自身不调用它。
- automatic delivery 使用 `tasks/<task>/result-manifest.json` sidecar：它位于 lifecycle 既有 `implementationHead` 的 fixed tree且属于该 implementation commit 改动，delivery.md 紧随该 commit；sidecar 不包含 implementation SHA。sidecar 绑定 task/repository/branch/path/base/bundle/verifier result/evidence digest。
- `deliver` 从实际 canonical verifier results 与 evidence regular files以结构化解析器重算事实并校验 sidecar；acceptance/rework 由 state implementation head 定位 sidecar并复核同一链。同步 CLI、service、model、schema、packaging expected set、bundle/lock、文档和正反合同；R5 task state 不增加新字段。

## Non-Goals

- 不实现 O4-O8，不改变 watcher、route、GitHub adapter、release 或 manual delivery 语义。
- 不把 Python 3.14 或任意本机解释器路径设为 workflow 必需条件，不以 PATH 覆盖替代兼容性修复。
- 不放宽 old acceptance ancestry、不接受自声明 result/evidence digest、不新增生产迁移或依赖。

## Acceptance Criteria

1. macOS/system Python 3.9 可执行 `gkd-task status`、`doctor` 和相关 task contracts；strict pairing 对长度/顺序不一致仍 fail-closed，原始程序错误不再被误报为 task filesystem 状态。
2. UTC 回拨/相同时间由 revision 验证；revision/head/record tamper 拒绝。R5 state 可由 current trusted-main status/doctor/rework 读取，且不含新 event/delivery key。
3. planning-refresh 只在 planning 成功且原子刷新所有 digest；其他 phase/漂移 fail-closed。
4. automatic deliver 从实际 canonical results/evidence 重算 result/evidence digest；缺失、非 canonical、task/base/bundle/result/evidence drift、sidecar不在implementation tree或不属于implementation commit改动都拒绝且不写 revision。
5. final implementation commit 包含全部源码/schema/tests/lock/sidecar，直接下一提交仅delivery.md；state implementationHead、sidecar location、delivery document parent、candidate bundle 与结果/证据事实一致，delivery后无提交。
6. Python 3.9 与常用开发解释器下的 task-core/runtime-bridge/rework/packaging/mutation/full verifier/bundle verify 均通过；独立 acceptor 用相对 policy 的 fixed-head CI success 和 canonical acceptance 通过。
7. 不引入绝对路径、凭据、新依赖或生产/AIO/GitHub settings 副作用。
