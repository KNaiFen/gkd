# GKD O6 Default Role And Optional Pack R2 Requirements

## Goal

收窄默认 executor 上下文和 core 安装面，将 CI advice 与 review/remediation 能力保留为显式、可验证的 optional pack，同时保持 task、route、acceptance、migration 与发布兼容承诺。

## User Decisions

- 基线为 trusted main `ce2d6814a1a4b75e16fe9e096f66b399a28de07f`，execution bundle 为 `fe1098fd1be01e8b59dd268b0ed45cc7b44217063e00e0a20afd0bf1c9b1014c`，project inventory 为 `ceaa6cec3dbae4fff1f29eefd863586c531b95bbf875f0e8c5e20649a104b1f4`。
- O6 attempt 0 已以 `delivery_consumer_optional_scope_compatibility` block，compatibility 前置 PR #50 已 merge `d3703bf57c5047f41db57e97d9117550acf7ffc9`；两者只读归档，不复用其 task、offer、claim、runtime、candidate 或提交。
- 一个精确 executor、一个独立 acceptor，trusted main 合并清理。executor 使用 bridge execution context 的精确 argv；不修改生产/AIO/settings/Secrets/runner/tag/Release。

## Scope

- 默认 executor 只注入 `gkd-execute`、`gkd-local-verify` 和需要固定 head CI 时的 `gkd-ci-monitor`；`gkd-main` 与 `gkd-accept` 保持其既有 trusted role 边界。
- 将 `gkd-optimize-ci`、`gkd-review-remediation`、resource class/preset、recommendation/scanner、review core/adapter/remediation 与其专用 schema/input 移到显式 optional pack；默认 core install、project stage、role context 和 verifier 不得隐式包含或加载这些能力。
- optional pack 必须能按名称显式 stage、verify 和 remove；声明、实际文件、mode、size、SHA-256、role/context/project inventory digest 必须一致，缺失、篡改、未知 pack 或错误安装面在写入前 fail closed。
- 保留现有 optional CLI 行为、用户显式触发 Skill、迁移时禁用重复 Skill 的机制，以及旧 manifest/schema/bundle 的 read/reject/migrate 兼容入口。
- 更新 source declaration、manifest/schema/lock、role inventory、project staging、文档和正反合同；core 与 optional pack 的结果必须使用已接受的 future consumer 格式绑定固定树。

## Non-Goals

- 不删除 CI advice、review/remediation 或其公开 CLI，不改变 fixed-head monitor、task/role/bridge/acceptance、production migration、finalization/release 行为。
- 不进入 O7 contract 索引收敛或 O8 兼容矩阵/engine 评估，不修改已发布资产或生产安装。

## Acceptance Criteria

1. 默认 core bundle/install/project stage 与 executor context 不含 CI advice、review/remediation 的 Skill 或专用 runtime 文件；executor 仍可完成 task delivery、local verify 与必要的 fixed-head CI handoff。
2. core main/acceptor route、五个默认 GKD Skills 的角色边界、manifest/lock/context/project inventory digest 和旧迁移禁用重复 Skill 机制保持有效。
3. CI advice 与 review optional pack 可分别或按批准组合显式 stage、verify、使用和 remove；未显式请求时无文件、配置或上下文副作用，所有 drift 反例 fail closed。
4. Python 3.9.6 与 Python 3.14.6 的 default/core verifier、bundle/install/project route、optional pack verifier、fixed-head CI 和 independent acceptance 都通过。
5. 不引入绝对路径、凭据、外部依赖或未授权外部副作用。
