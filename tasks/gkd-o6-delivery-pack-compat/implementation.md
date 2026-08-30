# GKD O6 Delivery Pack Compatibility Implementation

## Internal Design

以 schemaVersion 与 lane/profile 作为明确分派，不从字段缺失猜测版本。v1 走现有完整安装与十 scope default；v2 使用严格 pack ownership/core-pack digest 和显式 lane scope 集合。共享的路径、mode、size、SHA-256 与 fixed-head 校验保持单一实现。

## Execution Details

先运行 bridge 提供的精确 status/doctor argv。以 blocked O6 commit 中的 future artifact 形状建立仓库内可重建 fixture，覆盖 v2 正例和最小 mutation；不得改变本任务自身 source/manifest producer 或默认 scope 集合。双解释器完成 full verifier、future consumer probe、bundle/install 与 fresh delivery 后停止。
