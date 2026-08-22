# GKD Consumer Bootstrap Policy Binding

## Goal

让首个尚未跟踪 `.gkd/policy.json` 的消费项目，能够由 trusted main 提供严格、固定的 policy package，并在不手写候选文件、不伪造 claim 的前提下进入现有 automatic executor 流程。

## User Decisions

- 用户于 2026-08-23 明确授权修复此 GKD 流程、更新并安装新版本，然后继续 AIO adoption。
- 设计采用受限 bootstrap policy：输入只能是 schema-valid `policy.json`，由 GKD CLI 复制并绑定；不开放任意预写候选文件的通道。
- automatic route 仍只允许 exact `gkd_executor`、trusted-main bridge、六门 route decision 和既有一小时等待合同；不得采用 generic worker、角色替换、模型降级或公开 claim。
- action mode 为 `implement_and_merge_on_acceptance`；本任务的 GKD release/production migration 与后续 AIO 继续必须使用新 fixed head 的独立验证事实。

## Scope

- 扩展 `gkd-task bootstrap`，使其能从规划 package 的受限 policy 输入建立 candidate `.gkd/policy.json`，并在新 task state 中不可变绑定 policy digest、repository 与 base branch。
- 扩展 `gkd-role project-stage/project-verify`，让首个项目使用同一 package policy 进行 machine-local stage/verify，inventory 绑定 policy digest 与 repository/base branch。
- 扩展 trusted-main automatic bridge 与 fixed-head acceptance，使 project verification、task binding、claim 与 candidate policy 必须相同；不匹配时在写入前拒绝。
- 增加严格 schema、transaction、bridge、acceptance 和 backward-read regression tests；更新必要的 GKD 文档与 release version。

## Non-Goals

- 不为任意文件、脚本、角色配置或项目代码增加 bootstrap copy 入口。
- 不修改 AIO、生产 `~/.codex`、GitHub settings、Secrets、付费 runner 或现有 AIO CI/release 行为。
- 不放宽 public automatic CLI、candidate claim、capability、receipt 或 trusted activation 边界。
- 不迁移、重写或补造既有 task state、offer、claim、receipt、delivery 或历史证据。

## Acceptance Criteria

- [ ] P3-01：bootstrap package 的 policy 缺失、symlink、非 canonical JSON、repository/base branch 不匹配，或 base 已有 policy 时使用 bootstrap input，均在 candidate/ runtime 写入前失败。
- [ ] P3-02：合法首个项目 policy 仅由 `gkd-task bootstrap` 写入 candidate 初始提交；task state v3 绑定 policy path/digest/repository/base branch，候选 policy drift 被 doctor/bridge/acceptance 拒绝。
- [ ] P3-03：project stage/verify 对已有 tracked policy 和 bootstrap package policy 都可验证；inventory 绑定 policy digest 与 identity，pre-existing conflict、symlink、mode/content/origin/base drift fail-closed。
- [ ] P3-04：automatic bridge 在 offer 写入前比较 verified project、bundle、role/config、task policy、repository/base branch；任一错配不产生 tracked 或 runtime 副作用。
- [ ] P3-05：fixed-head acceptance 对 claim base、claim commit、delivery 与 candidate head 的 policy binding 复核；任何漂移拒绝，正常 policy-bound automatic path 通过。
- [ ] P3-06：既有 v1/v2 state 保持可读/历史 doctor；它们不能冒充新的 policy-bound automatic task。
- [ ] P3-07：GKD versioned verifier、双 evidence、fixed-head CI、独立 acceptance，以及 post-merge patch release/production doctor 全部绑定新版本的同一 source SHA。
