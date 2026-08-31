# GKD I1 Trusted Task Context Implementation

## Internal Design

新增只读 `TrustedTaskContext` 数据对象与 resolver。resolver 只接受 trusted current path 和可选 task ID，使用已有 worktree/attachment/state 验证得到 durable identity、policy、snapshot 和受验证 bundle/project binding。新增的 `gkd-main` 薄 CLI 只调用这些只读能力与 planning package publisher；所有 lifecycle 写入继续留在既有 TaskService。planning package 的 artifact 以严格 parser 验证后原子发布，机器输出只含 selector 和 digest。

## Execution Details

先添加 runtime read-only/attachment enumeration 与 locator 正反合同，再实现 context 和 path-redacted inspect/preflight。随后实现 planning create/inspect、canonical source/installed classification、payload binary/manifest/lock，并扩展安装式 CLI 合同。运行 Python 3.9.6 与 Python 3.14.6 的批准验证，形成 implementation commit、delivery document commit 和 canonical delivery；delivery 后不再加入实现提交。
