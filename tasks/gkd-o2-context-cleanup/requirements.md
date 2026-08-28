# GKD-O2 Requirements

## Goal

清理 `.agents/context.md` 的过期、矛盾和重复状态，使新 Session 能直接识别当前发布事实、授权边界和下一任务；不改变 GKD bundle、生产安装或历史决策记录。

## User Decisions

- O2 必须从 O1 accepted merge `eacd9652134a767902d74da5b4b3d084fa122dfa` 之后的 trusted main 完整基线开始。
- 只允许一个 `gkd_executor` 交付，独立 `gkd_acceptor` 验收，trusted main 合并和收尾。
- host-level 子代理回收 hook 只保留为事实，不复制到 GKD bundle、`.codex` 或项目配置。
- 不修改生产 `~/.codex`、AIO、GitHub settings/Secrets、付费 runner、tag/Release 或已发布资产。

## Scope

- 删除 `.agents/context.md` 中已被后续事实覆盖的“生产目录和 AIO 仍未写入”旧表述，保留当前授权/未授权边界。
- 合并重复的 AIO C final 条目，保留一条可核对的 merge、digest、隔离根和未触碰范围事实。
- 将当前状态、下一任务和历史事实分层，明确 O1 已完成、O2 正在执行以及 O3 依赖 O2 accepted SHA。
- 保留指向 `.agents/decisions.md`、`.agents/open-items.md` 和任务 acceptance/retrospective 的历史索引，不重写历史记录。

## Non-Goals

- 不改 canonical source、payload、manifest/lock、Skills、roles、scripts、tests 或生产/AIO 文件。
- 不删除任何历史决策、失败尝试、digest、release 或 migration 事实。

## Acceptance Criteria

1. context 只保留一条当前状态和一条 next task，生产/AIO 授权边界与已发布 pin 无矛盾。
2. 重复 AIO C final 只剩一条；历史细节仍可从 decisions/open-items/task records 追溯。
3. host-level 子代理回收事实仍明确标注为 bundle 外配置。
4. 文档 diff 不包含绝对本机路径、凭据、token 或新机制；代码行为、manifest 和安装面不变。
5. candidate delivery、独立 review、固定头 CI 和 `gkd-task accept --merge` 均成功。
