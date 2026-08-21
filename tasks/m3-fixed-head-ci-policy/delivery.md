# GKD-M3-A 交付

## 结果

- Outcome: `fixed_head_ci_policy_ready`
- Fixed base: `d669c11735f1468127ce4b7b4699a19ef0984753`
- Claim base head: `720eb9c92299d90a3566cc6b0e6ca4d8ab13dcca`
- Claim: `054b234ddca49006d11eab7024be0db76ee34eaf31a2c5a36f0f4f21ca938cb5`
- Main-sync commit: `c17d14108e0ab88ca11c221bf05191d3b87c924f`
- Implementation/repair head: `bb0f7ae285ae3617f29a16a2ca6216a0e6e4bf01`
- PR: [KNaiFen/gkd#8](https://github.com/KNaiFen/gkd/pull/8)
- Accepted execution bundle: `1983f05b64860510bfb1af661e5458a6c7b660632479a33af46c27d35ff188d4`
- Candidate output bundle: `e49f6bf994a3dea405248535ffdd70473feacd13c27ae39a6ecfc1fabd9a7efd`

本交付只实现 M3-A：通用仓库 CI policy、GitHub origin/base 一致性、固定头只读
terminal monitor、标准 Actions workflow 与同一版本化本地验证入口。M3-B 资源与
scanner、M3-C review core 与新 Skills 均未实现。

## 实现

- `.gkd/policy.json` 使用严格 canonical JSON 与版本化 schema，声明 GitHub 仓库、
  base branch 和 required checks。parser 拒绝未知字段、非 canonical 内容、重复或
  非规范 check、路径穿越、policy/祖先 symlink、非 GitHub origin、歧义 remote、
  repository/base mismatch。
- installed `gkd-ci-monitor` 只接受显式 checkout/repository/PR/full head，policy、
  deadline 与轮询间隔，通过只读 GitHub adapter 获取 PR、check runs 与 status contexts；
  每次 observation 重验 policy/origin/base/head，head drift、缺失或 pending check、
  失败、API/transport error 和 deadline 均 fail-closed。
- monitor 使用版本化 path-free terminal JSON，拥有 bounded polling 并只返回一个终态；
  不 rerun、dispatch、cancel、编辑 PR metadata、accept 或 merge。
- `scripts/gkd-verify --base-sha <full-sha>` 验证 full base ancestry，在标准库隔离
  subprocess 中运行 M3-A 与 retained short contracts。`.github/workflows/gkd-ci.yml`
  使用标准 `ubuntu-latest`、完整历史、只读 contents 权限和同一 verifier；policy/workflow
  required check 均为 `GKD Verify`，不使用 Secrets、付费或 self-hosted runner。
- 首次 GitHub-hosted Linux CI 以 `FORBIDDEN_SOURCE_CONTENT` 和平台缺失 `/Users` 事实
  失败；repair head 使用构造式临时路径别名并将 retained migration fixture 改为
  `Path.home()`，未扩大 M3-A 行为范围。旧失败 head 不再重跑。
- canonical source/manifest/lock 已由生成器更新为 60 个 payload 文件。

## 验证

本地唯一版本化 verifier：

`scripts/gkd-verify --base-sha d669c11735f1468127ce4b7b4699a19ef0984753`

终态为 `362/362`：M3-A `29`、task-core `126`、role-routing `70`、runtime-bridge `37`、
foundation `53`、watcher-core/live-negative `47`。未安装依赖，未运行历史 live probe、
M2-B 一小时实验、大型构建或 cache。

M3-A evidence 在两个互不相交的干净系统临时根生成，均为 `29/29` 且逐字节一致：

- Evidence digest: `a2ffc693a75780aa893538462bf6a1a2428f2d55d0c68d138b33f4a288cd1c5b`
- Evidence file SHA-256: `93b9e6b365f6fa832485183e0dcf83ab293e27804d5d087f1c438720474ba181`
- Production before/after: `957e7ddbb7ed95e79f0774c131421514473bbd5e50939668803b038ced31434e` (`2295` entries)
- AIO before/after: `27358a2dcde47816b6dd213005167645b0a86644693e446ca4da8c1c656d98c3` (`15675` entries)
- 两个 evidence temporary root 结束为空。

repair head `bb0f7ae285ae3617f29a16a2ca6216a0e6e4bf01` 的 policy-backed monitor 返回：

- Outcome: `success`
- Reason: `ALL_REQUIRED_CHECKS_SUCCESSFUL`
- PR/head: `8` / `bb0f7ae285ae3617f29a16a2ca6216a0e6e4bf01`
- Required checks: `GKD Verify` = `success`
- Policy digest: `d77e68152843dcc1f470d88c76fe8c249ef803854048f4a9d42ed5cc92cd54c2`

## 停止边界

本 session 停在 exact claim delivery 与 trusted-main 独立验收之前：不验收、不合并、
不归档、不清理 worktree/branch、不启动 M3-B，不修改生产 `~/.codex`、AIO、sandbox、
仓库设置、Secrets、runner、tag 或 Release。
