# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: 里程碑 1、M2-A 与 M2-B 门禁已完成；M2-B 继续绑定历史执行 bundle `5b115a918d8a5241551b0be8dac657a448e1b912815493e1988007b1f4ed1880`。`GKD-M2-C` 已在一次性 bootstrap exception 下形成 `automatic_runtime_bridge_ready` 候选：implementation/evidence commit `958a313f48ea7fd5d190dfa5b200230d81d29fd4`，candidate output bundle `2d8117b5ac8ecf9d30fa578424d208ff7795192a3396eb653ee641376955116a`，evidence digest `5ffe2feef2646b39f5bf293e2365fcbf509fd5518d9a5885250716d1b9814e0e`。project-scoped staging、六门 decision、exact spawn→activation→claim/recovery 与执行/输出 bundle 分离均有正向、负向、恢复和 mutation 合同；PR #7 等待 fixed-head 独立验收。验收前不得把 candidate output 当作 accepted runtime upgrade，不得启动 fresh main 或 M3。M3 已拆为 A fixed-head CI/policy、B 资源与防泄漏 core、C 两项新 Skill/review core。生产安装、AIO、付费 runner、Secrets 和计划外 GitHub 设置继续未授权。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
