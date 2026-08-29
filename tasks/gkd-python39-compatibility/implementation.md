# GKD Python 3.9 Compatibility Implementation

## Internal Design

采用小型内部 compatibility facade 统一 TOML 入口：可用时导入标准 `tomllib`，否则使用随 payload 分发的、带许可的完整兼容实现。严格配对在迭代前显式验证长度，dataclass 移除 Python 3.10-only `slots` 参数；不以解释器路径或外部依赖规避问题。

## Execution Details

先以 `/usr/bin/python3` 复现全链路失败并枚举可达断点，再完成 payload、watcher/probe、tests 和文档的最小修改。新增 Python 3.9 subprocess/full-verifier 与 TOML parity/negative 合同，更新 manifest/lock 后同时验证 Python 3.9 和开发解释器。所有实现、许可、测试、evidence 和 delivery 文档遵循既有 fixed-head 顺序；不修改历史 task state 或 gate-repair 行为。
