# GKD-R6 Runner Binding Release 交付

## 结果

- Outcome: `runner_binding_release_candidate_ready`
- Fixed base: `c38e3a3d5a88b87beb13ff38fdefb82fa3416f6e`
- Claim base head: `1241b8df53a9cd9f8a6e935a9fadc51b23bff128`
- Claim: `ad981da5d59538ec14cdaf749f4e612db4832c907732b29c14af62af7bebaf0e`
- Implementation/evidence commit: `093ea72fe980c01d526386d3d9b82af2e808488c`

本交付将已验收的 R5 runner-resource binding 升级为稳定 `0.1.4` release
candidate。没有修改 R5 resource semantics、task bridge、workflow、production、AIO、
GitHub settings、Secrets 或 paid runner。

## 实现

- `canonical/source.toml` 声明 `0.1.4`，canonical generator 已重建 manifest 与
  lock。
- L1 release property 保留 `0.1.1` 至 `0.1.3` 的历史 tag propagation，并加入
  `0.1.4`；当前 release fixture 和 mutation contract 绑定 `v0.1.4`。
- 两次 release-contract 运行生成同一 canonical evidence，不包含 capability、运行时
  identity、prompt、transcript、credential 或机器路径。

## 摘要与证据

- Accepted execution bundle: `cc465d26f08edb2a133775e4d6a58aa517eab1bde0ec2e1ec72f6d9f2c8883bd`
- Candidate output bundle: `cdaa791ace82a5e7c407b29a93a4211b852d7f364900bbcd8a549dbe918bf2a7`
- Release-contract evidence digest: `b5f1c85cf9e274e31cb9bebe96ee0276c5e3ee5a54679abad72d4c6d70377ef1`
- Evidence file SHA-256: `9be6fdf6da5933b98f5957837c8db4ba63570a3757290cb8bc528530196632d3`
- Evidence: `evidence/r6-runner-binding-release/release-contracts.json`

## 验证

```text
PYTHONDONTWRITEBYTECODE=1 scripts/gkd-verify --base-sha c38e3a3d5a88b87beb13ff38fdefb82fa3416f6e
```

终态为 `pass`，11 个 scope 共 429 项：release candidate 15、finalization 9、CI policy
29、resource scanner 19、review core 11、task core 130、role routing 71、runtime bridge
39、production migration 6、foundation 53、watcher 47。未安装依赖、未运行 live gate、
未修改 runner、GitHub settings、production 或 AIO。

## 停止边界

本文件单独提交后，executor 仅调用 `gkd-task deliver` 绑定该文档与 candidate output
bundle。终态协调提交会成为唯一后续提交；executor 停在固定 head，不验收、不合并、不归档、
不清理 worktree 或分支、不启动其他任务，也不创建 tag、Release、runner、Secrets、production
或 AIO 变更。只有 trusted main 完成独立验收与 exact merge 后，才可执行既有 post-merge
release gate、promotion 和 isolated restage。
