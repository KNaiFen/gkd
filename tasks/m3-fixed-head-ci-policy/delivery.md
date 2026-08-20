# GKD-M3-A 交付

## 结果

- Outcome: `fixed_head_ci_policy_ready`
- Fixed base: `5cc7f6bbc61c2a06ecdf2104a6e7cd3129f23959`
- Claim: `1a538c861a253dc70e3c973f00db31872f82d1cf088e2859e630570aa376d6c7`
- Implementation commit: `142dcdb2a0f051f3536baa5c231db429a04872a8`
- PR: [KNaiFen/gkd#8](https://github.com/KNaiFen/gkd/pull/8)
- Accepted execution bundle: `05288d5b09bdd8b4703a45d8a300d9466ad59f6b414d8eb5684c4a214ecfaaad`
- Candidate output bundle: `92e218e9809e6147f3b04ec7f8fed79231c6e8b3a94480729b52b6fcdbafafe8`

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
终态为 `333/333`：M3-A `27`、task-core `104`、role-routing `70`、
runtime-bridge `32`、foundation `53`、watcher-core/live-negative `47`。未安装依赖，
未运行历史 live probe、M2-B 一小时实验、大型构建或 cache。

M3-A evidence 在两个互不相交的干净系统临时根生成，均为 `27/27` 且逐字节一致：

- Evidence digest: `3476aabb597f8c257737ae47c5fca943517ed2642d17349e5c5d9fc288c855a4`
- Evidence file SHA-256: `4b2d7ad2f0b08b30fe28e4f957b9f7372644c0552ab7c39caf9ae3982c93d18f`
- Production before/after: `957e7ddbb7ed95e79f0774c131421514473bbd5e50939668803b038ced31434e`（2295 entries）
- AIO before/after: `4135aa3394a11db94fe948e401fda8dab10b3e2d97a8e7f01ae83f0ceed5dfd6`（15681 entries）

两个 evidence temporary root 结束为空。最终 delivery push 后，executor 使用本任务新增的
policy-backed monitor 观察 PR #8 的完整 fixed head；该云终态由 executor handoff 单独
报告，不在 push 前预写为成功。

## 停止边界

本 session 停在 exact claim delivery 与 trusted-main 独立验收之前：不验收、不合并、
不归档、不清理 worktree/branch、不启动 M3-B，不修改生产 `~/.codex`、AIO、sandbox、
仓库设置、Secrets、runner、tag 或 Release。
