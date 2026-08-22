# GKD

GKD 工作流的规范源码、版本管理与专属验证仓库。

长期使命、用户承诺和冲突取舍以唯一的 [VISION](VISION.md) 为准。

当前仓库提供可扩展的 development bundle foundation、确定性任务核心、固定角色/路由核心、project-scoped automatic runtime bridge、trusted fixed-head rejection/rework、无副作用的 finalization/release promotion record，以及由仓库 policy 驱动的 GitHub fixed-head CI monitor、资源/产物规划、固定范围脱敏 scanner 和 repository-neutral review/remediation core。`0.1.1` 还提供独立的生产迁移计划、应用、doctor 与回滚/恢复接口；旧 temporary migration 命令继续拒绝生产根目录。实际生产安装与 AIO 接入仍由 trusted main 在独立门禁中执行。

Canonical CLI、project staging 与 automatic runtime bridge 要求 Python 3.11 或更高版本。

仓库 CI policy 位于 `.gkd/policy.json`。本地与 pull request 验证共用
`scripts/gkd-verify --base-sha <full-sha>`，只需要 Python、Git 和标准库。
