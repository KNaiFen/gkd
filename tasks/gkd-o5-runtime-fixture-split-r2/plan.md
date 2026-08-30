# GKD O5 Runtime Fixture Split R2 Plan

## Goal

收窄默认 core runtime 安装面，而不丢失 release traceability 或 fixture 消费者的可验证输入。

## User Decisions

- 基线 `419549747fdf06918a5db9f31290bde37e598120`，execution bundle `b7a70cb64624f1b44a96e1367af07ffb98f17c11994c1ddfebcf4093d2ae5ff4`。
- 历史任务不复用；一个 executor、一个 acceptor，trusted main 才合并清理。生产/AIO/settings/Secrets/runner/tag/Release 不变。

## Behavior And Defaults

- core bundle 只安装 core runtime 所需文件；fixtures 通过明确的 test/release-verification 输入面访问，不能因安装路径偶然可见。
- manifest/lock 继续是安装面唯一事实源；fixture 输入与 release traceability 的 digest 都必须由实际文件重算。

## Scope

- 定位四个 fixture 及全部 consumer，迁移其声明和读取路径；更新 bundle source、manifest/lock、tests、traceability 文档与正反合同。

## Non-Goals

- 不改变 release/finalization 公开行为、O4 lane、task/role/bridge/CI 状态机，或已发布资产。

## Acceptance Criteria

- core install 无 fixture；显式 fixture/release input 可复现读取；双解释器 verifier、bundle、delivery、CI、independent acceptance 通过。

## Compatibility

- 保留 schema、release traceability、legacy read/reject/migrate 和 public CLI 形状；拒绝隐式 fallback 到 core 安装路径。

## Security And Data

- 不读取凭据或生产配置；fixture 内容和错误保持已有脱敏边界；缺失/篡改 fail-closed。

## Migration

- 合并后仅刷新未发布 development bundle/project staging；旧 release asset 与生产安装不修改。

## Public Interfaces

- 若新增显式 fixture root 或 test/release entry，只使用版本化参数或明确内部 test helper，不改变 core workflow CLI 调用形状。

## Execution Route

- gkd-main 完成 planning/authorization/offer/claim；spawn 前固定 acknowledgement 与 status CAS，spawn 后立即 bridge claim；executor 只交付，acceptor 只验收，trusted main 合并清理。

## External Side Effects

- 仅允许 task worktree/branch/PR、verifier/evidence 与只读 CI；禁止生产/AIO/settings/Secrets/runner/tag/Release 写入。

## Action Mode

`implement_and_merge_on_acceptance`

## Implementation Notes

- 先从 source declaration、manifest lock 和 fixture consumer 建立精确清单，再执行最小迁移。final implementation commit 含代码/schema/lock/results/evidence；delivery.md 是唯一直接子提交，delivery 后无实现提交。
