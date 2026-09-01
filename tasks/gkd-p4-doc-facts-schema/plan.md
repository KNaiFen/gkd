# P4 文档事实渲染与 schema 迁移计划

## Goal

在 P3 trusted-main facade 之上增加 renderer，不改变生命周期、CI、acceptance 或 production 权限边界。

## User Decisions

继续采用 trusted-main 生成机器事实；保留 fixed-head、digest、独立 review、CI、授权与 legacy read/reject 兼容边界。

## Behavior And Defaults

默认由 trusted `gkd-main` 从当前 task context 生成 canonical facts；缺失或歧义输入 fail closed，Agent 不手填 roots、CAS、digest 或 JSON。

## Scope

新增确定性的事实渲染器和受信 CLI 入口；为 requirements、plan、implementation、delivery、acceptance 定义版本化事实块规则；补充从现有 machine artifacts 重建事实的合同与 drift 负例。

## Non-Goals

不修改生产 `~/.codex`、AIO、GitHub settings/Secrets、付费 runner、tag/Release；不删除历史文档，不改变任务状态机或外部 GitHub 行为。

## Acceptance Criteria

同一 task/result/review/CI 输入两次 renderer 输出逐字节一致；机器事实与人类叙事分离，叙事改动不影响 acceptance；历史文档可读且无效 schema fail closed；Python 3.9 与当前支持解释器通过默认 verifier。

## Compatibility

保留低层 CLI 与旧文档读取路径；新 facts schema 只扩展受信主路径，不改变 legacy read/reject 合同。

## Security And Data

renderer 不读取或输出 capability、绝对路径、凭据或生产配置；只接受已校验的 task/result/review/CI 对象。

## Migration

先生成兼容 facts 区段并验证，再允许新 schema 文档；历史文档不做原地重写，迁移失败保持旧读取路径。

## Public Interfaces

trusted `gkd-main` 增加 facts render/verify 入口；内部低层接口继续保留为兼容和诊断，不要求 Agent 直接调用。

## Execution Route

实现、focused contracts、canonical artifacts、delivery 文档和最终 task-only commit 按既有 fixed-head 顺序完成；验收在 merge 前执行。

## External Side Effects

只允许仓库源码、临时 bundle、临时 project stage 和批准的 public PR；不触碰生产/AIO/settings、Secrets、付费 runner、tag/Release。

## Action Mode

默认自动路线仍需完整六门禁；facts renderer 本身为纯计算，写入只发生在 trusted-main 受管路径。

## Implementation Notes

复用 canonical/digest/schema 工具，renderer 不创建 daemon、IPC、签名或第二事实源。
