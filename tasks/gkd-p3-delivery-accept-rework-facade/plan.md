# P3 交付、CI、验收与返工外观实施计划

## Goal

消除交付、CI、验收与返工过程中的重复机器参数，同时保留固定事实和用户控制。

## User Decisions

- 只在用户已授权范围内修改 GKD canonical source 与测试；不修改生产或 AIO。

## Behavior And Defaults

- 高层入口默认从 trusted context 派生路径、摘要、CAS、policy 和角色事实。
- 无法唯一推导或发生漂移时返回稳定错误，不写入状态。

## Scope

- delivery、CI monitor、accept/rework 的事实解析与意图入口，以及对应合同测试。

## Non-Goals

- 不迁移 planning 文档 schema，不删除 legacy CLI，不创建新外部基础设施。

## Acceptance Criteria

- 正向路径无需 Agent 手填重复机器事实；所有错配在写入前拒绝。

## Compatibility

- 旧 task state、legacy record、低层 CLI 的读取和拒绝行为保持兼容。

## Security And Data

- 不输出 capability、凭据、私有 agent/thread 身份或生产绝对路径；只保留最小机器事实。

## Migration

- 仅新增版本化 facade；历史记录不重写，旧格式按既有 read/reject 合同处理。

## Public Interfaces

- 新增 trusted-main-only 高层调用；candidate/public claim 与旧 CLI 不获得新权限。

## Execution Route

- trusted main 建立 fresh task，唯一 executor 实现，独立 acceptor 审查，fixed-head CI 成功后由 trusted main merge。

## External Side Effects

- 只允许任务 branch、PR、fixed-head CI 和合并；禁止 production、AIO、settings、Secrets、runner、tag、Release。

## Action Mode

- 用户已授权实施与范围内 merge；executor 不验收、不合并、不清理。

## Implementation Notes

- 在 trusted-main orchestration 层复用 `TaskService`、`gkd_role` project/policy、CI monitor 和 acceptance/rework service，不复制状态机。
- 增加只读事实解析与最小意图入口：delivery 只接收完成意图，CI 只接收固定 PR 观测意图，accept/rework 只接收独立 review 与 merge/rework 意图。
- 所有生成事实在外部写入前从 canonical state、固定 tree、policy/origin 和 PR snapshot 重算；任何不一致返回稳定错误且不改状态。
- 通过兼容适配保持 legacy CLI 和历史 record 的读取与拒绝路径，不改变 task state schema。

### Verification

- 为每个 facade 增加正向、缺失、替换、漂移、重复和写前不变合同；重点覆盖 O4/R7/R8/R9 记录的真实失败形态。
- 使用 Python 3.9.6 与 3.14.6 运行完整 `scripts/gkd-verify --base-sha 6f088c819cf5c203404ad031ac2de1aec7c6d702`，并生成双运行一致 evidence。
- 由 trusted main 创建 PR，使用相对 `.gkd/policy.json` 的 fixed-head monitor；独立 acceptor 在 merge 前完成 review，随后才允许精确 merge。

### Boundaries

executor 只实现本任务并停在 delivery；不验收、合并、返工、归档或清理。trusted main 独占 acceptance、merge、rework 和 cleanup；本任务不触碰生产或 AIO。
