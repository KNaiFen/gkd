# GKD Gate Repair R6 Retrospective

## 结果

R6 解决了阻止 O4 干净重启的三项通用门禁：跨进程顺序不再依赖 UTC 排序，planning documents 有受限的 refresh 路径，automatic delivery 绑定 final implementation tree 中的 verifier artifacts。

## 经验

- Lifecycle state 需要唯一、持久的顺序来源。revision、head 与 record continuity 适用；独立生成的 timestamps 不适用。
- immutable planning digests 必须有显式且范围狭窄的 update transition，否则只修正文档也可能永久锁死 implementing task。
- delivery metadata 必须绑定 acceptance 能从 fixed tree 独立定位并重算的 artifacts。post-delivery sidecar 或自指 commit field 无法提供此保证。
- 必须先完成 Python 3.9 支持，修复才能经实际 executor path 运行；仅有 status/doctor compatibility 不能证明 delivery compatibility。

## 后续

从 R6 closeout baseline 建立全新 O4 task。不得 rework 任一已拒绝的 O4 lifecycle。
