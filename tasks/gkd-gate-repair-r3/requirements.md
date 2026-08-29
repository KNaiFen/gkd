# GKD Gate Repair R3 Requirements

## Goal

完成 GKD 逻辑时间、planning 文档 digest refresh 与 automatic delivery result manifest 门禁修复，并以 self-hosting-compatible 的交付形状通过独立验收，从而解除 O4 重启前置阻塞。

## User Decisions

- 本任务从 trusted main `b1adc67` 建立；所有旧 O4、attempt 0、R1、R2 拒绝记录只读保留，不复用任何旧 offer、claim、activation、delivery 或 PR。
- 只允许一个精确 `gkd_executor`、一个独立 `gkd_acceptor` 和 trusted main merge/收尾；不启用 nested agent 或 fallback。
- 只改 GKD canonical、合同测试、task records；生产、AIO、GitHub settings/Secrets、付费 runner、tag/Release 和已发布资产不在范围内。

## Scope

- 使用现有、integrity-covered `history.revision` 作为逻辑顺序，不再以 UTC 字符串排序决定 state 有效性；保持 event 和 delivery record 的既有 key set。
- 增加仅 planning 可调用的 CAS `planning-refresh`，一次性刷新 requirements/plan/implementation 与 plan material digest；planning 外文档漂移继续 fail-closed。R3 自身不得调用此 transition。
- automatic delivery 使用 canonical `tasks/<task>/result-manifest.json`。sidecar 必须包含在最后一个 implementation commit，该 commit 必须是 delivery document commit 的直接父提交；sidecar `implementationHead`、lifecycle `implementationHead` 和 delivery document parent 必须相等。
- `deliver` 必须以结构化输入读取实际 canonical verifier results 与 evidence 文件，重新计算/验证 verifier result digest、evidence digest、task/base/implementation/bundle 事实，再校验 sidecar；不能只信任 sidecar 自声明。新 acceptance/rework 必须从 fixed implementation tree 与实际复核结果执行同类验证。
- 更新 schema、CLI、service、acceptance/rework、packaging expected set、manifest/lock、README 和正反合同；不得向 R3 task state 新增 event 或 delivery fields。

## Non-Goals

- 不实现 O4/O5/O6/O7/O8，不重写 watcher、CI adapter、路由或 release。
- 不通过取消 digest、放宽 old acceptance ancestry、虚构 evidence 或接受自由文本声明绕过门禁。
- 不新增生产迁移、依赖或外部设置。

## Acceptance Criteria

1. 回拨/相同 event UTC 在新 validator 下可由 revision 顺序通过；revision/head/record tamper 拒绝。R3 state 仍可由合并前 trusted main `status`、`doctor`、`rework` 读取。
2. planning-refresh 在 planning 精确刷新所有受管文档 digest，在其他 phase fail-closed；全成功和失败路径都保持 CAS/事务完整性。
3. automatic deliver 从实际 results/evidence 解析取得 digest；任一文件缺失、非 canonical、result/evidence/bundle/base/task/head drift 或 sidecar 篡改均拒绝且无 revision 写入。
4. sidecar 位于 final implementation commit；delivery document 是唯一下一提交；state delivery implementation head、sidecar implementation head、delivery document parent 与 fixed output bundle digest 完全一致。delivery 后没有候选提交。
5. task-core、runtime bridge、rework、packaging 和 mutation/negative contracts 通过；独立 acceptor 的 exact-head CI 使用相对 `.gkd/policy.json` 并成功。
6. 不出现绝对路径、凭据、新依赖或生产/AIO/GitHub settings 副作用。

