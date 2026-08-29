# GKD Python 3.9 Compatibility R2 Acceptance

## Outcome

`accepted`；PR #43 fixed head `4215f394aaef3a05611aaad2470a30348bf76a0b` 已由独立 `gkd_acceptor` 通过 narrow acceptance，并 squash merge 为 `360ba876c83bed4c2b4fcea98a172eefe94838a5`。

## Evidence

- Review digest：`4c307fce535b614742c46a058fc2df9213271eac33d58484c7fa65467a248526`。
- Fixed-head CI：`success / ALL_REQUIRED_CHECKS_SUCCESSFUL`，`GKD Verify` 精确观测 `4215f394…`，policy digest `d77e68152843dcc1f470d88c76fe8c249ef803854048f4a9d42ed5cc92cd54c2`。
- Python 3.9.6 与 3.14.6 均通过 11 scopes、439 项完整 verifier；bundle、project stage/verify、native probe 与 fresh bridge claim-to-deliver 均通过。
- TOML facade、Tomli 2.0.1 MIT 许可、manifest/lock、CLI `INTERNAL_ERROR` 分类以及 receipt drift fail-closed 合同均通过。

## Scope Check

实现只触及 Python 3.9 兼容、测试、manifest/lock、许可与文档；未修改逻辑时钟、planning refresh、delivery sidecar、state schema、生产、AIO、settings、Secrets、runner、tag、Release 或已发布资产。

## Decision

Python 3.9 成为 executor 的最低支持版本。该 accepted merge 是新建 `GKD-GATE-REPAIR-R6` 的唯一基线；O4 继续等待 R6 完成。
