# GKD 工作流执行复盘报告

**报告日期：** 2026-08-25
**分析范围：** Session `01a00f64-2b83-75d0-bb8b-ca156f0979f8` 起，至历史最新 Session `01a03986-b846-7242-8383-f801d16a3c60` 止；不包含当前会话。

## 结论摘要

这几天的执行结果总体符合原始方向，但实现形态比最初设想更严格、更保守：

- GKD 已从消费项目中的工作流实践，落成可版本化、可安装、可独立验证的 canonical bundle；`v0.1.0` 至 `v0.1.5` 均经过固定 SHA、独立 verifier、GitHub fixed-head 检查和发布资产验证。
- “人工先行、条件自动”已实现，但自动化不是普通的 `spawn`。它依赖受信主会话、已验收 bundle、精确角色、offer/claim、固定 head、等待门和单 writer；任何事实缺失都回到 manual-only 或 fail-closed。
- 用户控制、授权分层、失败不补造证据、消费项目只使用已发布资产等原则实际守住了；但平台线程配额回收、工具路由、跨平台契约和验收适配器曾多次造成真实停滞或错误动作。
- 报告写入前仓库 `main` 与 `origin/main` 同步，基线 HEAD 为 `546c6cff9fee5a21628b54f1dbdaace4cecc4db1`。生产 GKD 已由已发布资产完成迁移；AIO B4/C/D 已完成，但后续普通 AIO 改动仍需新的任务和授权。

## 分析方法与证据边界

Session 存储在 `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`。本次共覆盖 190 个 rollout 文件：

| 日期 | 文件数 | 主要阶段 |
|---|---:|---|
| 08-17 | 9 | 原流程复盘、GKD 计划与授权边界 |
| 08-18 | 42 | D2、canonical foundation、M0 |
| 08-19 | 16 | M1、M2-A 角色路由与可信握手 |
| 08-20 | 27 | M2-C 自动桥、M2-D/J/I-R |
| 08-21 | 9 | M3-A 与自动路线实战问题 |
| 08-22 | 21 | M3、M4、M5、P1/P2 |
| 08-23 | 20 | M2-K、R1-R6、v0.1.2-v0.1.4 |
| 08-24 | 26 | R7-R10、v0.1.5 |
| 08-25 | 20 | AIO B4/C/D 收尾 |

分析只提取真实用户消息和助手可见正文，排除了 `session_meta`、`turn_context`、工具调用、命令输出和加密 reasoning。起始 Session 的用户问题位于 `...01a00f64...jsonl:9-10`；历史最新 Session 的用户问题位于 `...01a03986...jsonl:9-10`。当前会话产生的 3 个新 rollout 文件未纳入。

项目事实以 `.agents/context.md`、`.agents/decisions.md`、`.agents/open-items.md` 和 Git 提交为准；Session 对话用于还原当时的意图、误判和实际阻碍，不用于替代最终验收记录。

## 原始工作流与实际结果

| 原始设想 | 实际实现 | 与原计划的差别 | 评价 |
|---|---|---|---|
| 用户先批准材料性方案，Agent 再执行外部动作 | GKD/AIO/生产授权拆开，生产目录、AIO、GitHub 设置各有独立边界 | 许可被拆得更细，不能从“批准 GKD”推导生产或 AIO 许可 | 按预期且更严格 |
| 前期人工，核心完成后切换专用 executor | M-1/M0/M1/M2 由人工顶层 Session 完成；M2-C 后才具备自动桥 | 自动路线必须绑定 host-observable facts，不能退化为普通 worker | 基本按预期 |
| 长任务以固定事实交接和恢复 | task state、offer/claim、CAS、journal、delivery、rework epoch 和 fixed-head acceptance 已实现 | 恢复从“会话延续”变为“状态机事务恢复” | 按预期，复杂度显著增加 |
| 健康等待静默，异常才返回 | 形成 3,600,000ms 一小时等待合同和 M2-B 记录 | 当前工具层暴露上限曾只有 360,000ms；不能用短轮询拼出一小时 | 合同完成，平台能力仍是边界 |
| 通用机制可移植，项目 policy 留在仓库 | `.gkd/policy.json`、显式 repository/full head、相对 policy 路径、版本化 verifier | 早期脚本写死仓库、检查名和绝对路径，后续被逐项修正 | 方向正确，回归面仍高 |
| 固定 head CI 通过后由 canonical acceptance 合并 | M3-A 至 R10 均采用 fixed-head monitor、独立 review、canonical merge | adapter self-test 越权 merge 的事故证明“单 writer”必须是硬权限边界 | 已实现，曾出现严重偏差 |
| 发布产物与 source SHA、L3/L4、sandbox canary 精确绑定 | `v0.1.0`-`v0.1.5` 资产、tag、Release、canary 均按 exact SHA 绑定 | M5/R1 期间曾混淆 source SHA、sandbox PR head 和宿主事实，后改为可观察事实合同 | 已实现 |
| AIO 只接入已发布并验证的 bundle | B4/C/D 均从已发布 `v0.1.5` asset 建立隔离 runtime | 每个失败 attempt 都关闭并重新建 epoch/head，不能沿旧 head 重试 | 按预期 |

## 按阶段复盘

### 1. 08-17：原流程问题被明确化

起始 Session 复盘了原 Trellis/AIO 流程：需求恢复、规划、worktree、CI、固定 head 验收、PR 和发布链条都存在，但控制面依赖聊天约定。用户当时指出的核心问题后来全部成为 GKD 的设计输入：

- 自动 worker 可能在未获授权时被启用；
- 默认子代理的模型和 effort 不可证明；
- 三分钟轮询和执行期播报污染上下文；
- 方案可能未经用户批准就直接施工；
- Skill、CI 脚本和路径存在仓库名、用户名或绝对路径假设；
- 失败后缺乏明确的恢复、归档和停止边界。

这一天形成了 `VISION.md`、GKD/AIO 分离、manual-first/conditional-auto、双 public 仓库、单 writer 和 fixed-head acceptance 等基础决定。它们不是事后包装，而是后续提交和任务状态机的直接来源。

### 2. 08-18：平台限制和 bootstrap 缺陷暴露

原定 D2 单次等待 12 小时，但 `codex-cli 0.147.0` 只接受最多 3,600,000ms。外部 watcher core 虽完成 hermetic 合同，真实 app-server live gate 无法稳定获得 parent/child/thread/turn 绑定，最终结论是 `unsupported`。因此路线从“外部 watcher 自动化”改为“人工顶层执行 + 条件自动”，不是把 unsupported 伪装成成功。

M0-A 首轮 fixed-head 验收发现三类未被原测试覆盖的缺陷：metadata mode 未绑定、evidence 输出改变 protected 快照顺序、跨机器污染扫描误杀。修复后才合并。这说明早期“已有测试全绿”并不能代表合同完整，反例验收比测试数量更重要。

### 3. 08-19：任务事务和角色可信边界成形

M1-A 至少经历两次 fixed-head 返工：candidate-only claim、runtime 写失败残留、phase 不变量、symlink 身份和 CAS 前 attachment 写入均在独立验收中被发现。最终以 task lock、CAS、journal、精确 receipt 和可重试恢复闭环。

M2-A 的角色握手是最典型的“平台事实误读”案例。`--ignore-user-config`、parent model override、strict-config 和不完整 stdout 先后造成模型拒绝、用户配置解析失败或看似没有 child。最终只接受真实 rollout 中唯一 `gkd_executor` spawn、child activity 和 parent/child terminal；M2-K 又把合同收窄到当前宿主真正可观察的 acknowledgement 和 attempt handle。缺少可绑定 terminal 时不得自动 reclaim。

### 4. 08-20 至 08-22：自动桥、CI、发布链完成但代价高

M2-C 解决了“正式 claim 依赖待实现 bridge，bridge 又需要 claim”的 bootstrap 死锁，因此使用一次性人工例外；该例外在合并后终止。桥接实现随后补齐 bundle 重验、symlink 拒绝、activation postimage 事务、receipt/claim 绑定和 in-flight bundle 替换检测。

M3-A/B/C、M4 和 M5 完成了 policy、monitor、资源事实、review core、finalization 和 release gate。过程中实际暴露了 Linux `/tmp` 与 macOS `/private/tmp` 差异、required-check 名称含空格、PID publication 竞态、Git teardown `ENOTEMPTY`、跨仓库 source/head 身份混淆，以及过宽的 traceability fixture。最终 `v0.1.0` 精确指向 `c14f166e...`，但这条结果是多轮反例修复后得到的，不能用首轮设计假设解释。

P1/P2 将生产迁移拆为受管 roles/Skills/config/recovery 和独立 global `AGENTS.md` policy。第一次生产 gate 返回 `MIGRATION_PRODUCTION_FORBIDDEN`，阻止了对运行中 Codex 状态的未验证覆盖；之后 `v0.1.1` apply/doctor 才在受管面完成。

### 5. 08-23 至 08-25：发布修复和 AIO adoption 实战

R1 因要求宿主无法提供的 fresh executor/child/effective runtime 字段被 R2 取代；R2 以 host-observable L3 发布 `v0.1.2`。R3/R4 绑定消费仓库 policy、origin、base branch 和 required checks，并发布 `v0.1.3`。R5/R6 修正 host resource 与 GitHub runner capacity 混淆并发布 `v0.1.4`。

R6 发生了最严重的动作边界事故：canonical `gkd-task accept` 返回 `INVALID_GITHUB_RESPONSE` 后，adapter self-test 错误调用 merge，实际合并了已经独立验证的 PR。项目保留该失败事实，拒绝倒填 acceptance 成功；R9 才修复 REST `merged/closed` 解析、stdout 尾换行、exact-head squash reconciliation 和 implementation -> delivery-document -> deliver 顺序，R10 发布 `v0.1.5`。

AIO B4/C/D 都证明了“失败 attempt 不沿旧 head 继续施工”的价值：

- B4：绝对 policy path、GitHub 查询失败、简写 repository，最终以 epoch 3、完整 repository、相对 policy 和唯一 3600 秒 monitor 成功；
- C：history smoke 初始漏掉删除路径，且首次 canonical accept 出现 `FILESYSTEM_ERROR`，两轮 rework 后完成；
- D：v1 的 lifecycle EOF/`ci-gate`、v2 的 stale selftest/required-check identity 歧义被关闭，v3 从新隔离 runtime 成功。

## 施工中出现的主要工作流缺陷

### A. 子代理和平台线程管理

早期主会话曾直接启用内置 worker，绕过独立 execution session；后续虽然改为固定 `gkd_executor`，但实战仍出现 20 分钟无活跃、`thread limit reached` 和长期 `awaiting_claim`。`followup_task` 只能消费邮箱或触发一轮，不能释放历史 completed/interrupted thread；当前平台缺少显式 close/reap 和配额查询接口。

这不是业务代码失败，而是编排基础设施缺陷。结果是自动桥合同已经成立，实际路线却无法稳定获得执行槽位，主会话被迫保留 manual-only。

### B. 工具路由和参数类型不够可证明

Session 中出现过把本地文件连接器错误放入 `functions.exec`、把等待上限设为平台拒绝的 12 小时、把 bridge request 传给 strict validator，以及把 direct spawn 错映射为 `functions.exec` 的情况。它们共同说明“工具名称在聊天中可见”不等于“参数已经通过机器级 schema 校验”。

### C. 生命周期状态机发现问题偏晚

`implementing`、writer、offer、claim、delivery、review、rework 和 receipt 之间的关系，最初依赖执行者遵守约定；后来才逐步加入 CAS、epoch、immutable requirements、delivery document 顺序和 exact-head 绑定。重复的 fixed-head 返工是必要的，但也说明关键不变量没有在 offer 前集中生成和验证。

### D. 可移植性合同仍靠事故驱动补齐

绝对路径、仓库简称、required-check 空格、EOF 空白、Linux 临时目录、PID 和 teardown 竞态均是在 CI 或 AIO 中才暴露。当前结果已经改善，但仍不能假设“macOS 本地 verifier 全绿”代表 GitHub-hosted Linux 可用。

### E. 安静等待合同与现有界面冲突

“健康时不输出、不分析、不查状态”是正确的控制策略，但当前 Session/工具层仍会把 wait 调用和 timeout 结果放入父上下文；它能减少自愿噪声，不能声称真正零上下文。更重要的是，实际工具上限不足时必须停止自动路线，而不是用多轮短等待冒充一小时。

### F. Bootstrap exception 有长期残留风险

M2-C、M2-K、R3/R4 等任务没有正式 claim/receipt，这是诚实的历史事实；但只要任务资料与正式 automatic lifecycle 混在一起，后续审查就容易误以为状态不完整。例外应有显式类型和终止标记，而不是靠每份 acceptance 文档解释“不适用”。

## 未尽如人意的计划功能

1. **自动路线的“可用”与“可启动”不是一回事。** M2-A/M2-B/M2-C 已提供合同、fake-clock 和 bridge，但真实宿主的线程配额和 child terminal 观察能力仍不足，因此自动执行无法持续复现。
2. **通用 acceptance adapter 的写权限曾过宽。** R6 事故证明 snapshot、自检和 merge 必须在接口层完全分离；靠文档要求“不要调用 merge”不够。
3. **CI policy 的显式化晚于实现。** M3-A 之前大量脚本内含仓库/检查名假设，导致同一机制跨仓库接入成本高；AIO B4/D 的失败表明 policy/origin/check identity 应在任务创建时冻结。
4. **发布 traceability 初版偏重字段齐全，轻实际合同。** M5-A/R1 的失败说明“矩阵完整”不能替代 L1/L2/L3/L4 的真实分层证据。
5. **AIO adoption 的失败反馈链仍较长。** B4/C/D 每次失败都正确停住，但从失败到新 epoch、隔离 runtime、相对 policy 和重新 monitor 的重复成本很高。

## 改进建议

### P0：先修平台和入口

- 为子代理提供显式 `close/reap`、thread quota 查询和失败原因；`followup_task` 不应被当作资源回收手段。
- 提供专用、结构化的 `spawn`/`wait` API，禁止通过通用 `functions.exec` 代理角色启动；启动前校验 role、model、effort、sandbox、bundle digest 和 task ID。
- 在运行时暴露真实单次 wait 上限；合同要求一小时就必须拒绝不满足上限的环境，禁止调用层自行拼接短等待。

### P1：把关键不变量前移到 offer 之前

- 生成并锁定 `decision -> offer -> envelope -> spawn request` 的规范化 JSON；bridge 只接受该对象，不接受自由形状的 request。
- 在 offer 前一次性验证 repository/full head、相对 policy、base branch、required checks、bundle/role/config digest、requirements EOF 和 clean worktree。
- 将 bootstrap exception 建模为独立 lifecycle 类型，自动禁止 claim/receipt 补造，并在合并后自动关闭例外。

### P1：把写权限收缩到单一 canonical writer

- acceptance adapter 只允许 snapshot/read；merge、tag、Release 和 delivery 只能由 canonical command 发起。
- self-test 使用 mock/snapshot，加入“调用 merge 即失败”的测试；所有失败 attempt 保留 terminal fact，不允许旧 head 洗绿。
- 对 implementation head、delivery-document head、PR head、merge head 建立不同字段名和类型，避免同一个 `head` 被跨阶段复用。

### P2：建立跨平台、跨仓库回归矩阵

- 最少覆盖 macOS/Linux、绝对路径/相对路径、带空格 check name、EOF 空白、symlink、临时目录别名、PID publication 和 teardown 竞态。
- 将 GitHub snapshot、fake-GitHub、local verifier、fixed-head monitor 作为同一 contract matrix 的不同层，而不是各自维护相似 fixture。
- 把 AIO adapter 的 history、删除路径和 policy 触发条件纳入变更分类测试，避免只测 manifest-only 变化。

### P2：降低人工复盘成本

- 生成 machine-readable 的 session index：Session ID、日期、阶段、结果、failure code、fixed head、merge SHA、release tag。
- 报告和 acceptance 记录只引用 index 与权威 task record，减少主会话重复搜索 5MB 级 JSONL。
- 对静默等待采用单一状态摘要，健康 timeout 不产生 commentary；只有 child terminal、错误、授权变化或 deadline 才唤醒主会话。

## Git/发布结果对照

| 阶段 | 关键合并/发布 | 结果 |
|---|---|---|
| M-1A/M-1B/M-1C | `0cc09e9` / `1d30345` / `afacf49` | D2 原生不足、watcher core ready、live gate unsupported，auto route 保持关闭 |
| M0/M1 | `2207645` / `5eb3bd3` | canonical foundation 与 deterministic task core 完成，多轮反例修复后合并 |
| M2 | `9351d62` / `b16349a` / `0976b49` | 角色路由、自动桥、rework core 完成；bootstrap exception 终止 |
| M3/M4 | `d7348ab` / `f7c5a05` / `6f265e1` / `44e4139` | policy、资源、review、finalization 完成 |
| M5 | `c14f166` | `v0.1.0` 精确发布，source/canary/L3/L4 同 SHA 绑定 |
| P1/P2 | `ded7a72` 与 trusted-main apply | `v0.1.1` 生产迁移、global AGENTS 无损压缩和 doctor healthy |
| R2-R4 | `dd7ec7a` / `2a63cd8` | `v0.1.2`、`v0.1.3` 发布，消费 policy/origin 绑定 |
| R5/R6 | `be1e515` | `v0.1.4` 发布，修复 runner-resource 事实绑定 |
| R9/R10 | `790d592` / `60ac0c4` | GitHub acceptance/delivery 修复后发布 `v0.1.5` |
| AIO B4/C/D | `36a4b185` / `378fb515` / `1c4ffe45` | 从已发布 `v0.1.5` 隔离 runtime 完成 adoption 三阶段 |

失败事实仍需保留：R6 adapter 越权 merge、R7 `HEAD_MISMATCH`、R8 immutable requirements EOF、AIO B4/C/D 各轮失败 head。它们是流程证据，不应被清理为“无效噪声”。

## 当前判断

原定工作流已经从“依赖 Agent 自觉的长会话流程”升级为“由授权、事实源、状态机和固定 head 约束的发行流程”。这是成功的核心变化。代价是流程更慢、更依赖平台能力，也更容易在契约边界处停住。

短期不应继续扩展功能面，优先解决 P0/P1 的平台与入口问题：线程回收、结构化 spawn、offer 前合同冻结、canonical writer 权限和跨平台矩阵。完成这些后，自动路线才有资格从“合同上可用、实战上经常 awaiting_claim”变成可重复的生产能力。

## 可复核材料

- `VISION.md`
- `.agents/context.md`
- `.agents/decisions.md`
- `.agents/open-items.md`
- Session JSONL：`~/.codex/sessions/2026/08/17/` 至 `~/.codex/sessions/2026/08/25/`
- AIO adoption 的任务事实源由 `.agents/context.md:11` 指向；R7-R10 与 B4/C/D 的失败和收尾记录见 `.agents/context.md:14-19`、`.agents/decisions.md:407-429`
