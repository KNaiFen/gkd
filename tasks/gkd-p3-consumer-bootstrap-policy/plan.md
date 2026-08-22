# GKD Consumer Bootstrap Policy Binding Plan

## Goal

让首个尚未跟踪 `.gkd/policy.json` 的消费项目，能够由 trusted main 提供严格、固定的 policy package，并在不手写候选文件、不伪造 claim 的前提下进入现有 automatic executor 流程。

## User Decisions

- 用户于 2026-08-23 明确授权修复此 GKD 流程、更新并安装新版本，然后继续 AIO adoption。
- 设计采用受限 bootstrap policy：输入只能是 schema-valid `policy.json`，由 GKD CLI 复制并绑定；不开放任意预写候选文件的通道。
- automatic route 仍只允许 exact `gkd_executor`、trusted-main bridge、六门 route decision 和既有一小时等待合同；不得采用 generic worker、角色替换、模型降级或公开 claim。
- action mode 为 `implement_and_merge_on_acceptance`；本任务的 GKD release/production migration 与后续 AIO 继续必须使用新 fixed head 的独立验证事实。

## Behavior And Defaults

- 若 candidate base 已有 `.gkd/policy.json`，bootstrap 读取、canonical-verify 并绑定它；此时提供 bootstrap policy input 必须拒绝，绝不覆盖。
- 若 base 缺少 policy，bootstrap 仅接受 planning package root 内的 regular `policy.json`，并用现有 CI policy parser 验证 repository/base branch 后写入 candidate `.gkd/policy.json`。
- 新 state/inventory 明确 versioned policy binding；旧 state/inventory 仅保留读取与 historical doctor，不获得 automatic-route 权限。
- project-stage 只在 trusted project root 写 machine-local stage 文件；candidate worktree 从不作为 stage target。

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

## Compatibility

- 已有 GKD/消费项目的 tracked policy 继续采用现有 schema version 1；它们无需新增 bootstrap input。
- task state 与 project inventory 的旧版本不能被自动升级或重写；只允许历史读取，新的 automatic bridge 要求 policy-bound version。

## Security And Data

- policy input 必须是固定 package 内的常规文件，拒绝 symlink、路径逃逸、额外资产、非 canonical 内容和不匹配身份。
- task state、project inventory、bridge context 和 acceptance 输出只携带 policy digest 与公开 repository/base facts，不携带 capability、host identity、session transcript、凭据或本机绝对路径。
- 任一验证失败在写入前终止；事务异常保持 candidate tracked 面与 runtime preimage 可恢复。

## Migration

- 无需迁移既有 task/inventory；新 bootstrap 自动生成新 binding，旧记录保持 historical-compatible。
- AIO 当前 blocked task 在新 bundle release/install/verify 成功后，从 fresh main 和新的 policy package 重新 bootstrap，不复用旧 offer/claim。

## Public Interfaces

- `gkd-task bootstrap` 增加受限 bootstrap policy input；task state schema 增加 immutable policy binding。
- `gkd-role project-stage` 增加 planning package policy input；`project-verify` 输出并校验 policy digest、repository 和 base branch。
- `TrustedMainRuntimeBridge.prepare` 接受已验证 project facts，并以 task binding 做 pre-write equality gate。

## Execution Route

- automatic route。trusted main 从干净 staged GKD project 取得 exact role/config/project verification 与 six-gate decision，再通过 trusted bridge 启动唯一 exact `gkd_executor`；执行者只修改注册 candidate、交付 fixed head 并停止。

## External Side Effects

- 允许 GKD task branch/PR、必要标准 GitHub Actions CI、无阻塞 acceptance merge、patch Release 与已验证的新 bundle production migration。
- 不允许 AIO 写入，直到新 bundle production doctor 通过且 AIO task 从 fresh state 重新启动。

## Action Mode

- `implement_and_merge_on_acceptance`；executor 可 commit、push、更新 PR、修复范围内 CI 并 ready for review。trusted main 仅在 fixed-head acceptance 后 conditional merge。

## Implementation Notes

1. 复用 `gkd_ci.policy` 的 canonical parser/digest，避免新增第二套 policy 解析或自由 JSON copy。
2. 将 policy binding 放入 task state/inventory 的版本化结构，由现有 transaction/CAS 写入；所有 reader 明确区分 legacy 与 policy-bound state。
3. bootstrap 与 project-stage 分别从相同 planning package 读取同一 input，写入前验证 identity；bridge 只接受 project-verify 的结构化输出。
4. 覆盖 bootstrap、stage/verify、bridge 和 acceptance 的 mutation/preimage tests，再运行完整 versioned verifier 与双 evidence。
5. delivery document 先提交，随后执行唯一 final delivery transition；trusted main 监控同一 PR head 并独立验收。
