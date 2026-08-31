# GKD O7 Contract Index And Result Reuse Requirements

## Goal

在不降低既有合同覆盖、固定 head 绑定或可追溯性的前提下，让 delivery 消费 task-core 的 canonical 结果，建立测试 ID 到合同 ID 的确定性反向索引，并收敛 foundation 的重复映射实现。

## User Decisions

- 基线为 trusted main `20f787b01248bcdc77af32952b439773b06be752`；execution bundle 为 `8c34b7474d4fb55c1d688f515dbd2f4f7cac32c8706865a4bc8eea2060bd10b3`，默认 core 为八 scopes。
- O1-O6、P0 与 delivery manifest compatibility 都是已合并只读历史；本任务不复用任一旧 task、offer、claim、runtime、candidate 或提交。
- 一个精确 executor 交付，一个独立 acceptor 验收，trusted main 合并和清理；不修改生产、AIO、settings、Secrets、runner、tag 或 Release。

## Scope

- 让 delivery-contract 在提供 canonical results 时只选取并验证 task-core 中既有的九个目标测试，继续执行 document、implementation head、temporary/protected/output 等该 lane 特有边界检查。
- 为 watchdog 和 foundation 建立声明式且确定性的 contract-to-full-test-ID 映射，并派生稳定的 full-test-ID-to-contract-IDs 反向索引；共享测试可被多个合同引用但只对应一次 canonical 执行结果。
- 在结果消费层提供最小的已验证 scope 测试选集查询，保持现有 schema、fixed head、base ancestry、environment、scope、digest 和全通过约束；选集缺失、失败或漂移必须拒绝。
- 更新所有受影响的 runner、evidence、正反合同与 bundle declaration/lock，使证据按 contract ID 可查询且失败事实保留 test ID、scope 和 fixed head。

## Non-Goals

- 不删除 task-core、delivery、watchdog 或 foundation 的任何现有合同，不改变 canonical results schema、结果写入顺序、release/finalization、task/role/bridge/acceptance 或 watcher 行为。
- 不进入 O8 的旧格式矩阵降频或 `gkd-finalize`/`gkd-release` engine 合并评估，不修改已发布资产或生产安装。

## Acceptance Criteria

1. canonical task-core 结果生成一次后，delivery-contract 在 canonical-result 模式不再执行 focused unittest suite，并严格拒绝九项任一缺失、失败、head/base/environment/scope/digest 漂移。
2. watchdog 与 foundation 的每个合同仍可查询到完整 test ID 列表；反向索引确定、无重复且能表示一个测试对应多个合同，原有合同覆盖不下降。
3. 所有 canonical-result 消费方继续把 scope、fixed head 和环境绑定纳入失败路径；evidence 中能关联 contract ID、test ID 和结果 digest，负向合同 fail closed。
4. Python 3.9.6 与 Python 3.14.6 的 core verifier、相关 focused contracts、bundle/install、fixed-head CI 和 independent acceptance 均通过。
5. 不引入绝对路径、凭据、外部依赖、隐式重复执行或未授权外部副作用。
