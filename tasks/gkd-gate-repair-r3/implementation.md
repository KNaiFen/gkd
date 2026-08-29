# GKD Gate Repair R3 Implementation

## Internal Design

history revision 已是单 writer、连续且 integrity-covered 的逻辑顺序，因此移除 UTC 排序检查而不扩展 state。planning-refresh 沿用现有事务模型。automatic delivery 从固定 implementation tree 的 sidecar 和真实 results/evidence regular files构造可信 binding：服务重算 digest，sidecar 与生命周期已有 implementationHead/candidate output 字段闭合；没有新 state 字段。

## Execution Details

executor 先定位 R2 的 acceptance hard gate、现有 results/evidence canonical parser 与 delivery 调用点。所有代码、schema、tests、packaging、lock、实际 results/evidence、sidecar 必须在 final implementation commit 固定；sidecar 要声明该 commit SHA。下一提交只添加 delivery.md，随后立刻 deliver，禁止后续提交。交付文档记录 revision 顺序、refresh 边界、results/evidence 来源、sidecar ancestor、最终 digest、fixed head、测试和清理事实；不修改旧任务状态。
