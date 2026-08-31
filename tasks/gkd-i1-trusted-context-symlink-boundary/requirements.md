# GKD I1 Trusted Context Symlink Boundary Requirements

## Goal

修复已合并 I1 TrustedTaskContext 的路径边界缺陷：任何 candidate cwd、runtime attachment candidateRoot 或 trusted anchor 的祖先 symlink 都必须在物理路径解析前被拒绝，同时保持正常 context/preflight/planning 行为不变。

## User Decisions

- 基线为 trusted main `5605c5fb16d0571185aeab256cf4c4c40a52061c`；execution bundle 为 `045604ca8572525c56cf6561bad53e22a16a6efa2fec1b875c3f97e118960192`，project inventory 为 `4bc58d1e8d44edc39bef1117b783e95abd6c847fae4f1b6f8a09ad73b77f8f3e`。
- 这是 I1 的独立 corrective task；I1 R2 已合并，但 post-accept audit 发现祖先 symlink 缺陷。不得复用其 offer、claim、receipt、candidate 或 PR 状态。
- 一个精确 executor 交付，一个独立 acceptor 验收，trusted main 合并和清理；不修改生产、AIO、settings、Secrets、runner、tag 或 Release。

## Scope

- 在 context resolver、candidate locator 和 runtime attachment validation 的原始输入路径上增加逐段 lexical `lstat` 检查，任何祖先 symlink、叶子 symlink、跨 common-dir 或 identity drift 均 fail closed。
- 保持真实非 symlink candidate、trusted-main selector、唯一 attachment、gkd-main inspect/preflight/planning create/inspect、bundle/project binding 和现有机器输出不变。
- 增加 cwd 与 attachment 两条路径的 ancestor-symlink 正反合同，并更新 manifest/lock、delivery evidence 和文档。

## Non-Goals

- 不修改 task state schema、CAS、automatic route/claim/wait、delivery、CI、accept/rework、planning package parser、公开 CLI 形状或 P2-P5 功能。
- 不将任何 symlink 处理扩展为删除、修复或静默 realpath；错误必须快速失败。

## Acceptance Criteria

1. candidate cwd 的任一祖先 symlink、runtime attachment candidateRoot 的任一祖先 symlink、trusted anchor 的任一祖先 symlink 都返回稳定错误且不写 task/runtime/Git。
2. 正常 candidate、trusted-main selector、attachment fallback 三路 context 仍等价；I1 inspect/preflight 在存在无关历史 task drift 时仍可定向工作。
3. Python 3.9.6 与 Python 3.14.6 的 core verifier、focused symlink/context contracts、bundle/install、fixed-head CI 和 independent acceptance 通过。
4. 不引入绝对路径、凭据、外部依赖或未授权外部副作用。
