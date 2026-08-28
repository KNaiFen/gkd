# GKD-O1 Plan

## Goal

完成无行为变化的核心清理：移除确认无调用的 payload helper，并合并 foundation mode 测试的重复实现，保持公开接口、状态机、manifest 和兼容承诺不变。

## User Decisions

- O1 从 trusted main 的完整 fixed base SHA 开始，独立交付和独立验收。
- 只允许一个 `gkd_executor` 实现并交付；独立 `gkd_acceptor` 验收，trusted main 合并和收尾。
- 不修改生产 `~/.codex`、AIO、GitHub settings/Secrets、付费 runner、tag/Release 或已发布资产。
- 不删除 task/role/release 核心 API、legacy read/reject/migrate、watcher/probe 行为或测试语义。

## Behavior And Defaults

- `validate_legacy_v1`、`migrate_v1`、scanner/review/resource 主入口和所有 CLI 行为保持不变。
- 只有测试构造 legacy v1 输入时才使用 tests helper；runtime 不再提供 `make_legacy_v1`。
- foundation mode drift 仍覆盖 executable 与 metadata 两类反例，测试 ID 和错误边界保持可追溯。

## Scope

- 删除 `gkd_task.gitops.fixed_tree_paths`。
- 将 `gkd_task.migration.make_legacy_v1` 移到 tests 专用 helper。
- 删除或移到 tests 的 `scanner_result_digest`、`canonical_adapter`、`canonical_resource_plan`。
- 合并 `tests/foundation/test_install.py` 中 mode drift 的重复测试表达。
- 更新受影响 import、测试 helper，以及由生成流程证明必须变化的 manifest/lock。

## Non-Goals

- 不拆 optional pack，不改变 `role-routing.json` 默认 Skill，不移动 fixture，不改 `scripts/gkd-verify` scope，不迁移 watcher/probe。
- 不合并 `gkd-finalize` 与 `gkd-release`，不改 release 版本或生产安装。

## Acceptance Criteria

- 全仓搜索确认 5 个 helper 无 runtime/公开 CLI 调用；测试构造器位于 tests helper。
- task、foundation、CI、review、release 相关现有行为测试通过；mode drift 反例覆盖不下降。
- `scripts/gkd-verify --base-sha <full-base-sha>` 通过且无 protected surface、临时目录或路径泄漏漂移。
- 两次独立 evidence 运行字节一致，candidate output bundle digest 与 delivery document 绑定固定 head。
- 不引入仓库名、用户名、绝对路径、token、secret 或依赖；旧发布资产不被修改。

## Compatibility

- 保留所有公开 CLI、错误码、schema、canonical JSON、digest 算法、manifest source 声明和 release traceability。
- 测试 helper 的 legacy fixture 字段和 digest 算法必须与原实现逐字节一致。

## Security And Data

- 仅处理仓库内源代码和测试输入；不读取凭据、用户级配置或私有 session 记录。
- 变更和 evidence 中不得出现原始 token、secret、机器绝对路径或用户名。

## Migration

- 无生产或消费仓库迁移；O1 只在 candidate worktree 交付，接受后由 trusted main 按 bundle 规则更新。
- 如果发现外部 Python 调用者，停止删除，改为弃用标记并在 findings 中说明。

## Public Interfaces

- 不新增公共接口；删除的 helper 均为确认无调用的内部符号或仅测试构造器。
- `gkd-task`、`gkd-role`、`gkd-ci`、`gkd-review`、`gkd-finalize`、`gkd-release` CLI 接口保持不变。

## Execution Route

- `gkd-main` 完成 requirements-ready、plan-approve、authorization、offer、claim 和 trusted bridge。
- 精确角色为 `gkd_executor`，不允许 worker、fallback、nested agent、角色替换或同 attempt 重试。
- 交付后由 `gkd_acceptor` 在干净同步 checkout 使用显式 full candidate head 验收；拒绝只能经 canonical rework 进入新 revision/epoch。

## External Side Effects

- 允许：一个 task worktree/branch/PR、仓库声明的 verifier、隔离 evidence root 和只读 CI 观察。
- 禁止：生产 `~/.codex`、AIO、GitHub settings/Secrets、付费 runner、tag/Release、未授权网络写入。

## Action Mode

- `implement_and_merge_on_acceptance`；executor 交付后停止，trusted main 仅在独立验收成功后合并。

## Implementation Notes

- 先生成符号引用清单和 focused test 基线，再做最小删除/移动。
- 运行 focused tests、`scripts/gkd-verify --base-sha <full-base-sha>`、双 evidence 和 candidate bundle verification。
- 交付顺序为实现提交、delivery document 提交、`gkd-task deliver`；不在同一任务混入 O2-O8。
