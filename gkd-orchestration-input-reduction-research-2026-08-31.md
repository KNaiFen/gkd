# GKD 编排输入面收敛调研报告

**日期：** 2026-08-31
**范围：** trusted-main 编排、task/role/bundle/CI CLI、机器交接工件与任务 Markdown。
**结论：** 近期失败的主因不是缺少检查，而是同一机器事实被 Agent 以路径、命令行参数、JSON 和 Markdown 多次手填。下一轮应先删除这些重复输入面，再由受信 CLI 从唯一事实源派生剩余机器数据。

## 1. 判断与边界

GKD 的安全边界本身需要保留：task state 的 CAS、固定 head、policy 绑定、bundle digest、独立 review、host spawn acknowledgement 和显式 merge 授权都不能因“少填参数”而弱化。

要删除的是 Agent 面向的重复输入，不是底层证据：机器仍会保存 offer、capability、envelope、claim receipt、结果 manifest 和 review；但 Agent 不再创建、编辑、复制或把它们重新放进另一个命令。

这符合 VISION 的“脆弱状态与重复动作由确定性脚本生成和校验”原则，也比增加人工预检更直接。

## 2. 会话事实

本机 session `01a04842-1b67-71e0-878e-64e862b19d69` 与任务历史记录显示，下列失败都源于手工拼装而非业务判断：

- 空 planning package 直接 bootstrap，得到 `INVALID_PLANNING_PACKAGE`。
- bundle install 先把仓库根误作 source root，后又漏建 target，再把 target 多嵌套一层，依次得到 `INVALID_SOURCE_DECLARATION`、`INVALID_TARGET` 和缺失启动脚本。
- bundle digest 更新后直接 stage，得到 `PROJECT_STAGE_DRIFT`；正确动作是受管 remove -> stage -> verify。
- 手填不存在的 CLI 参数得到 `INVALID_ARGUMENTS`；完整 verifier 又先以前台短时上限启动而被中止。
- 更早 attempt 有绝对 policy path 的 `POLICY_PATH_UNSUPPORTED`、candidate path identity mismatch、claim 前启动 executor 的 preclaim race、简写 repository 的 `REPOSITORY_INVALID`。

这些失败均被 fail-closed 门禁阻止，没有伪造成功或污染已合并状态；但它们证明当前主控 API 的人工输入面过大。

## 3. 当前重复输入面

| 面 | 当前 Agent 手填 | 已有权威来源 | 收敛结论 |
|---|---|---|---|
| task 生命周期 | candidate/runtime/main/package roots、task path、repository、branch、base SHA、CAS head/revision | candidate `task.json`、runtime attachment、Git common dir、trusted checkout | 高层命令不再接收这些定位和重复状态参数；底层 transaction 内部仍执行 CAS。 |
| 自动 route/claim | route decision JSON、role/config/bundle digest、envelope ID、nonce、spawn acknowledgement JSON | project inventory、bundle lock、task policy、offer/envelope、host API 返回 | 仅 trusted-main adapter 构造和消费；Agent 只发起 route 选择并转交原始 host 返回。 |
| executor | status/doctor 的完整 argv、candidate/runtime/task identity | bridge sealed execution context | executor 只接收 opaque context，不再根据 cwd 或手拼 argv 推断。 |
| delivery | claim ID、delivery path/digest、result/evidence paths、candidate bundle digest | task state、固定 task path、result manifest、verification artifacts、candidate bundle root | CLI 固定计算路径和 digest；Agent 只交付实现与机器生成的验证产物。 |
| acceptance/rework | trusted/candidate roots、repository、checks、policy path、adapter path、actor role、candidate head | task state、task policy、trusted checkout、installed bundle、PR snapshot、runtime | 高层命令只接受 task selector、独立 review artifact 和明确 merge/rework 意图；PR 只在唯一匹配时自动发现，否则 fail closed。 |
| CI monitor | checkout、repository、relative policy path、policy digest、timeout/poll | trusted checkout origin、固定 `.gkd/policy.json`、task state | 默认 checkout 为 trusted cwd，repository/policy 由校验函数取得；PR/head 和可选超时策略保留。 |
| bundle/project stage | source root、temporary root、target layout、bundle digest、旧 stage transition | bundle wrapper、manifest lock、project inventory | development wrapper 只接受受管 workspace；临时根/target 和 digest 由 CLI 创建或读取。生产 root 继续显式。 |
| Markdown | delivery/acceptance 中的 head、PR、digest、tests、CI 结果重复抄写 | task state、review、CI snapshot、result/evidence artifacts | 保留人类结论、范围、风险与复盘；精确机器事实由 renderer 生成或只引用 canonical artifact。 |

相关实现在 [gkd_task CLI](canonical/payload/lib/gkd_task/cli.py)、[gkd_role CLI](canonical/payload/lib/gkd_role/cli.py)、[trusted bridge](canonical/payload/lib/gkd_role/bridge.py) 和 [planning parser](canonical/payload/lib/gkd_task/documents.py)。

## 4. 第一步：应删除的输入与副本

以下内容应从 Agent 面向的高层 API 删除。它们可继续作为内部函数参数或机器工件字段，但不能再要求 Agent 填写。

1. 所有 `--main-root`、`--candidate-root`、`--runtime-root`、`--bundle-root`、`--package-root`、`--repository`、`--task-branch`、`--task-path`、`--base-branch`、`--base-sha` 的重复组合。
2. 所有 Agent 直接填写的 `--expected-head`、`--expected-revision`、`--role-digest`、`--config-digest`、`--bundle-digest`、`--envelope-id`、`--activation-nonce`、delivery document path/digest 和 adapter path。
3. `route-decision.json`、wait state/observation JSON、spawn acknowledgement JSON、activation JSON、offer/capability/envelope/claim/receipt JSON 的人工创建或复制。
4. `delivery.md` 与 `acceptance.md` 中手填的 PR、head、merge SHA、review digest、bundle digest、test count、CI result、lane/profile/scope。它们不是机器验收输入，也不应有第二 writer。
5. requirements 与 plan 中重复的 Goal、User Decisions、Scope、Non-Goals、Acceptance Criteria 的事实性副本。requirements 保留需求与授权语义；plan 只保留行为、迁移、接口、执行设计，公共事实使用 requirements digest 引用或生成快照。

这不是删除 `task.json`、authorization、offer、runtime receipt、result manifest、verification artifacts 或 structured review。它们是独立证据，不能从叙述安全重建。

## 5. 第二步：由受信 CLI 派生的输入

建议新增仅可信 main 可用的 `TrustedMainOrchestrator` 与对应 `gkd-main` 高层入口。它从当前 clean trusted checkout、task state、runtime attachment、bundle lock、project inventory、Git origin 和 `.gkd/policy.json` 推导机器事实，并继续调用已有的严格底层 service/bridge。

| 高层动作 | Agent 显式提供 | 受信实现派生或生成 |
|---|---|---|
| 创建任务 | task intent package、任务简短 ID、显式 base/ref 选择 | task path/branch、worktree/runtime/package location、repository、base identity。 |
| 批准 | decision reference、mode、allowed external actions | 当前 CAS snapshot、authorization artifact、所有 task locator 字段。 |
| 启动 | task selector、manual/automatic 选择、显式 optional packs | project verify、policy、bundle/role/config digest、route decision、offer/envelope、execution context。 |
| 完成 spawn | host API 原样返回的单次 spawn acknowledgement | task name 校验、activation nonce/receipt、即时 claim、sealed executor context。 |
| 等待 | host terminal/error/wait event | wait state、observation JSON、deadline/interrupt decision。 |
| 交付 | 无额外机器参数 | claim、固定 delivery 路径、验证 artifacts、digest 和 candidate output bundle identity。 |
| 验收/rework | task selector、独立 review artifact、显式 merge 或 rework 意图 | candidate/trusted root、PR 唯一发现、fixed head、repository、policy checks、adapter、actor role、CAS snapshot。 |

PR 与 full head 是外部事实，不能静默猜测为任意值。高层入口只能从 task branch 发现唯一 open PR，并将其 head 与 delivered fixed head 比对；缺失、多个或 drift 均拒绝。review/finding 与用户授权同样不可自动生成。

## 6. 必须继续显式的输入

- 用户材料性意图、requirements/plan 的决策内容。
- `decision-ref`、实现模式、允许的外部动作和显式 merge/rework 决定。
- manual 或 automatic route 选择；六门全通过只表示 automatic 可用，不代表可替用户选择。
- optional pack 选择，因为它改变角色能力和上下文。
- 独立 review 的 conclusion/findings；它可以由 acceptor 产生 canonical artifact，但 main 不能代写。
- 生产 home/root 和任何计划外外部系统目标。

## 7. 建议的验收指标

- `gkd-main` Skill 不再展示或要求 root、digest、CAS、policy path、完整 argv 或手写 JSON。
- 正常 automatic route 中，Agent 不创建任何 route/spawn/wait/offer/claim/receipt JSON。
- delivery/acceptance Markdown 没有手写机器事实副本，且仍能从 canonical artifacts 完整重建审计事实。
- 历史的 planning package、source/target layout、policy path、stage drift、preclaim、candidate identity、delivery head 错误均有回归合同。
- legacy low-level CLI 只有在明确 diagnostic/compatibility 模式下保留；默认高层路径不允许回退到人工拼装。

## 8. 风险与取舍

高层外观不能变成绕过信任边界的万能 CLI：公开 `gkd-role automatic-*` 与 candidate-side claim 必须继续 fail closed。CAS 也不能“删除”，只能从外层参数移入同一受信 transition 内部读取和复核。

文档去重需要版本化迁移，不能手改旧 task Markdown 或破坏 legacy reader。第一版可先保留现有文件形状，只停止把机器事实当手写内容，并由 renderer 生成；随后才引入新的 planning document schema。
