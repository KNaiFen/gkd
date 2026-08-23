# GKD-R4 验收

## 结论

- Outcome: `released_and_project_restage_verified`
- Pull request: `KNaiFen/gkd#28`
- Fixed base: `3133e35df8dd520e2976116e6468761eef6d84df`
- Accepted fixed head: `7eea74239e3ea258f7f81e3f2eda2c14f69433fd`
- Squash merge: `2a63cd8ff2fcb7f0cb155dcc32578cda4b3381af`
- Version/bundle digest: `0.1.3` /
  `cc465d26f08edb2a133775e4d6a58aa517eab1bde0ec2e1ec72f6d9f2c8883bd`

## 独立核对

- requirements、plan、implementation、delivery 与完整 `3133e35..7eea742` diff 均在范围内。
- 两个 clean temporary root 的 release contracts 均为 `15/15`，提交 evidence 的
  file SHA-256 为 `782d743beb0494ecb033fbc9f406f7c5fb64340d0a63838e4c636ad25f3926de`，
  self-excluding evidence digest 为
  `306b5d979b3c202352212b6852809457df1cff3694c22a15a2279c4237af0a1b`。
- registered base 上的完整 verifier 为 `424/424`。PR #28 的 `GKD Verify` 在 exact
  fixed head 成功，required check 为 `GKD Verify`。
- 独立审查未发现阻塞项：`0.1.3` propagation 与历史版本兼容；watchdog PID publication
  和 task fixture temporary Git teardown 的 Linux 竞态修复仅限测试基础设施，均有界且不吞掉
  其他错误。

## Bootstrap 边界

本任务以已发布 `v0.1.2` runtime 建立 R3 自托管 release candidate，保持 documented manual
bootstrap exception。`task.json` 保持 planning，未创建或补造 offer、claim、delivery、activation
或 receipt，也没有调用 public automatic lifecycle CLI。

## 发布门与 Restage

- Release candidate/L3 record digest：
  `bd315e26c585ecc4412632385baaceea2d9979d95f8765c67846a24df8a34263` /
  `ab28d7a76bafce21caf82359da2a2e6db90e0cb0e655f37710fefb34aaa1c222`。
- L4 sandbox PR [#6](https://github.com/KNaiFen/gkd-sandbox/pull/6) fixed head 为
  `2f322915d471218154902ae1931a89fc9c36f72a`，`GKD Canary` success。L4 request/observed
  digest 为 `90a7db7a76c7f7589e1e87b2255f28d1a6820864c9e1995678284148b5274fa5` /
  `fd00d16ae4715d1b23d4ebf8d77fe1b00b6da9205b6a38a947df455557fb6deb`。
- Final record/provenance digest：
  `8a5c4738d1748bf13b6f733f297d905bbd617d89f2e1ff179dd0dcb82f455dae` /
  `57d146f2f5fda8c86d33d1c565d1536b5bf0cae777f010a88f8cf1b69b6e7c32`。
- Annotated `v0.1.3` tag 与 GitHub Release 都精确指向 source merge
  `2a63cd8ff2fcb7f0cb155dcc32578cda4b3381af`。asset
  `gkd-0.1.3-final-2a63cd8.tar.gz` SHA-256 为
  `9d9e6ea0fff64e0894af08a547b6798f1f6634e0e4cf4e174cd8dfc5c0179954`；回下载、解包和
  asset-local install/verify 均返回 `0.1.3`、103 files 与 candidate bundle digest。
- 旧 `v0.1.2` project staging 先以旧安装态 verified，再按 inventory 移除；回下载 asset
  已重新 stage/verify project，inventory digest 为
  `37cc3ab1cc1967583a404e1c992eac02bb6c7f29eabbb36ec5b7ac60dc0b6eda`，并包含 R3 的
  `.gkd/policy.json` binding。

production、AIO、GitHub settings、Secrets 和 paid runner 均未写入。AIO adoption 现在只可从
已发布且已 restage 的 exact bundle 开始不写入 inventory/mapping。

## 清理

验收记录提交并推送后，候选 worktree
`/Users/knaifen/Documents/Codex/gkd-worktrees/r4-release-policy-binding`、本地
`task/r4-release-policy-binding` 分支和同名远端分支均已删除。PR #28、squash merge、任务文档
和验收记录保留为历史事实。

sandbox PR #6 在 `GKD Canary` fixed-head success 后已关闭，`gkd-canary/2a63cd8ff2fc` 远端分支
已删除。R4 的 temporary release/runtime/evidence/install roots 与 CI 日志均已删除；`v0.1.3`
tag、Release、asset、main records 和 project-local staging 保留。
