# Canonical development bundle

`canonical/` 是 GKD 的唯一 bundle 源目录。`source.toml` 是人工审查的声明；
`manifest.json` 和 `manifest.lock.json` 由 generator 生成，不得手工编辑。

当前 development bundle 的正常安装面只有 foundation 和 `gkd-main` Skill。
`gkd-main` 负责读取 `plan.md`、`progress.md`、`review.md`，协调执行 session，
并把审查决定留在主代理。普通任务不需要 GKD role、automatic route、fixed-head
acceptance、生产安装器或任何 migration 命令。

旧 task/role/bridge、CI/review、release 和 migration 文件可能仍在源码、测试或
历史 bundle 声明中，用于理解既有决策和验证旧记录；它们不属于当前路由，不应安装
到生产 `~/.codex`，也不提供兼容恢复入口。历史 optional pack 同样不由 GKD 自动选择。

Canonical CLI 支持 Python 3.9 或更新版本；TOML 解析在 Python 3.11+ 使用标准库，
Python 3.9/3.10 使用仓库内的 Tomli 兼容实现。bundle content digest 是按规范化
JSON 记录计算的 SHA-256，manifest、lock 和所有声明 payload 必须保持一致。

bootstrap installer 只接受显式存在的系统临时目录及其下的目标，不接受生产 home。
安装后的 `verify`/`version` 是 foundation 只读检查，不是生产 doctor。生成或修改
bundle 后必须重新生成 manifest/lock，并运行与变更范围相称的测试。

项目的正常协作入口见 [manual workflow](../docs/manual-workflow.md)；历史 verifier、
release lane 和旧 task 记录只作为只读证据，不构成当前任务的前置流程。
