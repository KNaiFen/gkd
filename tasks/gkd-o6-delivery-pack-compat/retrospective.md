# GKD O6 Delivery Pack Compatibility Retrospective

## 结果

O6 首次候选证明默认 scope 与安装面变化会同时改变 fixed-tree delivery artifact。已接受的 execution bundle 只能理解旧十 scope default，因此先用一个仍能由旧 consumer 接受的任务，把新格式的严格解析能力合入；O6 producer 随后必须从新 lifecycle 重新交付。

## 经验

- 对自托管任务，consumer compatibility 必须先于 producer 格式或默认 scope 变化合入。只在候选中同时改变两端会在 `deliver` 处形成不可交付的死锁。
- compatibility task 必须冻结自身 producer，否则新 parser 无法由旧 delivery contract 接受，也无法提供可靠的前置基线。
- future-format fixture 应当在仓库内重建并绑定实际 mode、size、SHA-256 与 ownership，不能引用被 block attempt 的临时 worktree。
- lane/profile 是 result manifest 的协议字段，不是测试调度细节；必须同 scope、core/pack digest、fixed head 一起由 delivery/acceptance 验证。

## 后续

从 merge `d3703bf57c5047f41db57e97d9117550acf7ffc9` 生成并验证新的 development execution bundle，再建立全新 O6 retry，实施默认角色和 optional pack 拆分。
