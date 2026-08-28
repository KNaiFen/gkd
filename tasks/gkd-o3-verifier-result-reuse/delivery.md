# GKD-O3 交付

## 结果

- Outcome: `verifier_result_reuse_ready`
- Fixed base: `992c4dfddc2f5cb6c337d07d5407297bc1d1996c`
- Claim base head: `dc3b85425e1b0332b549ceb9c1f2b0448020b0d3`
- Claim: `ba97dd58513c3675941791a86df4b59145b2b0b83cde6dbf9d15c7b145acd0ef`
- Implementation head: `1f30cdb4f00c8a8eea414fc0be1491b54ad129bf`

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
- Canonical results manifest digest: `b2361f90d1a752d185b1d83d4b9a606d4407aa38f8a5c3f4d8f950a79f52cd26`
- O3 evidence digest (two runs): `416c4c4a340cbfd34b40d37746888363959abd03a4eb5d9bf8771470f5740408`
- O3 evidence file SHA-256 (two runs): `d555fedca01eff7bcfeaf9e263af0901cb747f9f6fc16aad7dac9d1562a4b41a`

完整 verifier 返回 433/433：`foundation` 52、`m3-ci-policy` 29、
`m3-resource-scanner` 19、`m3-review-core` 11、`m4-finalization` 9、
`m5-release-candidate` 15、`p1-production-migration` 6、`role-routing` 71、
`runtime-bridge` 39、`task-core` 135、`watcher-core-and-live-negative` 47。
两个独立根的 O3 evidence 均为 `verifier_result_reuse_ready`、433 tests，逐字节一致；
task-core 与 foundation consumer 均成功且无 unittest 输出，证明行为测试由 canonical
runner 执行一次后被消费。watchdog consumer 的缺失结果返回
`CANONICAL_RESULT_MISSING`，未知 test ID 变异返回 `CANONICAL_RESULT_TEST_IDS_MISMATCH`，
均为 exit 2 且不写 evidence。

## 验证

```text
gkd-task status --repository github.com/KNaiFen/gkd --task-id GKD-O3 --task-branch task/gkd-o3-verifier-result-reuse --task-path tasks/gkd-o3-verifier-result-reuse --candidate-root . --runtime-root <runtime-root>
gkd-task doctor --repository github.com/KNaiFen/gkd --task-id GKD-O3 --task-branch task/gkd-o3-verifier-result-reuse --task-path tasks/gkd-o3-verifier-result-reuse --candidate-root . --runtime-root <runtime-root> --mode live
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/gkd-verify --base-sha 992c4dfddc2f5cb6c337d07d5407297bc1d1996c --results-dir <results-dir>
PYTHONDONTWRITEBYTECODE=1 python3 -B tests/verification_results/run_evidence.py --canonical-results <results-dir> --output <output> --temporary-root <temporary-root> --protected-root <protected-root>
```

验证使用 Python 3.14.6；未安装依赖。完整 verifier 返回 433/433：`foundation` 52、
`m3-ci-policy` 29、`m3-resource-scanner` 19、`m3-review-core` 11、`m4-finalization` 9、
`m5-release-candidate` 15、`p1-production-migration` 6、`role-routing` 71、
`runtime-bridge` 39、`task-core` 135、`watcher-core-and-live-negative` 47。结果和 evidence
输出不含机器绝对路径、凭据、原始日志或 runtime 身份。

## 停止边界

本文件单独提交后，executor 仅调用 `gkd-task deliver` 绑定本文件、实现提交和
candidate output bundle digest，然后停止；不验收、不合并、不归档、不清理 worktree
或分支，不启动其他任务。后续 fixed-head CI、独立验收、trusted main 合并和收尾由主会话完成。
