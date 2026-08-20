# GKD-M3-A 交付

## 结果

- Outcome: `fixed_head_ci_policy_ready`
- Fixed base: `5cc7f6bbc61c2a06ecdf2104a6e7cd3129f23959`
- Claim: `5dacf02c07be1f9646414c94dec605a95dfe33d6894a92804c87aba39c2afb0b`
- Implementation commit: `990dae37f1603a2216d14f160eb4e3565b926772`
- PR: [KNaiFen/gkd#8](https://github.com/KNaiFen/gkd/pull/8)
- Accepted execution bundle: `1983f05b64860510bfb1af661e5458a6c7b660632479a33af46c27d35ff188d4`
- Candidate output bundle: `0484095704599750df655bc6c92cf0b5829bc2c1ebb877aa3f3cd132cc29998f`

本交付只实现 M3-A：通用仓库 CI policy、GitHub origin/base 一致性、固定头只读
terminal monitor、标准 Actions workflow 与同一版本化本地验证入口。M3-B 资源与
scanner、M3-C review core 与新 Skills 均未实现。

## 实现

- `.gkd/policy.json` 使用严格 canonical JSON 与版本化 schema，声明 GitHub 仓库、
  base branch 和 required checks。parser 拒绝未知字段、非 canonical 内容、重复或
  非规范 check、路径穿越、policy/祖先 symlink、非 GitHub origin、歧义 remote、
  repository/base mismatch。
- installed `gkd-ci-monitor` 只接受显式 checkout/repository/PR/full head/policy/deadline，
  通过只读 `gh api --method GET` 获取 PR、check runs 与 status contexts；分页、外部
  类型、未知结论、重复 required check、API/transport failure 均 fail-closed。
- monitor 在每次 observation 前后重验固定 policy，head drift 立即终止且不再查询
  checks；deadline 同时约束 polling 与 GitHub subprocess。唯一 success 绑定 expected
  head、open PR 和全部 policy-required checks success。
- terminal JSON 使用版本化 strict schema，只包含 path-free repository/PR/head/base/
  state/check/policy digest 与终态分类；不保留 token、header、环境 secret、原始 API
  body 或机器路径，也不提供 rerun/dispatch/cancel/PR edit/accept/merge 写操作。
- `scripts/gkd-verify --base-sha <full-sha>` 验证 full base ancestry，在隔离标准库
  subprocess 中运行六个声明 scope。`.github/workflows/gkd-ci.yml` 使用标准
  `ubuntu-latest`、只读 contents 权限和同一入口；policy/workflow check 名均为
  `GKD Verify`，不使用 Secrets、付费或 self-hosted runner。
- canonical source/manifest/lock 已由生成器更新为 60 个 payload 文件。相邻
  `gkd-ci-monitor`、`gkd-local-verify` 与 `gkd-accept` 文档仅接入本任务公开接口。

## 验证

`scripts/gkd-verify --base-sha 5cc7f6bbc61c2a06ecdf2104a6e7cd3129f23959`
终态为 `335/335`：M3-A `29`、task-core `104`、role-routing `70`、
runtime-bridge `32`、foundation `53`、watcher-core/live-negative `47`。未安装依赖，
未运行历史 live probe、M2-B 一小时实验、大型构建或 cache。

M3-A evidence 在两个互不相交的干净系统临时根生成，均为 `29/29` 且逐字节一致：

- Evidence digest: `22b72cd484492317b9dd3196a86e34edfd3f697dbf4b1d526ff90263fd6db4ba`
- Evidence file SHA-256: `4568aa0d8aafead6ca53c5d37d3cd8986be0c6d0dec3ffb59575c9f27c4158f5`
- Production before/after: `957e7ddbb7ed95e79f0774c131421514473bbd5e50939668803b038ced31434e`（2295 entries）
- AIO before/after: `4135aa3394a11db94fe948e401fda8dab10b3e2d97a8e7f01ae83f0ceed5dfd6`（15681 entries）

两个 evidence temporary root 结束为空。最终 implementation head push 后，executor 使用
本任务新增的 policy-backed monitor 观察 PR #8 的完整 fixed head。monitor 绑定 expected
head `990dae37f1603a2216d14f160eb4e3565b926772`，110 次 observation 后以
`timeout / DEADLINE_EXHAUSTED` 终止（3600 秒）；PR 仍 open，observed head 与 expected
head 一致，但 `GKD Verify` 未出现，因此未宣称 CI success。

## 停止边界

本 session 停在 exact claim delivery 与 trusted-main 独立验收之前：不验收、不合并、
不归档、不清理 worktree/branch、不启动 M3-B，不修改生产 `~/.codex`、AIO、sandbox、
仓库设置、Secrets、runner、tag 或 Release。
