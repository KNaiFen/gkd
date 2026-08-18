# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: 里程碑 0 已由 `GKD-M0-A` 完成并记录终态验收；PR #4 fixed head `68c418aef398dd6c2a3576c330d744e5d351acfa` squash merge 为 `2207645ab7a3bfc4b0ad4a15cf4bbe743612933c`，development version `0.0.0-dev.0`，content digest `0b8b2487640ff2c78360a18e7f24304f72a8e8c8b5cbd1317ef833c323726228`。未定义的 M0-B 占位已撤销；清理任务 worktree/分支后，下一步规划里程碑 1 的 `GKD-M1-A`。D2 保持 `unsupported`，manual-only 继续生效。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
