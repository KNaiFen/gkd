# GKD Gate Repair R4 Implementation

## Internal Design

revision 已提供可验证顺序，因此逻辑时钟不改变 state shape。planning refresh 保持单 writer/CAS。automatic delivery 的 sidecar 坐落于 final implementation tree，由 existing delivery implementationHead 定位；它只陈述无自引用的 identity、base、bundle、result/evidence digest。deliver 以真实 canonical artifacts 重算这些事实，acceptance/rework 从同一 fixed tree 和复核结果验证它。

## Execution Details

先定位 R2/R3 的 ancestor 与 digest failures、结果/证据 parser、delivery path。完成所有源码/schema/tests/packaging/lock后运行真实 verifier/evidence，生成 sidecar并将其与实现一同提交；确认该 commit包含sidecar且是delivery.md提交的父提交。delivery.md下一提交后立刻deliver并停止。交付记录 revision/refresh/sidecar推导规则、实际artifact digest、fixed head与验证摘要；不得修改旧任务状态。
