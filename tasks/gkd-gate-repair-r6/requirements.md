# GKD Gate Repair R6 Requirements

## Goal

在已验收的 Python 3.9 executor runtime 上，完成跨进程逻辑顺序、planning 文档 digest refresh 和 automatic delivery result-manifest 绑定门禁，使 O4 可从 accepted merge 重新启动。

## User Decisions

- 本任务从 trusted main `b5569bba8268770e2363372221bbc07dbdd6b92a` 建立，并使用已验证 execution bundle `d9ea5f423987812bc4dd259d0bd90c485bbf0e8fdfda6c6a0d31f3f5a4a3aaf7`。O4、GKD-GATE-REPAIR attempt 0-R5 与 Python compatibility 失败 attempts 都是只读历史，禁止复用其 lifecycle 对象。
- R5 implementation `eea2973` 只可作为 gate-repair 代码参考；不得 cherry-pick 其 task state、task documents、`.agents`、Python compatibility 补丁、delivery 或 evidence。
- 一个精确 `gkd_executor` 交付、一个独立 `gkd_acceptor` 验收、trusted main 合并和收尾；不使用 nested agent、fallback 或手写 runtime/state。
- 只修改 GKD canonical、合同测试、任务记录和相关文档。生产、AIO、GitHub settings/Secrets、付费 runner、tag/Release、已发布资产保持不变。

## Scope

- 将 task history 的连续 revision/head/record relationship 定义为持久逻辑顺序；UTC 字段只作格式正确的审计信息，不再用于跨进程事件先后排序。拒绝 revision 缺口、重复、head/record mismatch 和 lifecycle/history 漂移，允许 wall-clock 回拨或相同秒。
- 增加 planning-only、CAS 原子的 planning document refresh transition：重新读取 requirements/plan/implementation，更新 document revision/digest 与 plan material digest；材料变化时失效旧 approval、authorization、offer 与相关 tracked capability 输入。R6 自身不调用该 transition。
- automatic delivery 使用 `tasks/<task>/result-manifest.json`。sidecar 必须是 final implementation commit 中新增或修改的 canonical regular file，并位于该 fixed tree；它不得声明自身所在 implementation SHA。delivery document commit 必须直接以 implementation commit 为父提交。
- `gkd-task deliver` 接收实际 canonical verifier results 与 verification evidence regular files，结构化解析并重算文件 digest；sidecar 绑定 task/repository/branch/path/base/candidate bundle/verifier result/evidence。缺失、非 canonical、identity/base/bundle/result/evidence drift 或 sidecar 未属于 final implementation commit 改动都在状态写入前拒绝。
- acceptance/rework 从既有 lifecycle `implementationHead` fixed tree 定位 sidecar和 artifacts，复核同一绑定链。同步 CLI、service、model、schema、packaging expected set、manifest/lock、Skills、文档与正反合同；R6 自身 task state 不新增字段，保持当前 trusted validator 可读。

## Non-Goals

- 不实现 O4-O8，不改变 watcher、route、GitHub adapter、release、manual delivery 或 Python runtime 兼容语义。
- 不放宽 old acceptance direct-parent ancestry，不接受自声明 digest，不向 state/event/delivery record 添加新字段，也不手工恢复旧 rejected attempt。
- 不安装生产 bundle、不修改 AIO、settings、Secrets、runner、tag、Release 或已发布资产。

## Acceptance Criteria

1. 系统 Python 3.9 的 accepted execution bundle可完成 bootstrap/status/doctor、fresh offer/claim、完整 verifier、bundle generate/verify 和 canonical deliver；开发解释器回归同样通过。
2. history 顺序只依赖连续 revision/head/record 关系；UTC 回拨/同秒通过，revision/head/record/lifecycle tamper 拒绝。R6 final state 可由 merge 前 trusted main status/doctor/accept/rework 读取，且不含新 state key。
3. planning refresh 仅在 planning phase 以 exact head/revision CAS 成功，原子刷新三份文档与 material digest；非 planning、tracked drift、并发 CAS 或无效文档拒绝且无半状态。R6 自身 lifecycle 不调用 refresh。
4. final implementation commit 包含全部源码/schema/tests/lock、canonical verifier result、verification evidence 与 result-manifest；sidecar 不含 implementation SHA，且确属该 commit 改动。下一提交只包含 delivery.md，随后唯一 final state commit，无 post-delivery commit。
5. automatic deliver 从实际 result/evidence 文件重算摘要；任一 identity/base/bundle/artifact/manifest drift、非 canonical/非 regular file、sidecar位置或 implementation-tree drift 均拒绝且 revision 不变。
6. candidate acceptance/rework 合同复核同一 fixed-tree artifact 链；系统 Python 3.9 与开发解释器完整 verifier、bundle、fixed-head CI、独立 review 和 canonical acceptance 全部通过。
7. 不引入绝对路径、凭据、新外部依赖或生产/AIO/GitHub settings/Secrets/runner/tag/Release 副作用。
