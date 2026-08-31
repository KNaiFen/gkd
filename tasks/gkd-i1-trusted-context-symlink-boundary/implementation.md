# GKD I1 Trusted Context Symlink Boundary Implementation

## Internal Design

新增最小 lexical ancestor validator，沿原始输入路径逐段 `lstat`，发现任一 symlink 即返回既有 fail-closed 错误。resolver 在调用 `git_root`、`Path.resolve`、attachment identity compare 前调用该 validator；其余 context、planning package 和机器输出逻辑保持不变。

## Execution Details

先补 cwd、candidateRoot、trusted anchor 的 ancestor-symlink 正反合同，再接入 resolver/attachment validation，运行双解释器 core/focused 验证与 bundle/install。形成 implementation commit、delivery document commit 和 canonical delivery；delivery 后不再加入实现提交。
