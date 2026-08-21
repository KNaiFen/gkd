# GKD-M3-C 交付

## 结果

- Outcome: `review_core_ready`
- Fixed base: `6b3f28aa8f1f1308fbb45064f5b96128837e4c4f`
- Claim base head: `5e4f839986cf2df15d720b050e682e0c33e73ca7`
- Claim: `e7af0e81458cc49a4a0a55210b79eebc76e2c06c6f3f6d046f74724904b2a707`
- Activation: `7758ff0078489dd8d38aab1052b579ac2d1db0c9246353ee4d9215a57787256e`
- Envelope: `e30d8f31992d2f6290abd79ea218ad0f97bb37152773f95eb35691a1d10e24f3`
- Implementation/evidence commit: `6f2ded0a0902077f8a465412d9536a89c61ca777`
- PR: [KNaiFen/gkd#18](https://github.com/KNaiFen/gkd/pull/18) (Draft)
- Accepted execution bundle: `5f68703a42df613125814d78a491cb1991620afcb915d5a486c6ea6334604129`
- Candidate output bundle: `b93568270185a44d5a39855a50e354eb22624ad9d7e4a896e87b0aff99d98487`
- Evidence digest: `816c9cb9bac95f31472fb84e821d13229ff54346830255a5a19c4430c069c2f9`
- Evidence file SHA-256: `26eeb0b2a05308c43d78b7a0da70f274fdef97dd0e7894f292adfd8743124843`
- Role/config/route digests: `e21916be7aa65313cf83dda521850a8f91d746e520b240356f9a08232cfae29a` / `10c0675808974609242280367f2e7aea07e61dd839a1ec2e244d53a9b6c74e3e` / `70376b685e04318e2ab761d4a4ec3f1640105aaaac3424b5d41864ec4174426c`

本交付只实现 M3-C：共享 review core、`gkd-optimize-ci`、
`gkd-review-remediation`、七 Skill bundle 收口、通用多仓库 adapter schema 与脱敏
fixture。M3-A policy/monitor、M3-B resource/scanner 语义、M4/M5、生产 `~/.codex`、
AIO、Secrets、付费 runner、计划外 GitHub settings、tag 与 Release 均未修改或实现。

## 实现

- `gkd_review.core` 提供 targeted、guided、recon 入口，模糊意图停在 clarification，
  并以 canonical digest 保存 partial approval、显式 resume 与 recovery 的 review state。
- `gkd_review.remediation` 仅允许脱敏 finding、显式 partial approval、resume 和 recovery，
  不写 merge、rerun、dispatch 或 settings 状态。
- `gkd_review.adapter` 绑定多个 repository identity、provider、branch、policy path 与
  capability facts；所有 fixture 与机器输出拒绝 credential-shaped 数据和本机绝对路径。
- 新增 `gkd-review` machine CLI、review state/recommendation/remediation/adapter schemas、
  两个 workflow Skills，并将 manifest、lock、role inventory 与 project staging 更新为七个
 唯一 Skill。
- 新增 11 项 review core/mutation contracts 与 deterministic evidence runner；保留 M3-A、
  M3-B 既有实现和语义。

## 验证

唯一版本化 verifier：

`scripts/gkd-verify --base-sha 6b3f28aa8f1f1308fbb45064f5b96128837e4c4f`

终态为 `389/389`：M3-A `29`、M3-B `14`、M3-C review core `11`、task-core `128`、
role-routing `70`、runtime-bridge `37`、foundation `53`、watcher-core/live-negative `47`。
运行环境为 Python 3.14.6；未安装依赖，未运行历史 live probe、真实一小时等待、大型构建或
cache。

M3-C evidence 两次生成逐字节一致：

- Contract count: `11`
- Candidate output bundle: `b93568270185a44d5a39855a50e354eb22624ad9d7e4a896e87b0aff99d98487`
- Evidence digest: `816c9cb9bac95f31472fb84e821d13229ff54346830255a5a19c4430c069c2f9`
- Evidence file SHA-256: `26eeb0b2a05308c43d78b7a0da70f274fdef97dd0e7894f292adfd8743124843`
- `machinePathsRetained`: `false`

## 停止边界

PR #18 当前为 Draft，fixed-head `GKD Verify` 尚未由本 session 运行或宣称成功。本 session
停在 exact claim delivery 与 trusted-main 独立验收之前：不验收、不合并、不归档、不清理
worktree/branch、不启动 M4/M5，不修改生产 `~/.codex`、AIO、Secrets、runner、GitHub
settings、tag 或 Release。
