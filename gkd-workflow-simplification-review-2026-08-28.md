# GKD 工作流精简审查报告

**审查日期：** 2026-08-28
**审查性质：** 只读审查，未修改 GKD 实现、bundle、生产目录或 AIO。

## 结论先行

当前 GKD 的核心闭环已经成立，但发行包和默认验证路径同时承载了三类不同东西：

1. 长任务控制的核心机制；
2. 发布、兼容迁移和历史恢复所需的机制；
3. CI 建议、跨仓库 review、外部 watcher、演练 fixture 和历史证据等可选或开发专用内容。

第三类内容是本次精简的主要目标。最有效的方案不是删除所有“看起来复杂”的代码，而是把默认核心收窄，再把可选能力、兼容能力和历史验证移到独立 lane。这样可以保留用户控制、恢复、固定证据、可移植性和自验证发布等需求，同时减少默认上下文、安装面和每次 PR 的执行成本。

### 最重要的建议

- **立即清理候选：** 5 个确认无调用的函数；它们不影响当前 CLI 和核心库行为。
- **优先拆出默认路径：** 外部 watcher/probes 的 47 项默认验证、4 个运行时 fixture、`gkd-optimize-ci` 与 `gkd-review-remediation` 的默认 Skill 注入。
- **优先合并验证：** `gkd-verify` 与各 `run_contracts.py` 的重复执行、delivery contract 对 task-core 的 9 项重复、watchdog 的多重 contract 映射。
- **暂不删除：** task 状态机、CAS/journal、固定 head acceptance、`gkd-ci-monitor`、生产迁移、release self-verification、legacy migration 的读取/拒绝路径、`sitecustomize.py`/`usercustomize.py`。
- **文档层需要清理：** `.agents/context.md` 存在过期状态与重复的 AIO C 条目，会制造比代码更大的上下文噪声。

## 审查范围与当前基线

审查对象包括 canonical source、payload、CLI、schemas、Skills、默认验证入口、`src/` watcher、`probes/`、tests、evidence、tasks 和当前持久记录。

当前基线事实：

- 当前 HEAD 为 `efa2d378fe4736663e192058cc0a0b33ebf896eb`，工作树在审查开始时干净；该提交只记录 2026-08-28 的子代理回收策略修正。
- `canonical/source.toml` 声明 24 个 component、101 个 payload 文件；其中 48 个 Python library 文件、24 个 schema 文件、14 个 Skill 文件。
- `scripts/gkd-verify` 默认执行 11 个 scope（`scripts/gkd-verify:25-36,94-130`），包括 `watchdog-core-and-live-negative`。
- payload library 约 12,914 行，tests 约 13,425 行；`src/` 与 probes 约 4,204 行。后两者不进入 canonical manifest，但会影响默认验证和开发上下文。
- 2026-08-28 已停用无条件 `SubagentStop` mailbox-drain hook；该配置在 GKD bundle 之外，不能再复制一份到 GKD（`.agents/context.md:3`、`.agents/decisions.md:3-5`）。

核心判定依据是 `VISION.md` 的使命和成功标准：用户控制、可恢复长任务、固定证据、可移植性、资源保护和发行物自验证（`VISION.md:3-17`）。不满足这些目标的内容，应优先从默认 bundle 或默认验证 lane 移出。

## Findings

### S0: 默认验证重复执行完整 scope

**证据：** `scripts/gkd-verify` 对 11 个 scope 逐一启动自身的 `--scope-internal`（`scripts/gkd-verify:25-36,94-130`）；各 scope 的 `run_contracts.py` 又重新 discover 并执行同一测试目录，例如 task-core（`tests/task_core/run_contracts.py:88-101`）、role-routing（`tests/role_routing/run_contracts.py:206-213`）和 release-candidate（`tests/release_candidate/run_contracts.py:45-55`）。

**问题：** 目前一次本地验证和一次 evidence 生成可能重复执行同一行为断言。重复运行确实再次检查了临时目录、protected surface、digest 和 evidence 写入，但没有新增同等比例的行为覆盖。

**建议：** 保留一个 canonical scope runner，输出固定 head、test IDs、结果和环境摘要；evidence runner 只消费该结果并补充自身的边界快照。若必须重新执行，应明确标注为不同 evidence lane，而不是默认重复。

**风险与边界：** 不能简单删除 evidence runner 的 protected/temporary/output 校验；应先把这些校验拆成独立 wrapper，再让测试结果复用。

### S0: 外部 watcher 已不是当前核心，却仍在默认验证链

**证据：** `src/gkd_watchdog/`、`scripts/gkd-watchdog-mcp` 和 `probes/app-server-watcher/` 服务于 M-1 外部 app-server/MCP watcher；它们不在 `canonical/source.toml`。但 `scripts/gkd-verify:32-36` 仍默认执行 `tests/watchdog`，该 scope 会加载 `src/gkd_watchdog` 和 live-negative probe。M-1C 的最终结论是 `unsupported`，当前 automatic route 依赖 project-scoped bridge、host acknowledgement 和一小时 wait gate，而不是外部 watcher（`.agents/decisions.md:87-93,371-377`）。

**问题：** 47 项 watcher 合同和相关 probe 继续增加每个 GKD PR 的时间、导入面和跨平台失败面，却不保护当前发行 bundle 的运行时功能。

**建议：** 将 watcher/probe/test 移到 `historical-watcher` 或 `host-capability` 专用验证 lane；默认 `gkd-verify` 只保留当前 role/wait/bridge 合同。历史 evidence 保留，发布候选时按版本升级或平台能力变更重新运行。

**不能做的事：** 不要删除历史 evidence 或改写 M-1C 的 `unsupported`；删除的是默认执行路径，不是事实记录。

### S1: 运行时 bundle 打包了只供测试/演练读取的 fixture

**证据：** `canonical/source.toml:45-60,123-128` 把 `release/traceability.json`、`release/trusted-main-evaluation.json`、`review/multi-repository.json` 和 `finalization/generic-input.json` 纳入 manifest。代码运行时并不自动读取这些文件，主要由 tests 读取（例如 `tests/release_candidate/test_traceability.py:13-15`、`tests/release_candidate/run_contracts.py:57-69`）。四个 fixture 合计约 8 KB，体积不大，但它们把开发输入和消费安装面混在一起。

**建议：** 做 dev/test fixture split：

- production/core bundle 只携带 schema 和运行时逻辑；
- release-verification bundle 或仓库 tests 携带 fixture；
- manifest、lock、fixture digest 和 release traceability 同步调整。

**风险：** 不能直接从 `source.toml` 删除文件而不改变 manifest/lock 和 release contract；应先增加“fixture 不在 runtime 安装面”的版本化契约。

### S1: executor 默认加载了两个非执行必需 Skill

**证据：** `canonical/payload/config/role-routing.json` 为 `gkd_executor` 默认启用 `gkd-optimize-ci` 和 `gkd-review-remediation`，同时启用 `gkd-ci-monitor`、`gkd-execute`、`gkd-local-verify`。这会把 CI 资源建议、价格事实、review remediation 等上下文带入每个实现任务；相同两个 Skill 也构成 `gkd_ci_reviewer` 的主要能力。

**问题：** 实现任务的最小必需集合是 `gkd-execute`、`gkd-local-verify`、必要时的 `gkd-ci-monitor`。CI 优化和 review remediation 是用户工作流的可选判断面，不是每个 executor 都需要的固定上下文。

**建议：** 默认 executor 只注入核心三项；在 route decision 明确需要时再按需 stage optional Skill。保留两个 Skill 和其 CLI，但从默认角色上下文和 core bundle 移出。

**风险：** 角色 digest、context manifest、production migration 和 manifest 都会变化，必须作为新 bundle 版本处理，不能编辑已发布资产。

### S1: 资源建议/scanner/review adapter 应拆为 optional packs

**证据：** resource scanner 包含独立 CLI、4 个 library 文件和 CI schemas；review 包含 CLI、adapter/core/remediation、4 个 schemas 和 fixture（`canonical/source.toml:35-80,83-98`）。它们的能力是分类、价格/runner 建议、diff/PR/artifact scan、多仓库 review 和 remediation，不参与 task claim、delivery 或 fixed-head merge。

**建议的拆分：**

| Pack | 保留内容 | 默认状态 |
|---|---|---|
| Core task | foundation、task、role/wait/bridge、fixed-head CI monitor、核心 5 个 Skill | 默认安装 |
| CI advice | resource class/preset、recommendations、scanner、`gkd-optimize-ci`、`gkd_ci_reviewer` | 按需安装 |
| Review | review core、remediation、multi-repository adapter、`gkd-review-remediation` | 按需安装 |
| Compatibility | legacy migration、旧 schema read/reject、生产迁移辅助 | 版本升级 lane |
| Historical verification | watcher/probes、旧 evidence runner、live capability fixtures | 发布/平台变更 lane |

这样保留用户要求的推荐和审查能力，但不让它们成为所有任务的固定成本。

### S1: 5 个 payload 函数确认无调用

以下函数在全仓搜索中只有定义，没有 CLI、library export 或其他调用：

| 函数 | 文件 | 建议 |
|---|---|---|
| `fixed_tree_paths` | `canonical/payload/lib/gkd_task/gitops.py:262-269` | 移除；若视为外部 Python API，先标记弃用 |
| `make_legacy_v1` | `canonical/payload/lib/gkd_task/migration.py:39-50` | 移到 tests helper；保留 `validate_legacy_v1`/`migrate_v1` |
| `scanner_result_digest` | `canonical/payload/lib/gkd_ci/scanner.py:175-177` | 移除或移到 tests；scanner 主入口不变 |
| `canonical_adapter` | `canonical/payload/lib/gkd_review/adapter.py:91-94` | 移除或移到 tests；保留 `build_adapter`/`validate_adapter` |
| `canonical_resource_plan` | `canonical/payload/lib/gkd_ci/resources.py:232-236` | 移除或移到 tests |

这些是高置信、低行为风险的清理候选，但仍应在新变更中运行完整 core verifier，并确认没有外部 Python 调用者。

### S2: delivery contract 重复 task-core 的 9 项测试

**证据：** `tests/delivery_contract/run_contracts.py:21-30` 固定列出 9 个测试，其中全部来自 `tests.task_core.test_lifecycle`、`test_acceptance` 和 `test_mutations`；而 `scripts/gkd-verify` 已执行整个 task-core scope。

**建议：** 把 M2-J 的 runner 改成消费 task-core 的已生成结果，只保留 delivery-document binding 特有的 head/环境快照。若暂时无法共享结果，至少把 9 项标成同一 test ID 的二次 evidence，不要维护第二份 contract 列表。

### S2: watchdog contract 映射重复，不等于需要重复测试

**证据：** `tests/watchdog/run_contracts.py:22-103` 把同一测试映射到多个合同，例如 EOF shutdown、system-error interrupt、wrong expected turn 和 credential rejection。

**建议：** 保留行为测试，但生成唯一 `test ID -> contract IDs` 反向索引；证据按 contract 展开时引用同一测试结果。这样不减少语义覆盖，却降低维护和审计成本。

### S2: 安装 mode 测试可参数化，避免重复实现

**证据：** `tests/foundation/test_install.py:73-126` 中 `test_verify_detects_mode_drift` 与 `test_verify_detects_every_metadata_mode_mutation` 共享同一 verify 边界；可以用参数化/subTest 覆盖可执行文件和 metadata 文件。`test_manifest.py:113-122` 的 source generation mode 是另一边界，不能合并删除。

**建议：** 合并测试表达，不删除 mode 反例。

### S1: 历史兼容测试应降频，不应从产品承诺中删除

**证据：** role schema v1-v4、legacy delivery、legacy role ambiguity、historical doctor/migration 和旧 reviewer role 删除测试分散在 role/task/production scopes（例如 `tests/role_routing/test_packaging.py:92-96`、`tests/task_core/test_acceptance.py:84-100`、`tests/production_migration/test_production_migration.py:48-113`）。

**建议：** core PR 每种公开旧格式只保留一个 read、一个 reject/restore 正例；完整历史矩阵移到 release-upgrade lane。生产迁移、旧 schema 解析和 legacy delivery 的最小兼容承诺仍要保留，不能因为“当前用户已迁移”就删除。

### S1: `gkd-finalize` 与 `gkd-release` 存在可合并面，但暂不能判定为死代码

两者都处理 SHA、digest、provenance 和 promotion request，但职责不同：

- `gkd-finalize` 处理 closeout-only 与 release intent 的通用最终化记录（`canonical/payload/lib/gkd_finalization/core.py:175-220,302-331`）；
- `gkd-release` 处理 L0-L4、L3/L4、sandbox canary 和 post-merge promotion（`canonical/payload/lib/gkd_release/core.py:124-153,199-265`）。

建议下一版将它们统一为一个 release/closeout engine、保留两个兼容 CLI alias，或明确两个 engine 的输入/输出边界。当前不建议直接删除任一模块，否则会破坏 M4/M5 的可追溯发布能力。

### S2: 持久上下文有重复和矛盾，属于高收益文档清理

**证据：** `.agents/context.md:7` 在描述 `v0.1.1` 后仍写“生产目录和 AIO 仍未写入”，但 `.agents/context.md:10` 已记录 P1 production apply/doctor healthy；`.agents/context.md:19-20` 对 AIO C final 重复记录同一内容。

**影响：** 新 Session 读取 context 时无法立即判断哪些是当前事实、哪些是历史快照，容易重复调查或错误地把已完成动作当作未授权。

**建议：** context 只保留一条当前状态和一条 next task；版本、失败尝试、完整 digest 和历史清理放到 decisions/open-items/task records。此次子代理回收修正只保留为 host-level fact，不在 GKD bundle 增加镜像配置。

## 明确不应删除的核心边界

以下内容虽有兼容或防御代码，但直接删除会破坏现行需求：

- `gkd_task` 的 planning/authorization、offer/claim、CAS/journal、runtime、delivery、rework、acceptance；它们是“可控且可恢复长任务”的核心状态机。
- `gkd_role` 的 route/wait/bridge、`gkd_executor` 与 `gkd_acceptor`、项目 staging 和 bundle digest 绑定；它们是当前 automatic bridge 的最小闭环。
- `gkd-ci-monitor`、`.gkd/policy.json` 绑定、完整 history checkout 和 exact PR/head 检查；它们是固定 head 验收的核心，而不是普通 CI 装饰。
- `gkd-role production-migration-*` 及 recovery/doctor；当前生产安装已依赖受管 roles/Skills/config 的可恢复事务。
- `gkd-task migrate-v1`、legacy schema read/reject 和旧 role 删除检查；它们是已发布版本升级的兼容入口。若未来 major version 明确放弃旧格式，再单独做迁移策略。
- `sitecustomize.py` 与 `usercustomize.py`；前者禁用 bytecode，后者清理启动前缓存，测试分别覆盖不同启动阶段，不能按“两个同名文件”删除一个。
- 双层 GitHub adapter：`SubprocessGitHubAdapter` 是 trusted task 到安装 adapter 的边界，`GitHubAcceptanceAdapter` 是实际 REST 实现，职责并非重复。
- manifest、manifest.lock、schemas 和 final evidence；它们是可安装、自验证和固定事实的组成部分，不能只因生成文件重复 source 声明而删除。

## 建议的最小核心形态

建议把默认发行物收敛为以下闭环：

```text
foundation
  -> task state + authorization + offer/claim + delivery/rework
  -> role routing + trusted bridge + one-hour wait
  -> fixed-head CI monitor + independent acceptor
  -> finalization/release self-verification
```

默认 Skill 只保留：

```text
gkd-main, gkd-execute, gkd-local-verify, gkd-ci-monitor, gkd-accept
```

按需能力通过独立 pack 提供：

```text
gkd-optimize-ci, gkd-review-remediation, resource-scanner, review adapter,
legacy migration matrix, historical watcher/probes
```

这不是要求立即重写或删包，而是一个可以保持 digest/版本纪律的目标形态。每次拆分都应生成新 bundle、更新 manifest/lock、运行 core verifier，并从已发布资产建立隔离 restage。

## 实施顺序建议

1. **先做无行为变化的清理：** 删除/移出 5 个无调用函数；合并 foundation mode 测试表达；清理 context 重复和矛盾。
2. **再改验证执行模型：** 让 `gkd-verify` 与 evidence runner 共享一次 scope 结果；delivery contract 消费 task-core 结果；watchdog 改为历史 lane。
3. **然后拆 optional pack：** 将资源建议、scanner、review/remediation 和多仓库 fixture 从默认 executor/context 移出。
4. **最后评估兼容策略：** 将 legacy migration 和旧 schema 矩阵降频；在明确 major-version 放弃承诺前，不删除读取/拒绝/恢复入口。
5. **每一步独立发布和验证：** 不在同一变更中同时做行为修改、拆包和历史清理；失败时保留 exact head 和 terminal fact，不沿旧 head 洗绿。

## 审查结论

GKD 当前不是“核心功能太多”，而是核心、兼容、历史和可选建议共用一个默认安装/验证边界。最小且保守的精简路线是：

- 保留任务状态机、角色桥、等待、固定 head、release self-verification 和生产恢复面；
- 把 watcher、fixtures、资源建议、review/remediation 和历史兼容矩阵改为按需或低频 lane；
- 先消除重复执行和无调用函数，再做 bundle 拆分；
- 不把最近修复的 host-level 子代理回收策略复制进 GKD。

在完成这些拆分前，当前实现仍应视为功能正确但默认上下文和验证成本偏高；不建议直接从已发布 `v0.1.5` 资产删除文件或修改 manifest。

## 可复核材料

- [VISION.md](/Users/knaifen/Documents/Codex/gkd/VISION.md:3)
- [canonical/source.toml](/Users/knaifen/Documents/Codex/gkd/canonical/source.toml:1)
- [canonical/README.md](/Users/knaifen/Documents/Codex/gkd/canonical/README.md:25)
- [scripts/gkd-verify](/Users/knaifen/Documents/Codex/gkd/scripts/gkd-verify:25)
- [.agents/context.md](/Users/knaifen/Documents/Codex/gkd/.agents/context.md:3)
- [.agents/decisions.md](/Users/knaifen/Documents/Codex/gkd/.agents/decisions.md:3)
- [.agents/open-items.md](/Users/knaifen/Documents/Codex/gkd/.agents/open-items.md:3)
