# GKD-M4-A 交付

## 结果

- Outcome: `finalization_release_mechanism_ready`
- Fixed base: `a1dad775ee9d652203ab18efb1378362772dcc4a`
- Claim base head: `84d08fbd9e595c48b732debf21502a3f7179f1dc`
- Claim: `670617abb104f0a934582364bec2757335704e5dbec28bd2e4eab78848f3266d`
- Activation: `452252ff93b9bf2d35e7cd5c49b6727ca31e92b8e0f9e550af66899d3fbb2456`
- Envelope: `858a4a5f9f0228cbddd28db63a0cd99417b0a22117b6cac83c5fc8e4f5cbde99`
- Implementation/evidence commit: `4dbfb5f1e4a5227cbcd8cf1d9b377dc4e6cada3f`
- PR: [KNaiFen/gkd#19](https://github.com/KNaiFen/gkd/pull/19) (Draft)
- Accepted execution bundle: `b93568270185a44d5a39855a50e354eb22624ad9d7e4a896e87b0aff99d98487`
- Candidate output bundle: `27470fc60cfa005a2784ac81f0aba07c4e50e2381bf057fe9b38aa8d016e1912`
- Evidence digest: `90e499d761517a65080eb46edcab588b07d275267d38c609274a6dab3e287170`
- Evidence file SHA-256: `09c91349e0d0e4c836e93ef95367517b8383f5b0272463cf6da9ccb82d685bf6`
- Role/config/route digests: `b7660cee9bdab5b1011ae9e92a2a817536f508ef1475a10cc53acd9a1d99c25b` / `d44d2286d0a01a7b0f82610c02a6ada9fb1dc74f05730b1e8629f784d68595d2` / `2c9cc20acb275acd06bf3622c5be2f67282a914078327094ca381e0eb165166f`

本交付只实现 M4-A：generic fixed-head acceptance 的同步 main 重验、最多两个 PR 的
finalization state、canonical version/lock/changelog/release-intent/evidence/asset/provenance
绑定，以及 same-SHA promotion request。M3 产品语义、M5 L3/L4 或 release candidate、生产
`~/.codex`、AIO、Secrets、付费 runner 和 GitHub settings 均未修改。

## 实现

- `gkd_task.acceptance` 在两次 GitHub snapshot 之间重新确认 trusted main 与远端 base
  完全同步，候选内容始终只按固定树数据读取，不导入或执行 candidate code。
- `gkd_finalization` 只构造和验证 canonical records：closeout-only 拒绝 product logic 与
  release side effects；release mode 必须绑定 adapter digest、authorization digest 与资产。
- 每个 task/finalization PR、exact main/source SHA、version、bundle lock、changelog、evidence、
  asset 和 provenance 都在同一 record 中交叉验证。promotion interface 只生成 exact-SHA
  request；相同 receipt retry 返回 `already-promoted`，没有 tag 或 Release writer。
- 新增 `gkd-finalize` 只读 CLI、strict schema、generic fixture、focused/mutation contracts 和
  versioned M4 verifier scope；candidate bundle 已验证为 `90` 个文件。

## 验证

唯一版本化 verifier：

`scripts/gkd-verify --base-sha a1dad775ee9d652203ab18efb1378362772dcc4a`

终态为 `399/399`：M4 finalization `9`、M3-A `29`、M3-B `14`、M3-C `11`、task-core
`129`、role-routing `70`、runtime-bridge `37`、foundation `53`、watcher-core/live-negative
`47`。使用 Python `3.14`，未安装依赖、未运行 historical live probe 或一小时 wait。

M4 evidence 在两个独立根逐字节一致：

- Contract count: `9`
- Candidate output bundle: `27470fc60cfa005a2784ac81f0aba07c4e50e2381bf057fe9b38aa8d016e1912`
- Evidence digest: `90e499d761517a65080eb46edcab588b07d275267d38c609274a6dab3e287170`
- Evidence file SHA-256: `09c91349e0d0e4c836e93ef95367517b8383f5b0272463cf6da9ccb82d685bf6`
- `machinePathsRetained`: `false`

## 停止边界

PR #19 当前为 Draft，fixed-head `GKD Verify` 尚未由本 session 运行或宣称成功。本 session
停在 exact claim delivery 与 trusted-main 独立验收之前：不验收、不合并、不归档、不清理
worktree/branch、不启动 M5，不修改生产 `~/.codex`、AIO、Secrets、runner、GitHub settings、
tag 或 Release。
