# GKD O4 Lane Manifest Compatibility R3 Implementation

## Internal Design

将 lane/profile 定义为 manifest 内的显式 schema 事实。共享 validator 先验证已知 profile、完整无重复 scope，再验证 scope 的 test IDs、base/head 和 digests；legacy manifest 走严格旧分支。delivery、acceptance 与 rework 只调用这一个 validator。本任务不改变当前 producer 的实际 default scope。

## Execution Details

executor 先按 bridge `execution_context(envelope_id)` 返回的 status/doctor argv 核验 candidate。修改前建立当前 result baseline 与 synthetic profile negative cases；不得借测试跳过或放宽 validation 缩短路径。delivery document 提交后以当前 `git rev-parse HEAD` 和 trusted status revision 调用 canonical deliver；交付后停止。
