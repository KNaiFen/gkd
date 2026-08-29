# GKD Gate Repair R2 Implementation

## Internal Design

逻辑顺序复用 immutable history revision，不增加 event 字段。planning refresh 是现有单 writer/CAS 事务内的文档记录重算。自动路线的 result manifest 是固定任务路径下、在 implementation head 已存在的 canonical sidecar；服务和 acceptance 通过 delivery record 已有的 `implementationHead`、`candidateOutputBundleDigest` 与 task identity 定位、读取和验证该文件，而不扩展 task state。

## Execution Details

executor 先审计 attempt 0/R1 的失败点及所有 task-state schema/packaging expected-set，再实现最小兼容改动和负向合同。全部 tests、manifest/lock、candidate output digest、result-manifest sidecar 和 delivery 文档必须在 delivery 前固定；delivery 后不得有任何代码、schema、测试、lock、manifest 或文档提交。交付文档记录 revision 逻辑顺序、refresh phase 边界、sidecar 绑定规则、最终 digest、fixed head、测试摘要和清理事实；不得修改旧 O4 或已拒绝 task 状态。
