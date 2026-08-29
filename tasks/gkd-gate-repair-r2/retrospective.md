# GKD-GATE-REPAIR-R2 Retrospective

## What Worked

- 以 history revision 派生逻辑顺序、保持 state 旧字段形状，解决了 R1 的 trusted-validator 不可读问题。
- delivery 后没有追加提交，bundle/result sidecar/lock 在 fixed head 一致；438/438 verifier 和 exact-head CI 成功。

## Failure

- sidecar 被作为独立提交放在 implementation 与 delivery document 之间，导致 state 的 implementation head 不再是 delivery document 的直接父提交，触发旧 acceptance hard gate。
- result/evidence digest 仅是 sidecar 内的自声明，delivery 服务未读取实际 canonical verifier result/evidence 文件验证它们，无法防止协同篡改。

## Required R3 Changes

- sidecar 必须包含在最后一个 implementation commit；该 commit 必须同时是 delivery document commit 的直接父提交，sidecar `implementationHead` 和 lifecycle `implementationHead` 必须相同。
- automatic `deliver` 必须接收或定位实际 canonical verifier results/evidence 文件，并用结构化解析器重算结果/evidence digest 后与 sidecar 比对；acceptance 复跑或读取同类事实验证该链。
- state record 保持旧字段；R3 自身任何新服务能力不得改变其 bootstrap/delivery event key 或 delivery key。

