# GKD-O3 交付

## 结果

- Outcome: `verifier_result_reuse_ready`
- Fixed base: `992c4dfddc2f5cb6c337d07d5407297bc1d1996c`
- Claim base head: `18881ff353f24c0c7980d0787269ec9237006905`
- Claim: `19a0981afb690ca3bfe79bc3c54876293022095e34a42366a7bd032c3cfa4bab`
- Implementation head: `36b08643b425c7c46a8d14e0cf054c755a39eb80`

本交付建立了版本化 canonical scope result：`gkd-verify --results-dir`
对 11 个 scope 的行为测试各执行一次，写出绑定 base/head、scope、完整 test ID、
逐项状态、环境摘要和 digest 的结果；evidence/contract runner 通过
`--canonical-results` 显式消费并重新校验结果。缺失、篡改、base/head、环境、test
ID 或 digest 漂移均 fail-closed。原有 protected surface、temporary/output、安装、
manifest/lock、路径和凭据边界保持不变；watcher/probe、fixture、optional pack、
生产、AIO、settings、Secrets、runner、tag 和 Release 未修改。

## 证据

- Execution bundle digest: `273873360cb7e3115a54dfef7e6840611457cc8c4d3af80384670b32630f1dc0`
- Candidate output bundle digest: `03aa8dbbc42d7bd610b17adb3c0e46cc6b1d73ac4dde3bca095cea77e14a1b58`
- Canonical results manifest digest: `bd0d16c0eba177d4682ca9ed67786a958a53cbb5dfcec4ee8c2f2ccbb10f7af8`
- O3 evidence digest (two runs): `ce2670f040d47c326999f21e12b0f923c9353a33c73a2b25a43ff0fd49a9016d`
- O3 evidence file SHA-256 (two runs): `bb6a804b6085d03409d2ebecfeaab41a2ca5a6cd7d6c0c0dd1c4eee56cd22cde`

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

