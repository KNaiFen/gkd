# GKD-O4 Implementation

## Internal Design

将默认验证与历史验证建模为两个显式入口，共享 O3 的 canonical result schema 和固定 head 绑定。默认入口不导入 `gkd_watchdog` 或 `probes/app-server-watcher`；historical 入口才发现并调用 watcher contracts，必要时再显式调用 host-capability probe。历史入口必须保留 M-1B 47 项合同和 M-1C `unsupported` 事实的可追溯性。

## Execution Details

executor 修改前须搜索所有 `SCOPES`、watcher/probe runner 调用点和 manifest 生成入口，先建立默认/历史测试基线，再做最小分层。不得用删除测试、跳过失败或硬编码 `pass` 缩短默认结果；若发现默认入口与公开 CLI 兼容性冲突，停止并记录 finding。

交付时记录实际默认 scope 集合、历史 scope 集合、两次 evidence 摘要、candidate bundle digest、固定 head 和清理结果。缺少真实宿主能力时必须保留可复现的 fail-closed 结果，不把平台不可观测性改写为支持结论。

