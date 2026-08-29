# GKD Gate Repair R6 Implementation

## Internal Design

task history 以 revision 形成持久逻辑序列，UTC 保留审计但不排序。planning refresh 在现有 transaction/CAS 中重建三份文档记录并使过期授权失效。automatic sidecar 由 lifecycle 既有 implementation head 的 fixed tree 定位，不含自指 SHA；deliver、acceptance 与 rework 均通过结构化 parser 对实际 verifier result/evidence 文件重算 digest，state 保持现有形状。

## Execution Details

从 current main 实现最小 gate-repair，可对照 R5 implementation `eea2973`，但不复制旧 task/runtime/`.agents`。先补 revision/refresh/artifact 正反合同，再更新 schema、source manifest、lock 和 Skills。以系统 Python 3.9 与开发解释器完整验证；将真实 canonical result、evidence、无自指 sidecar 与全部实现放入 final implementation commit，下一提交只含 delivery.md，立即用系统 Python 3.9 `gkd-task deliver` 生成唯一 final state commit后停止。
