# GKD

GKD 工作流的规范源码、版本管理与专属验证仓库。

当前迁移目标是 manual-first：主代理写入目标、工作目录和行为约束，创建 Git worktree；执行代理按 `plan.md` 工作并更新 `progress.md`；主代理通过查看 diff、计划和报告决定通过或返工。完整协议见 [Manual-first 工作流](docs/manual-workflow.md)。迁移完成前，旧 automatic workflow 仍只作为 legacy 保留。

长期使命、用户承诺和冲突取舍以唯一的 [VISION](VISION.md) 为准。

原有 development bundle、确定性任务核心、自动 runtime bridge、fixed-head 验收、release engine 和专属 verifier 作为 `v0.1.5` legacy 保留。它们不再是普通人工任务的默认上下文；迁移计划完成前不修改既有发布资产、生产目录或 AIO。

Canonical CLI、project staging 与 automatic runtime bridge 最低支持 Python 3.9。

仓库 CI policy 位于 `.gkd/policy.json`。本地与 pull request 验证共用
`scripts/gkd-verify --base-sha <full-sha>`，只需要 Python、Git 和标准库。默认
lane 只运行核心合同；watcher/probe 历史合同必须显式使用
`scripts/gkd-verify --lane historical --base-sha <full-sha>`。
CI advice 与 review/remediation 合同分别使用 `optional-ci-advice` 和
`optional-review-remediation` lane；组合验证使用 `optional-packs`。
需要供 evidence runner 复用时，可显式传入 `--results-dir <directory>`；各 scope
runner 使用 `--canonical-results <directory>` 消费同一份固定结果。automatic
delivery 可额外使用 `--summary-output <path>` 生成待固定树校验的 canonical
verifier summary。historical lane 可使用 `--historical-evidence-output <path>`
生成 watcher evidence，并仅在显式传入 `--host-capability-probe-output <path>`
时执行 host-capability probe；不可观察的 host 会记录 `unsupported`。
