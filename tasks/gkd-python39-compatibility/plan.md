# GKD Python 3.9 Compatibility Plan

## Goal

将默认 executor 的 Python 3.9 从单个 `status` smoke 修复提升为可交付的全链路 runtime baseline，再以该 accepted bundle 重新建立 gate-repair 和 O4。

## User Decisions

- 用户选择完整 Python 3.9 兼容移植，基线为 trusted main `f4ec2461f3314a9246b3d0f5ba25eb67b693e862`。
- 一个 executor、一个 independent acceptor、trusted main merge；不使用 nested agent、外部依赖或解释器路径 fallback。
- 生产、AIO、GitHub settings/Secrets、runner、tag/Release、已发布资产保持不变。

## Behavior And Defaults

- 枚举并替换语言/API 断点：strict zip、dataclass slots 及任何实际可达的 3.10/3.11 语法或标准库依赖；对每类断点保留行为合同。
- 新解释器继续使用标准 `tomllib`；Python 3.9 使用带上游许可的完整内置 TOML compatibility facade。所有 payload TOML 入口、probes 和测试通过该 facade。
- 异常分类只将真实 filesystem 错误归为 `FILESYSTEM_ERROR`；Python 3.9 full verifier 是默认交付验证，不是可选 smoke。

## Scope

- 更新 payload、watcher/probe、测试运行器、manifest/lock、许可和最低版本文档。
- 增加 Python 3.9 subprocess/full-verifier、TOML parity/negative 和 CLI 分类合同。

## Non-Goals

- 不改 logic clock、planning refresh、delivery sidecar、state schema、O4-O8、route、CI policy、release 或生产迁移。
- 不支持 Python 3.8 或更低版本，不引入 pip/runtime download 或机器专用解释器路径。

## Acceptance Criteria

- Python 3.9 与开发解释器均通过完整 verifier、bundle 和核心 CLI；TOML 与严格配对保留 fail-closed 行为。
- manifest/lock/许可/文档一致，独立 acceptor 对 fixed head 的 canonical acceptance 通过。

## Compatibility

- 兼容承诺从 Python 3.9 起；不扩张到 3.8，不改变外部 CLI 协议或 task state schema。
- 不将 `/usr/bin/python3` 写入 payload。该路径只作为本机 executor 事实和验收测试入口。
- 不混入逻辑时钟、planning refresh 或 delivery manifest 修复；它们将在本任务 accepted merge 后以独立 gate-repair 尝试完成。

## Security And Data

- TOML compat 仅处理 task 已声明的配置文件；不读取凭据、session 或生产配置。
- 失败不吞错、不写半状态，不将内部错误伪装为 filesystem 事实。

## Migration

- accepted merge 后，O4 仍保持暂停；trusted main 从该 merge SHA 新建 GKD-GATE-REPAIR-R6。

## Public Interfaces

- 保留既有 CLI、task state 和 TOML 消费接口；compatibility facade 是 payload 内部实现。

## Execution Route

- trusted main 在 accepted execution bundle 上 bootstrap、approve、authorize、offer、prepare 和 claim。
- executor 在隔离 candidate worktree 完成实现、Python 3.9/开发解释器验证、evidence、PR 与 fixed-head delivery；不得验收、合并或收尾。
- independent acceptor 以完整 SHA、相对 `.gkd/policy.json`、Python 3.9 full verifier 和 fixed-head CI 审查；通过后由 trusted main narrow merge 和归档。

## External Side Effects

- 允许隔离 worktree、task branch、PR、runtime 与 evidence；禁止生产、AIO、settings、Secrets、runner、tag/Release 写入。

## Action Mode

`implement_and_merge_on_acceptance`

## Implementation Notes

- 先在系统 Python 3.9 重现，再完成枚举范围的最小兼容改动；生成 package/lock 后双解释器复验。
- 保持任务 state 旧 validator 可读，delivery 后停止；拒绝时只走 canonical rework。accepted merge 成为 `GKD-GATE-REPAIR-R6` 的唯一新基线；O4 仍暂停，直到 R6 独立通过。
