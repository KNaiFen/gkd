# Context

- Goal: 建立可版本化、可安装、可专门验证的 GKD canonical distribution source。
- Current state: 里程碑 2 已完成。`GKD-M2-C` fixed head `b25637d8f0989427f9bfe0cc46e603ffd3c79550` 已通过独立验收并由 PR #7 squash merge 为 `b16349af24ae76055f86f3b02437168404b97ff8`；candidate/merge tree 均为 `1fca9da644148631b541dc61f58d670dd0917ceb`。accepted execution-bundle upgrade digest 为 `05288d5b09bdd8b4703a45d8a300d9466ad59f6b414d8eb5684c4a214ecfaaad`，提交 evidence digest 为 `ab6efbc3cded637edc1fd0acd155958a3949566d48282fa1c4bfa81b266bbb82`；M2-C 32 项在两个临时根和 fixed-head archive 各通过一次，104/70/53/47/15 项保留回归通过。仅限 M2-C 的 bootstrap exception 已终止；M3 及以后必须使用正式 project staging、exact `gkd_executor`、route decision、activation/claim bridge 和一小时 wait gate。当前 Session 启动时未发现 staged exact `gkd_executor`，因此 M3 仍 fail-closed，禁止 generic worker、角色替换、模型降级或 fallback。M3 已拆为 A fixed-head CI/policy、B 资源与防泄漏 core、C 两项新 Skill/review core。生产安装、AIO、付费 runner、Secrets 和计划外 GitHub 设置继续未授权。
- Constraints: 完整 GKD 测试只在开发 GKD 或形成 GKD release candidate 时运行；消费项目的普通产品代码和文档变更不运行该测试套件。
- Useful paths: 审查事实源位于 `/Users/knaifen/Documents/Codex/aio-coding-hub/main/.trellis/tasks/08-17-gkd-workflow-remediation/`。
