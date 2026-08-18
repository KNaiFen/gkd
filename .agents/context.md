# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: `GKD-M1-A` 首个delivery head `c35ac55fd299196a463bc31e8ff0f98ef37c3858` 的独立验收未通过且未合并；原execution session已修复外部claim receipt、runtime/tracked事务顺序、完整生命周期/历史不变量和显式symlink candidate四项阻塞。implementation/evidence commit 为 `fee072bf6849d87ffd6a6323ea75a81af3504831`，候选 outcome 仍仅为 `deterministic_task_core_ready`，等待 PR #5 新 fixed head 的再次独立验收。development version 仍为 `0.0.0-dev.0`，content digest 为 `17e51babe52b18695abf270d7359b8c9ff343e017caf379a3274cb3f1e470aff`，evidence digest 为 `98079835befaefe7eae74b5becfcbeb0eb5b559abcde3223171072ba7dd7377b`；103项task-core、53项foundation、47项watcher core和15项watcher live-negative通过。GitHub仍无configured checks或main branch protection，必须记为bootstrap缺口而非CI成功。旧 D2外部watcher路线保持历史`unsupported`；连续一小时 `wait_agent` 尚未通过fresh runtime实际门禁，因此auto route继续禁用。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
