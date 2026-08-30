# GKD O6 Delivery Pack Compatibility Requirements

## Goal

在保持当前 schema-v1/full-install producer 与十 scope default verifier 不变的前提下，升级受信 delivery/acceptance consumer，使后续 O6 可严格交付 schema-v2 packs、八 scope core 与显式 optional lanes。

## User Decisions

- 基线为 trusted main `db72c1e1ef8e4c377274107a87299a368b57efb1`，execution bundle 为 `b7f1d783cf01cdcecfb12f98ce426877aec99b7b4647dacc542fdae8cc053d02`。
- O6 attempt 0 block head `b654587400e2a74bcaff7d46033225965995c554` 只作为未来格式与失败重现样本；不复用其 lifecycle、claim、implementation、sidecar 或 delivery document。
- 一个精确 executor、一个独立 acceptor，trusted main 合并清理；不修改生产/AIO/settings/Secrets/runner/tag/Release。

## Scope

- 在 `gkd_task` result consumer 中声明并严格验证 O6 计划的八 scope core、`optional-ci-advice`、`optional-review-remediation` 与组合 optional pack lane/profile；现有 default/core 继续要求原十个 scopes，historical/watcher 不变。
- 在 shipped bundle/source/manifest/lock consumer 中 forward-validate schema-v2 pack 声明、component/input ownership、core/pack install lists、mode/size/SHA-256 与 core/pack/content digests；未知、重复、交叉归属、缺失、extra、tamper、symlink 和 digest/head drift 均 fail closed。
- delivery、acceptance、rework 与 fixed-tree artifact 解析必须接受格式正确的未来 O6 result manifest/candidate bundle，同时拒绝 scope/lane/profile/pack/file/digest 不一致。
- 增加 future-format fixture/contract，可由 blocked O6 事实重建但不得依赖已删除 worktree 或本机绝对路径。
- 本任务的 `canonical/source.toml`、manifest schema 与 lock 继续使用当前 schema v1；默认 bundle 继续包含 CI advice/review runtime 与全部七个 Skills，payload/install 继续为 O5 的 107/111 文件。
- 本任务的 default/core verifier 继续运行原十个 scopes，包括 resource scanner 与 review core；只允许新增显式 optional lane 测试，不得将任何 scope 或文件移出默认面。

## Non-Goals

- 不实现 pack stage/verify/remove、role/project `--pack`、默认 executor Skill 收窄或 core 安装拆分；这些只属于 fresh O6 retry。
- 不进入 O7/O8，不修改任务状态 schema、自动 bridge、发布或生产迁移语义。

## Acceptance Criteria

1. Python 3.9.6 与 Python 3.14.6 的 default/core 仍为十 scopes，并通过完整 verifier、bundle/install、fresh delivery、fixed-head CI 与 independent acceptance。
2. future schema-v2 pack source/manifest/lock 与八 scope/optional lane artifacts 由 installed compatibility bundle 严格解析；正例通过，所有结构、归属、digest 和 drift 反例拒绝。
3. 当前 schema-v1/full-install bundle、project stage、core executor/acceptor route、legacy read/reject/migrate 行为逐项保持。
4. 不引入绝对路径、凭据、外部依赖或未授权副作用。
