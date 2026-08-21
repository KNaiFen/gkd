# GKD

GKD 工作流的规范源码、版本管理与专属验证仓库。

长期使命、用户承诺和冲突取舍以唯一的 [VISION](VISION.md) 为准。

当前仓库提供可扩展的 development bundle foundation、确定性任务核心、固定角色/路由核心、project-scoped automatic runtime bridge、trusted fixed-head rejection/rework，以及由仓库 policy 驱动的 GitHub fixed-head CI monitor、资源/产物规划、固定范围脱敏 scanner 和 repository-neutral review/remediation core。默认路线仍为 manual，candidate-facing task claim 与公开 role automatic CLI 均 fail-closed；生产安装与 AIO 接入不在本结果内。

Canonical CLI、project staging 与 automatic runtime bridge 要求 Python 3.11 或更高版本。

仓库 CI policy 位于 `.gkd/policy.json`。本地与 pull request 验证共用
`scripts/gkd-verify --base-sha <full-sha>`，只需要 Python、Git 和标准库。
