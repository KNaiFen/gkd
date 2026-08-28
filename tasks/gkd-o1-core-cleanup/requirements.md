# GKD-O1 Requirements

## Goal

在不改变 GKD 运行时行为、公开 CLI、manifest 语义或兼容承诺的前提下，移除确认无调用的 payload helper，并合并 foundation mode 测试的重复实现。

## User Decisions

- O1 是精简计划的第一个独立任务，必须从 trusted main 的完整 fixed base SHA 开始。
- 只允许一个 `gkd_executor` 实现并交付；独立 `gkd_acceptor` 负责验收，trusted main 负责合并和收尾。
- 不修改生产 `~/.codex`、AIO、GitHub settings、Secrets、付费 runner、tag/Release 或已发布资产。
- 不删除 task/role/release 核心 API、legacy read/reject/migrate、watcher/probe 行为或测试语义。

## Scope

- 删除 `gkd_task.gitops.fixed_tree_paths`，除非实现发现存在未检出的外部 API 约束。
- 将仅由测试使用的 `gkd_task.migration.make_legacy_v1` 移到测试 helper，保留 `validate_legacy_v1` 与 `migrate_v1`。
- 删除或移到 tests 的 `gkd_ci.scanner.scanner_result_digest`、`gkd_review.adapter.canonical_adapter`、`gkd_ci.resources.canonical_resource_plan`；对应主入口和验证函数保持不变。
- 合并 `tests/foundation/test_install.py` 中 mode drift 的重复测试表达，保留可执行文件和 metadata 两类反例覆盖。
- 更新受影响的 import、测试 helper、manifest/lock（仅当生成流程证明文件列表发生变化），并保持 source/runtime 边界不变。

## Non-Goals

- 不拆 optional pack，不改变 `role-routing.json` 默认 Skill，不移动 fixture，不改 `scripts/gkd-verify` scope，不迁移 watcher/probe。
- 不合并 `gkd-finalize` 与 `gkd-release`，不改 release 版本或生产安装。

## Acceptance Criteria

1. 全仓源码和测试搜索确认 5 个 helper 无运行时/公开 CLI 调用；测试所需构造器位于 tests helper。
2. task、foundation、CI、review、release 相关现有行为测试通过；mode drift 的正反例覆盖数量不下降。
3. `scripts/gkd-verify --base-sha <full-base-sha>` 通过，输出无 protected surface、临时目录或路径泄漏漂移。
4. 两次独立 evidence 运行字节一致，candidate output bundle digest 与 delivery document 绑定固定 head。
5. 变更不引入仓库名、用户名、绝对路径、token、secret 或新的依赖；旧发布资产不被修改。
