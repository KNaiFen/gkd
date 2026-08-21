# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Active task: `GKD-M3-A`，从当前 fresh main 按正式 automatic bridge 开始注册和执行。
- Current state: `GKD-M3-A` 已在 epoch 4 exact claim 下同步 trusted main `d669c11735f1468127ce4b7b4699a19ef0984753` 并解决 PR #8 冲突；首次 implementation head 的 GitHub CI 失败已按 M3-A 范围修复 Linux `/tmp` bundle contamination 与 retained migration path portability。修复候选通过 362 项版本化本地验证；29 项 M3-A 双 evidence 逐字节一致。candidate output bundle/evidence digest 为 `e49f6bf994a3dea405248535ffdd70473feacd13c27ae39a6ecfc1fabd9a7efd` / `a2ffc693a75780aa893538462bf6a1a2428f2d55d0c68d138b33f4a288cd1c5b`，evidence file SHA-256 为 `93b9e6b365f6fa832485183e0dcf83ab293e27804d5d087f1c438720474ba181`；accepted execution bundle `1983f05b64860510bfb1af661e5458a6c7b660632479a33af46c27d35ff188d4` 保持不变。等待 repair head 的 policy-backed fixed-head CI、M2-J delivery sequencing 与 trusted-main 独立验收；M3-B/M3-C、生产安装、AIO、付费 runner、Secrets 和计划外 GitHub 设置继续未授权。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
