# Optional Packs

当前 manual-first 路由不注入任何 optional pack。普通任务只有 `gkd-main` 一个 GKD Skill；它负责计划、执行 session 交接和主代理审查。

`ci-advice` 与 `review-remediation` 仍可能出现在历史 bundle 声明中，但不属于当前生产入口，也不再由 GKD 角色自动路由。需要相关能力时，按任务明确选择独立工具或 Skill，不修改这三份人工交接文档的职责。

历史 bundle 的隔离 pack 命令仅供读取旧材料：

```sh
gkd-bundle pack-stage --source-root canonical --temporary-root <root> --target <target> --pack ci-advice
gkd-bundle pack-verify --temporary-root <root> --target <target> --pack ci-advice
gkd-bundle pack-remove --temporary-root <root> --target <target> --pack ci-advice
```

旧 `gkd-role` context/project staging 和 optional 验证 lane 不属于当前 manual-first 工作流。
