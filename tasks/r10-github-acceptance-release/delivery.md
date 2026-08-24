# GKD-R10 GitHub Acceptance Release 交付

## 结果

- Outcome: `github_acceptance_release_candidate_ready`
- Fixed base: `790d592d63c7c34a0047f136e18fa15238e722d6`
- Claim base head: `1a0f5fe11abf6f99127b0b5d180e4a90c2265728`
- Claim: `ef8ca827d4538deb9ca1f58fbe32f94d8ddecf100a9651bd80d518e8d034d91d`
- Implementation/evidence commit: `7e6504c6aa1fc837283518f2d81d0d7d992f3fec`

本交付将已验收的 R9 GitHub acceptance 与 delivery sequencing repair 升级为稳定
`0.1.5` release candidate。没有修改 R9 acceptance 行为、task bridge、workflow、
production、AIO、GitHub settings、Secrets 或 paid runner。

## 实现

- `canonical/source.toml` 声明 `0.1.5`，canonical generator 已重建 manifest 与
  lock。
- L1 release property 保留 `0.1.1` 至 `0.1.4` 的历史 tag propagation，并加入
  `0.1.5`；当前 release fixture 和 mutation contract 绑定 `v0.1.5`。
- 两次 release-contract 运行生成同一 canonical evidence，不包含 capability、运行时
  identity、prompt、transcript、credential 或机器路径。

## 摘要与证据

- Accepted execution bundle: `cdaa791ace82a5e7c407b29a93a4211b852d7f364900bbcd8a549dbe918bf2a7`
- Candidate output bundle: `d749b753fb11aeab44d41b4e1d8bec44c7fa2d18a4b08148fbc0e0c127e27e6d`
- Release-contract evidence digest: `0d1f78e4efd4e759ab694b3712b32699a8dcea48e1a045261d9c64e351514ffb`
- Evidence file SHA-256: `4efddb1dbd940c864b6cf80c4141d36aba7aaeefd5e40e2b8bf74913b781baff`
- Evidence: `evidence/r10-github-acceptance-release/release-contracts.json`

## 验证

```text
PYTHONDONTWRITEBYTECODE=1 scripts/gkd-verify --base-sha 790d592d63c7c34a0047f136e18fa15238e722d6
```

终态为 `pass`，11 个 scope 共 434 项：release candidate 15、finalization 9、CI policy
29、resource scanner 19、review core 11、task core 135、role routing 71、runtime bridge
39、production migration 6、foundation 53、watcher 47。未安装依赖、未运行 live gate、
未修改 runner、GitHub settings、production 或 AIO。

## 停止边界

本文件单独提交后，executor 仅调用 `gkd-task deliver` 绑定该文档与 candidate output
bundle。终态协调提交会成为唯一后续提交；executor 停在固定 head，不验收、不合并、不归档、
不清理 worktree 或分支、不启动其他任务，也不创建 tag、Release、runner、Secrets、production
或 AIO 变更。只有 trusted main 完成独立验收与 exact merge 后，才可执行既有 post-merge
release gate、promotion 和 isolated restage。
