# GKD O5 Runtime Fixture Split R2 Requirements

## Goal

将四个只服务于测试、演练或 release traceability 的 fixture 移出 core runtime 安装面，保持 schema、release traceability 与所有 fixture consumer 的可复现读取，不改变已发布资产或核心工作流行为。

## User Decisions

- 基线为 trusted main `419549747fdf06918a5db9f31290bde37e598120`，execution bundle 为 `b7a70cb64624f1b44a96e1367af07ffb98f17c11994c1ddfebcf4093d2ae5ff4`。
- O1-O4、Python 3.9 compatibility、gate repair、O5 attempt 0/R1 与所有旧 lifecycle 只读归档；本任务建立新的 task、offer、claim、runtime、branch、worktree 与 PR，不复用历史 artifacts。R1 的 `executor_candidate_identity_mismatch` 只通过更短 candidate path 与完整 execution context 处理。
- 一个精确 executor、一个独立 acceptor，trusted main 合并清理。executor 使用 bridge execution context 的精确 argv；不修改生产/AIO/settings/Secrets/runner/tag/Release。

## Scope

- 识别并迁移四个仅测试、演练或 release traceability 需要的 fixture，使默认 core bundle/install 不再包含它们。
- 为 fixture/release verification 提供显式、可复现的 test 或 release 输入面，保留已有 schema、digest、traceability 与 negative contracts。
- 更新 source declaration、manifest/lock、fixture digest、测试入口和文档；新增缺失/篡改/错误安装面的 fail-closed contracts。

## Non-Goals

- 不删除 release traceability、schema、legacy read/reject/migrate、production migration、finalization/release CLI 或任何已发布 asset。
- 不进入 O6-O8，不改 O4 default/historical lane、Python 3.9、逻辑时钟、planning refresh、delivery sidecar 或自动 bridge 语义。

## Acceptance Criteria

1. core install inventory 不含这四个 fixture，且 core verifier/role route/acceptance 行为保持兼容。
2. release-verification 或 test bundle 的 fixture 输入可独立复现读取；缺失、篡改或错误安装面在状态写入前拒绝。
3. Python 3.9.6 与 Python 3.14.6 完整 verifier、bundle、fresh delivery、fixed-head CI 和 independent acceptance 都通过。
4. 不引入绝对路径、凭据、新依赖或未授权外部副作用。
