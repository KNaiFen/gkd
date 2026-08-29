# GKD Gate Repair R5 Implementation

## Internal Design

以可移植的显式长度/顺序检查替代 Python 3.10 strict zip，保留 fail-closed。revision是已有逻辑序列，refresh在CAS事务中更新文档记录。automatic sidecar由delivery已有implementationHead的固定tree定位，不含自指SHA；deliver以实际canonical results/evidence重新计算其声明的digest，state保持既有形状。

## Execution Details

先用受控兼容解释器完成一次旧payload precheck并记录版本事实，随后修复所有必要3.10-only调用。补丁后必须用实际Python3.9跑status/doctor和合同。完成源码/schema/tests/packaging/lock后生成真实results/evidence和sidecar，将它们放进final implementation commit；下一提交仅delivery.md，立即deliver后停止。交付记录Python兼容、revision/refresh、sidecar固定tree、artifact digest、fixed head和验证；不修改旧任务状态。
