# GKD-O3 交付

## 结果

- Outcome: `verifier_result_reuse_ready`
- Fixed base: `992c4dfddc2f5cb6c337d07d5407297bc1d1996c`
- Claim base head: `dc3b85425e1b0332b549ceb9c1f2b0448020b0d3`
- Claim: `ba97dd58513c3675941791a86df4b59145b2b0b83cde6dbf9d15c7b145acd0ef`
- Implementation head: `7643c0ec5f07ee4b8301d4b0d8da84850ab96a0b`

本交付建立了版本化 canonical scope result：`gkd-verify --results-dir`
对 11 个 scope 的行为测试各执行一次，写出绑定 base/head、scope、完整 test ID、
逐项状态、环境摘要和 digest 的结果；evidence/contract runner 通过
`--canonical-results` 显式消费并重新校验结果。缺失、篡改、base/head、环境、test
ID 或 digest 漂移均 fail-closed。原有 protected surface、temporary/output、安装、
manifest/lock、路径和凭据边界保持不变；watcher/probe、fixture、optional pack、
生产、AIO、settings、Secrets、runner、tag 和 Release 未修改。

## 证据

- Execution bundle digest: `273873360cb7e3115a54dfef7e6840611457cc8c4d3af80384670b32630f1dc0`
- Candidate output bundle digest: `06095243b2199672243b559e0af2798fb9e051e33281775b98bc68c8b16ac48a`
- Canonical results manifest digest: `62ebbe2d61f2c8bd3f583b85814d26b690057a9b24e7b7428c2f9ec62f4574ce`
- O3 evidence digest (two runs): `10d660679fd52ec7e6866b51b88b050e80f2e08884cc0ded0e06531dc37f9270`
- O3 evidence file SHA-256 (two runs): `dbf2b65e4384da8d63bd260350a56dd91661960b9f1667677ddf2020c2d1ae08`

完整 verifier 返回 433/433：`foundation` 52、`m3-ci-policy` 29、
`m3-resource-scanner` 19、`m3-review-core` 11、`m4-finalization` 9、
`m5-release-candidate` 15、`p1-production-migration` 6、`role-routing` 71、
`runtime-bridge` 39、`task-core` 135、`watcher-core-and-live-negative` 47。
两个独立根的 O3 evidence 均为 `verifier_result_reuse_ready`、433 tests，逐字节一致；
task-core 与 foundation consumer 均成功且无 unittest 输出，证明行为测试由 canonical
runner 执行一次后被消费。

## 验证

```text
gkd-task status --repository github.com/KNaiFen/gkd --task-id GKD-O3 --task-branch task/gkd-o3-verifier-result-reuse --task-path tasks/gkd-o3-verifier-result-reuse --candidate-root . --runtime-root <runtime-root>
gkd-task doctor --repository github.com/KNaiFen/gkd --task-id GKD-O3 --task-branch task/gkd-o3-verifier-result-reuse --task-path tasks/gkd-o3-verifier-result-reuse --candidate-root . --runtime-root <runtime-root> --mode live
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/gkd-verify --base-sha 992c4dfddc2f5cb6c337d07d5407297bc1d1996c --results-dir <results-dir>
PYTHONDONTWRITEBYTECODE=1 python3 -B tests/verification_results/run_evidence.py --canonical-results <results-dir> --output <output> --temporary-root <temporary-root> --protected-root <protected-root>
```

验证使用 Python 3.14.6；未安装依赖。结果和 evidence 输出不含机器绝对路径、凭据、
原始日志或 runtime 身份。

## 停止边界

本文件单独提交后，executor 仅调用 `gkd-task deliver` 绑定本文件、实现提交和
candidate output bundle digest，然后停止；不验收、不合并、不归档、不清理 worktree
或分支，不启动其他任务。后续 fixed-head CI、独立验收、trusted main 合并和收尾由主会话完成。
