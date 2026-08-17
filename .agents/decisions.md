# Decisions

- [2026-08-17] 建立独立 GKD 开发仓库。
  - Why: 将 GKD 的 Skills、roles、脚本、schema、安装与测试从消费项目中分离，并使用 Git 管理版本。
  - Impact: 后续经批准的 GKD 实现和专属测试进入本仓库；消费项目只保存固定版本、digest 和项目 adapter。

- [2026-08-17] 完整 GKD 测试不挂到消费项目的每个 PR。
  - Why: 这些测试验证的是 GKD 工作流发行包，而不是普通产品功能。
  - Impact: GKD 源码变更运行 hermetic 测试，release candidate 运行适用的 agent/live 验证；消费项目仅在升级 bundle 或修改 GKD adapter/integration 时运行兼容性 smoke。

- [2026-08-17] GKD 上下文治理只采用 Skill无损去重、AGENTS无损压缩和角色最小上下文。
  - Why: 用户不需要专用profile、全局能力裁剪或token基线工程，只要求消除已证实的重复并减少规则与角色材料冗余。
  - Impact: 禁用Codex对6组 `.agents` Skill副本的发现但不删除原件；压缩AGENTS时保留全部硬边界；由确定性CLI生成角色材料清单。context window、插件/MCP、输出预算和fresh canary不在范围内。
