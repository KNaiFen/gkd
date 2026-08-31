# GKD O8 Release Upgrade Compatibility Requirements

## Goal

在不删除任何公开 legacy read、reject、restore 或 migrate 承诺的前提下，将完整历史兼容矩阵从每个 core PR 的默认验证中移出，形成可复现的 release-upgrade lane，并把 release/finalization engine 的未来合并边界记录为明确决策。

## User Decisions

- 基线为 trusted main `48e1e25948fe2e3348068821e6d945c712be89d9`；execution bundle 为 `904e1d02d5519b00bf9e3b9bda8e97a4ab1883d3114730d3e0caae03c25582af`，project inventory 为 `f0b06f5d5bfc3e404e6d8e683714374e00fe093d4b610ab6ccaa2db458226e34`。
- O1-O7、P0、delivery compatibility 和 O7 result reuse 都是已合并只读历史；本任务不复用任一旧 task、offer、claim、runtime、candidate 或提交。
- 一个精确 executor 交付，一个独立 acceptor 验收，trusted main 合并和清理；不修改生产、AIO、settings、Secrets、runner、tag 或 Release。

## Scope

- 建立版本化、可执行的 public legacy-format catalog。每个格式明确公开入口、core 的一个 read 正例与一个 reject 或 restore 正例，以及 release-upgrade 矩阵中附加的组合/版本/异常案例；catalog 不能只由文档叙述组成。
- core 保留每种 catalog 格式的最小代表合同，完整稳定版本 promotion matrix、组合兼容分支和扩展历史案例移到新的显式 `release-upgrade` lane/profile；lane 必须具有严格的 scope、head、base、environment、test-ID、digest 和固定结果验证。
- 保持 `historical/watcher` 独立且不重命名；更新 `gkd-verify`、result lane/profile、evidence、bundle declaration/lock、双解释器验证和正反合同。
- 在 `docs/adr/` 按模板新增 accepted ADR：O8 保留 `gkd-finalize`、`gkd-release` 的公共 CLI 和 record schema，不在本任务提取或合并 shared engine；ADR 定义一个后续独立迁移任务的前置条件、兼容合同和停止边界。

## Non-Goals

- 不删除、改名或弱化任何 legacy reader、reject、restore、`migrate-v1`、production recovery、release/finalization CLI、record schema、error code、stdin/stdout 或 trusted-main authority。
- 不直接合并或提取 `gkd-finalize`/`gkd-release` engine，不添加普通 PR 的 release-upgrade CI，不修改已发布资产或生产安装。

## Acceptance Criteria

1. catalog 覆盖仓库当前承诺的每种公开旧格式；每项在 default/core 中保留一个可独立定位的 read 测试和一个 reject 或 restore 测试，且缺失、重复、跨 scope 或未覆盖会失败。
2. release-upgrade lane 运行完整历史 matrix，固定 result manifest 严格绑定该 lane 的完整 scope/test IDs、base/head、environment 和 digest；两次独立 evidence 生成字节一致。
3. default/core 不再执行被迁出的组合、版本枚举和扩展 matrix，但仍通过代表性兼容承诺；historical/watcher 的 scope、行为和 `unsupported` host boundary 不变。
4. ADR 明确拒绝在 O8 合并 release/finalization engine，并定义后续单独迁移任务需要的 CLI golden output、旧 record read/reject、promotion request shape、provenance split、adapter 和双解释器合同。
5. Python 3.9.6 与 Python 3.14.6 的 default/core、historical/watcher、release-upgrade、bundle/install、fixed-head CI 和 independent acceptance 均通过；不引入绝对路径、凭据、外部依赖或未授权外部副作用。
