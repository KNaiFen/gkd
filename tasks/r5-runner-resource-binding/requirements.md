# GKD Runner Resource Fact Binding

## Goal

修复 CI recommendation 将 host 资源事实外推为 GitHub runner 容量的问题，使 speed-first 只在有同一 verified runner 的可用资源事实时选择非保守 preset。

## User Decisions

- 用户已授权修复已发现的 GKD 通用流程缺口，并继续 AIO adoption；AIO B2 在新的已发布 bundle 可用前不写入。
- 不添加 runner、修改 GitHub 设置、查询价格或修改消费仓库工作流。

## Scope

- 将 recommendation 的 preset 选择绑定到 resource facts 的 source 与 verified runner capacity，host/observed/unknown 事实不得证明云端容量。
- 在 current runner 没有同源、完整、已验证资源边界时保持 resource-constrained；recommendation 不得声称存在未提供的更高容量 runner。
- 增加 deterministic unit/contract regression，并更新 resource-scanning 文档的事实边界。

## Non-Goals

- 不变更 artifact class、scanner 规则、价格、GitHub workflow、role、task bridge、AIO 文件或生产安装。
- 不将本机硬件数值、AIO repository identity 或任意 runner price 写入 canonical payload。

## Acceptance Criteria

- [ ] host/observed/unknown resource facts 即使数值充足，也不能提升 cloud runner preset 或产生无依据的高容量 runner action。
- [ ] 仅当 runner facts 与完整 verified runner-sourced resource facts 一致时，speed-first 才可选择对应支持的 preset。
- [ ] 未提供候选 runner 集合时，recommendation 只保留当前已验证 runner，不声称选择不存在的容量。
- [ ] 既有 resource/scanner/recommendation contracts 和全量版本化 verifier 通过；固定 PR head `GKD Verify` 成功并经独立验收。
