# GKD-O1 Plan

## Implementation Shape

1. 从 fixed base SHA 建立 task worktree，读取根规则、VISION、持久记录和本任务文档。
2. 在 canonical payload 与 tests 中定位 5 个 helper 的全部引用，先写出符号清单和兼容判断。
3. 删除无调用 helper；将 `make_legacy_v1` 的测试构造逻辑移到 tests 专用模块，避免把测试输入生成器继续打包到 runtime。
4. 以 `subTest` 或等价参数化方式合并 foundation mode drift 测试，不改变断言边界和 test ID 语义。
5. 运行受影响的 focused tests，再运行声明的 `scripts/gkd-verify --base-sha`；生成两次确定性 evidence。
6. 提交实现和 evidence，单独提交 `execution.md`/`delivery.md` 后调用 `gkd-task deliver`，停在 delivered head。

## Compatibility Rules

- 保留 `validate_legacy_v1`、`migrate_v1`、scanner/review/resource 主入口及所有公开 CLI。
- 不因 helper 清理改变 canonical JSON、digest、schema、错误码、manifest source 声明或 release traceability。
- 测试 helper 可以移动，但不得改变 legacy fixture 的字段、digest 算法或错误路径。

## Verification

- focused: task migration/runtime、foundation install、scanner、review adapter、resource plan 相关测试。
- canonical: `scripts/gkd-verify --base-sha <full-base-sha>`，只使用仓库声明的 scope。
- deterministic: 两次同输入 evidence 逐字节比较；检查 candidate bundle 与 delivery document 的 digest/head 绑定。

## Execution Route

- `gkd-main` 完成 requirements-ready、plan-approve、authorization、offer、claim 和 trusted bridge。
- 精确角色：`gkd_executor`；不允许 worker、fallback、nested agent、角色替换或同 attempt 重试。
- 独立角色：`gkd_acceptor`，显式 full candidate head；拒绝后只能经 canonical rework 进入新 revision/epoch。

## Out Of Scope

- 默认验证重复执行、watcher historical lane、fixture split、optional Skill pack、兼容矩阵降频和 finalize/release engine 评估均留给 O3-O8。
