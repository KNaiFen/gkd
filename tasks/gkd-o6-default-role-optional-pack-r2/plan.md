# GKD O6 Default Role And Optional Pack R2 Plan

## Goal

将核心执行闭环与按需 CI/review 能力分层，降低默认安装和 executor 上下文成本，同时保留显式使用与兼容恢复能力。

## User Decisions

- 基线 `ce2d6814a1a4b75e16fe9e096f66b399a28de07f`，execution bundle `fe1098fd1be01e8b59dd268b0ed45cc7b44217063e00e0a20afd0bf1c9b1014c`。
- PR #50 已为 schema-v2 pack、八 scope core 与 optional lanes 提供受信 fixed-tree consumer；本任务才能改变 producer。旧 O6 attempt 不复用。

## Behavior And Defaults

- core 是默认且最小的 task/route/local-verify/fixed-head CI/acceptance/release 闭环；optional pack 只有显式请求才进入项目或角色上下文。
- source、manifest、lock 与 project inventory 是 core/pack 文件归属和 digest 的唯一事实源，不能用路径存在或 Skill discovery 偶然行为代替声明。

## Scope

- 建立最小的 core/optional pack 声明、安装、stage/verify/remove 和 role-context 选择；迁移当前 CI advice 与 review/remediation 文件并更新全部消费者、文档与测试。

## Non-Goals

- 不删除 optional 能力或兼容入口，不合并 O7/O8，不改变现有任务生命周期和发布语义。

## Acceptance Criteria

- 默认 executor/context/install 只含所需核心；optional pack 显式、可复现、可移除、自验证；双解释器、fixed-head CI 与 independent acceptance 通过。

## Compatibility

- 旧 bundle/manifest 的读取与拒绝/迁移边界保持；现有 CLI 名称和 Skill 触发语义保持，迁移继续禁用重复发现的旧 Skill。

## Security And Data

- 不读取凭据或生产配置；pack name、声明和目标路径严格验证，未知、篡改、symlink、extra/missing 内容均在写入前拒绝。

## Migration

- 合并后仅刷新未发布 development bundle/project staging；旧 release asset、生产与 AIO 不修改。

## Public Interfaces

- 若扩展 bundle/project CLI，保留无 pack 参数时的 core 默认，并使用版本化、枚举式 pack 参数；不复用自由路径作为 pack identity。

## Execution Route

- gkd-main 完成 planning/authorization/offer/claim；spawn 前固定 acknowledgement 与 status CAS，spawn 后立即 bridge claim；executor 只交付，acceptor 只验收，trusted main 合并清理。

## External Side Effects

- 仅允许 task worktree/branch/PR、verifier/evidence 与只读 CI；禁止生产/AIO/settings/Secrets/runner/tag/Release 写入。

## Action Mode

`implement_and_merge_on_acceptance`

## Implementation Notes

- 先建立当前 default role/context/install 与 optional consumer 的精确文件清单，再设计最小声明形状。实现必须使用 PR #50 已接受的 future result/pack consumer；所有 generator/schema/lock/packaging 更新进入 final implementation commit，delivery.md 是唯一直接子提交，delivery 后无实现提交。
