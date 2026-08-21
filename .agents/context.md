# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Active task: `GKD-M5-A`，从 M4-A 合并后的 fresh main 按正式 automatic bridge 开始注册和执行。
- Current state: M3 已完成；`GKD-M4-A` fixed head `2b9dbfe5aa8003926eed2ef89e562e245859cdf0` 已独立验收并由 PR #19 squash merge 为 `44e413937df8e05045d907af2630185bc4fb9bcc`。M4 candidate bundle/evidence digest 为 `27470fc60cfa005a2784ac81f0aba07c4e50e2381bf057fe9b38aa8d016e1912` / `90e499d761517a65080eb46edcab588b07d275267d38c609274a6dab3e287170`，evidence file SHA-256 为 `09c91349e0d0e4c836e93ef95367517b8383f5b0272463cf6da9ccb82d685bf6`；399 项 verifier、9 项双 evidence 与 policy-backed `GKD Verify` fixed-head monitor 均通过。当前 accepted execution bundle 为 `27470fc60cfa005a2784ac81f0aba07c4e50e2381bf057fe9b38aa8d016e1912`，已隔离安装并刷新 project staging，role/config/project-config/inventory digest 为 `b7660cee9bdab5b1011ae9e92a2a817536f508ef1475a10cc53acd9a1d99c25b`、`d44d2286d0a01a7b0f82610c02a6ada9fb1dc74f05730b1e8629f784d68595d2`、`9a9bc7db827ea68cf4ba6761902e91ce4982fbaec25b8d68b70c4c790cef35d0`、`b0bd7e7090f1d4fd5886c305d087aa1b9e8caa754c84db3678c1c1cf3b183fc9`。当前 main 为 `44e413937df8e05045d907af2630185bc4fb9bcc`。M5 release candidate 可在全部 L0-L4、独立验收与 exact SHA promotion 后使用已授权的最终 tag/Release；生产安装与 AIO 继续排除。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
- M4 closeout: finalization/release mechanics 已验收合并且没有产生发布副作用；M5 负责完整验证与最终 release candidate。
