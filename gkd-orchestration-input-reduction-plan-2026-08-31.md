# GKD 编排输入面收敛优化计划

**依据：** [编排输入面收敛调研报告](gkd-orchestration-input-reduction-research-2026-08-31.md)
**状态：** 已获授权；P1、P2、P3、P4 已完成，下一项为 P5。
**目标：** 让 Agent 只提交意图、授权、路线选择与独立审查结论；所有路径、摘要、CAS、机器 JSON、交接命令和事实性文档字段由受信实现生成和校验。

## 不变项

- 保留 task state 的单 writer、CAS、epoch、offer/claim/rework 历史和固定 head 证据。
- 保留 policy/origin 校验、bundle/project inventory 绑定、独立 review、fixed-head CI 与 explicit merge authorization。
- 保留 production root、optional packs、manual/automatic route、review findings 和授权动作的显式用户决定。
- 不写生产 `~/.codex`，不修改 AIO、GitHub settings/Secrets、付费 runner、tag/Release。

## 总体设计

新增 trusted-main-only `TrustedMainOrchestrator`。它不是开放自动 claim API，而是封装已有 `TaskService`、`TrustedMainRuntimeBridge`、project verifier、CI monitor 和 acceptance/rework 路径。

低层 CLI 与 machine artifacts 继续作为内部兼容/诊断接口；新 `gkd-main` 高层入口成为 Agent 的唯一正常接口。任何无法从唯一事实源推导的值必须显式作为意图或外部证据传入，歧义时 fail closed。

```text
Agent intent / authorization / review
              |
              v
TrustedMainOrchestrator
  -> trusted checkout + task state + runtime attachment
  -> bundle lock + project inventory + policy/origin
  -> generated CAS, JSON, argv, artifact facts
              |
              v
existing TaskService / Bridge / CI / Acceptance contracts
```

## P1：任务上下文解析与只读预检

**范围**

- 定义 `TrustedTaskContext`，从 trusted cwd 或显式 task selector 定位 candidate、task path、runtime、repository、branch、policy、bundle 与当前 snapshot。
- 新增只读 `gkd-main inspect`/`preflight`，输出机器生成的 task selector、允许下一动作和必要的人类输入，不输出 capability 或绝对生产路径。
- 为 planning package 提供受管创建/校验入口，消除空 package bootstrap。

**删除的 Agent 输入**

- status/doctor/attach/handoff/recover 的 repository、task ID、task branch、candidate/runtime root、task path 与完整 argv。
- 通过根目录猜测的 bundle/source/target 组合。

**验收**

- 从 candidate、runtime attachment、trusted main 三种允许位置均可得到同一 context；歧义、symlink、origin/policy drift、跨 task 仍拒绝。
- 历史 `INVALID_PLANNING_PACKAGE`、candidate identity 与 source/target layout 失误都有直接回归测试。

## P2：受信启动、spawn 与等待外观

**范围**

- 将 project verify、route decision、role/config/bundle digest、offer、handoff、bridge prepare/claim 收入一个 trusted-main transition。
- host adapter 直接把一次 `spawn_agent` 返回交给 orchestrator；不再让 main 构造 acknowledgement JSON、nonce、envelope ID 或 claim CAS。
- executor 只取得 sealed execution context，context 内的 status/doctor 命令由 bridge 生成。
- 等待状态和 observation 由外观生成；保留 host event 与一小时 wait 的既有边界。

**删除的 Agent 输入**

- route JSON、role/config/bundle digest、expected head/revision、expires-at、envelope ID、activation nonce、spawn JSON、wait JSON/started-at。

**验收**

- 单次 spawn 后在同一 trusted transition 内完成 claim；preclaim race、重复 spawn、bundle 替换、host task-name mismatch 均拒绝。
- 不修改 public `gkd-role automatic-*` 和 candidate-side claim 的 fail-closed 行为。

## P3：交付、CI、验收与 rework 外观

**范围**

- delivery 从 fixed task path 和 verification artifacts 自动计算 document/result/evidence paths、claim、digest 与 candidate output identity。
- CI monitor 默认 trusted checkout，内部读取 origin 与固定相对 policy；唯一 PR/head 检查继续显式绑定。
- accept/rework 从 task state、project policy 和 installed adapter 派生 roots、repository、checks、adapter、actor role；只接受 independent review artifact 和明确 merge/rework 意图。
- 仅当 task branch 对应唯一 open PR 且其 head 等于 delivered fixed head 时自动发现 PR/head；否则终止。

**删除的 Agent 输入**

- delivery claim/path/digest/result/evidence 参数；CI 的 repository/policy path；accept/rework 的 roots、checks、adapter、actor role、candidate head 和重复 repository。

**验收**

- absolute policy path、简写 repository、delivery head 错误、PR/head drift、多个 PR、review mismatch、缺检查都 fail closed。
- canonical accept/rework 保持两次 snapshot、独立 review、固定 head 和 explicit merge authorization。

## P4：机器事实渲染与文档 schema 迁移

**范围**

- 添加由 task/result/review/CI artifacts 生成的 delivery/acceptance facts renderer；Markdown 只保留人类解释、边界、风险和复盘。
- 先以兼容格式生成现有 `delivery.md`/`acceptance.md` 中的事实块，再引入版本化 planning document schema：requirements 是材料性需求和授权，plan 仅含其特有实施设计并引用 requirements digest。
- 保持 historical task docs 可读、可验证；不得手改既有 records。

**删除的 Agent 输入**

- delivery/acceptance 的 SHA、PR、bundle digest、test count、CI/result/lane 副本；requirements 与 plan 的重复事实段落。

**验收**

- renderer 输出两次字节一致；从 machine artifacts 可重建相同事实。
- 人类叙事缺失或与机器事实不同不会成为 acceptance 机器输入；历史 schema 的 read/reject/migrate 合同保持。

## P5：bundle/project stage 收敛与低层接口退场

**范围**

- 为 development bundle 增加受管 build/stage transition：canonical source root、临时目录、target layout、bundle digest、旧 stage remove -> stage -> verify 全由 CLI 驱动。
- 高层正常路径移除低层参数说明；旧低层 CLI 保留为内部 diagnostic/compatibility 模式，并要求显式 `--strict` 或同等标记。
- 更新 Skills，使 main/executor/acceptor 不再教 Agent 手写 JSON 或复制 argv。

**验收**

- development stage 更新不再出现 source-root、target layout 或 `PROJECT_STAGE_DRIFT` 的人工修复路径；生产 root 仍不能默认或自动选择。
- Skill 文本和自动化 contract 中没有 root/digest/CAS/route JSON 的人工模板。

## 实施顺序与任务边界

1. P1 先独立交付，只读 context/preflight，不改变现有主路线。
2. P2 以新的 trusted-main orchestrator 覆盖 automatic start/spawn/wait；真实 host executor 验收后才进入 P3。
3. P3 覆盖 delivery/CI/accept/rework，并在固定 head 上验证所有历史编排失败。
4. P4 单独迁移文档与 renderer，避免和状态机/外部 GitHub 行为混合。
5. P5 最后清理高层 Skill 与 development bundle/stage 输入面；只有全部真实路线通过后才退场低层手工接口。

每项都必须使用 fresh task lifecycle、独立 executor、独立 acceptor、fixed-head CI 和 trusted-main merge。P1-P3 的 API/信任边界变更必须保留 legacy read/reject 合同；不得为了减少参数而接受模糊任务、PR、head 或授权。

## 成功标准

- 正常任务从创建到清理不要求 Agent 手填 filesystem root、repository、policy path、digest、CAS、CLI argv 或机器 JSON。
- Agent 只填写不可推导的意图、授权、路由选择、optional pack 选择、独立 review/finding 与明确外部动作。
- 每一项被移除的 Agent 输入都有唯一机器来源、推导测试和 drift/replay 负例。
- 现有的 fixed head、policy、bundle、review、authorization 与 recovery guarantees 不降低；生产和未授权外部系统仍保持不变。
