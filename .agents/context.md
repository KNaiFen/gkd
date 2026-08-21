# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Active task: `GKD-M3-A`，从当前 fresh main 按正式 automatic bridge 开始注册和执行。
- Current state: `GKD-M3-A` 已在 epoch 4 exact claim 下同步 trusted main `d669c11735f1468127ce4b7b4699a19ef0984753` 并解决 PR #8 冲突。通用 `.gkd` policy、repo/policy/origin 一致性、GitHub fixed-head terminal monitor、标准 Actions/verifier 候选通过 362 项版本化本地验证；29 项 M3-A 双 evidence 逐字节一致。candidate output bundle/evidence digest 为 `22b935b0ec7ad1fb1da9222c5b30c4586fa1c55a68ec23f782928a5635e01120` / `2bee04f714db90808587986b13be38df42d041aa36efc3e3889c53c73fea5b58`，accepted execution bundle `1983f05b64860510bfb1af661e5458a6c7b660632479a33af46c27d35ff188d4` 保持不变。等待 implementation/evidence commit、M2-J delivery sequencing、fixed-head CI 与 trusted-main 独立验收；M3-B/M3-C、生产安装、AIO、付费 runner、Secrets 和计划外 GitHub 设置继续未授权。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
