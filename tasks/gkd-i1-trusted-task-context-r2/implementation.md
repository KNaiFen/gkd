# GKD I1 Trusted Task Context Implementation

## Internal Design

新增只读 `TrustedTaskContext` 数据对象与 resolver。resolver 只接受 trusted current path 和可选 task ID，使用已有 worktree/attachment/state 验证得到 durable identity、policy、snapshot 和受验证 bundle/project binding。显式 task ID 先按确定性索引定位对应 task record，再只读取该 record；不得递归校验无关历史 task，避免历史 drift 阻断正常 selector。新增的 `gkd-main` 薄 CLI 只调用这些只读能力与 planning package publisher；所有 lifecycle 写入继续留在既有 TaskService。planning package 的 artifact 以严格 parser 验证后原子发布，机器输出只含 selector 和 digest。

## Execution Details

先修复 selector 定向读取并添加“无关历史 task drift 不阻断”的回归合同，再添加 runtime read-only/attachment enumeration 与 locator 正反合同；随后实现 context 和 path-redacted inspect/preflight、planning create/inspect、canonical source/installed classification、payload binary/manifest/lock，并扩展安装式 CLI 合同。运行 Python 3.9.6 与 Python 3.14.6 的批准验证，形成 implementation commit、delivery document commit 和 canonical delivery；delivery 后不再加入实现提交。
