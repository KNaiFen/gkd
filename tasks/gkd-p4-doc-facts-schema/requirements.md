# P4 文档事实渲染与 schema 迁移需求

## Goal

将 delivery、acceptance 与 planning 文档中的机器事实收敛到可重建的 renderer 输出；Markdown 仅保留人类说明、边界、风险和复盘。

## User Decisions

继续采用 trusted-main 生成机器事实；保留现有 fixed-head、digest、独立 review、CI、授权与 legacy read/reject 兼容边界。

## Scope

新增确定性的事实渲染器和受信 CLI 入口；为 requirements、plan、implementation、delivery、acceptance 定义版本化事实块规则；补充从现有 machine artifacts 重建事实的合同与 drift 负例。

## Non-Goals

不修改生产 `~/.codex`、AIO、GitHub settings/Secrets、付费 runner、tag/Release；不删除历史文档，不改变任务状态机或外部 GitHub 行为。

## Acceptance Criteria

同一 task/result/review/CI 输入两次 renderer 输出逐字节一致；机器事实与人类叙事分离，叙事改动不影响 acceptance；历史文档可读且无效 schema fail closed；Python 3.9 与当前支持解释器通过默认 verifier。
