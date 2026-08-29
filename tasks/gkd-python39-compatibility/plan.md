# GKD Python 3.9 Compatibility Plan

## Goal

将默认 executor 的 Python 3.9 从单个 `status` smoke 修复提升为可交付的全链路 runtime baseline，再以该 accepted bundle 重新建立 gate-repair 和 O4。

## Design

1. 枚举并替换语言/API 断点：strict zip、dataclass slots 及任何实际可达的 3.10/3.11 语法或标准库依赖；对每类断点保留对应的行为合同。
2. 建立内置 TOML facade。新解释器继续委托标准 `tomllib`；Python 3.9 使用带上游许可的完整兼容实现。所有 payload TOML 入口、probes 和测试通过该 facade，避免环境依赖分叉。
3. 将异常分类收窄到真实文件系统错误，补 Python 3.9 subprocess/full-verifier 合同；更新 manifest/lock、许可和最低版本文档。

## Compatibility And Boundaries

- 兼容承诺从 Python 3.9 起；不扩张到 3.8，不改变外部 CLI 协议或 task state schema。
- 不将 `/usr/bin/python3` 写入 payload。该路径只作为本机 executor 事实和验收测试入口。
- 不混入逻辑时钟、planning refresh 或 delivery manifest 修复；它们将在本任务 accepted merge 后以独立 gate-repair 尝试完成。

## Execution Route

- trusted main 在 accepted execution bundle 上 bootstrap、approve、authorize、offer、prepare 和 claim。
- executor 在隔离 candidate worktree 完成实现、Python 3.9/开发解释器验证、evidence、PR 与 fixed-head delivery；不得验收、合并或收尾。
- independent acceptor 以完整 SHA、相对 `.gkd/policy.json`、Python 3.9 full verifier 和 fixed-head CI 审查；通过后由 trusted main narrow merge 和归档。

## Completion

- accepted merge 成为 `GKD-GATE-REPAIR-R6` 的唯一新基线；O4 仍暂停，直到 R6 独立通过。
