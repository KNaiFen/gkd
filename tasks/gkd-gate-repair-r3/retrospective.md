# GKD-GATE-REPAIR-R3 Retrospective

## Finding

Git commit 的内容寻址使“普通文件声明其自身所在 commit SHA”不可构造：sidecar 内容影响 tree，tree 影响 commit SHA，不能把最终 SHA 再写回同一 tree。

## Consequence

R3 的 task requirements 在 claim 后被证明不可满足。正确做法不是放宽 delivery ancestry，而是删除 sidecar 中的自指 `implementationHead` 字段，由 delivery state 已有的 implementation head 和该 commit 的固定 tree 作为唯一定位事实。

## R4 Boundary

R4 保持 state 兼容、sidecar 位于 final implementation commit、delivery document 紧随其后，并让 service 从真实 result/evidence 文件校验 sidecar 内容；sidecar 只声明可独立计算的任务、base、bundle、result/evidence 事实。

