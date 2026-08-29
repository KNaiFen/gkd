# GKD-GATE-REPAIR-R2 交付

## 结果

- Outcome: `gate_repair_r2_ready`
- Fixed base: `62ea7d901c746f491c8d42b2e6c11d23e2c1464d`
- Claim base head: `4c5ecd66c0f65025007db3c2f4096c71b1165b87`
- Claim: `9fe3a136a6592b900c0dddc2a500552d23fd0fbfd220522521e428c377d6080d`
- Implementation head: `4091ca53ed58c97ca27f58779d724a4ecddc0a78`
- Result-manifest commit: `cdf013d69c34b58ac845bceb5a2db6bdad32871a`

本交付以既有 immutable history revision 作为生命周期逻辑顺序；UTC 字段仍作为
审计事实，但 wall-clock 回拨不再决定有效性。`planning-refresh` 是仅限 planning 的
CAS transition，会原子重算三份规划文档及 plan material digest；R2 自身没有调用它，
因此 task state 继续保持 merge 前 trusted-main validator 可读的既有 event 与 delivery
record 形状。

automatic delivery 固定为四段提交关系：implementation、只改
`result-manifest.json` 的 sidecar、只改本文件的 delivery document，以及由
`gkd-task deliver` 写入的 final coordination commit。sidecar 绑定 task/repository/base、
implementation head、candidate output bundle、canonical verifier result 和 evidence
digest；service、acceptance 与 rework 由既有 implementation head 和 candidate output
bundle digest 推导验证，不向 task state 添加字段。

## 证据

- Execution bundle digest: `06095243b2199672243b559e0af2798fb9e051e33281775b98bc68c8b16ac48a`
- Candidate output bundle digest: `a6e25aec636fa2893064b2d2acc6a9aa0f74595aecea1844d85f3bdd542533e3`
- Canonical results manifest digest: `d8b20a814b1da5f9f8da901ed51bc9397d5001d3166ea0689c91baa3c6e24880`
- Task-core evidence digest: `68f875a103e8ab03eb4f435bb363a0a5e01337e74dcdb2d45e105f1ff08879e8`
- Result-manifest digest: `b398609c10d8d457ca029cc950877a713424f09188cefa70dac88b83a67e4de3`

完整 verifier 返回 438/438：`foundation` 52、`m3-ci-policy` 29、
`m3-resource-scanner` 19、`m3-review-core` 11、`m4-finalization` 9、
`m5-release-candidate` 15、`p1-production-migration` 6、`role-routing` 71、
`runtime-bridge` 39、`task-core` 140、`watcher-core-and-live-negative` 47。task-core
evidence 使用同一 canonical results 重新绑定，返回 140 contracts；输出不含 runtime
身份、凭据、提示词、transcript 或机器路径。

## 验证

```text
python3.14 canonical/payload/bin/gkd-task status --repository github.com/KNaiFen/gkd --task-id GKD-GATE-REPAIR-R2 --task-branch task/gkd-gate-repair-r2 --task-path tasks/gkd-gate-repair-r2 --candidate-root <candidate-root> --runtime-root <runtime-root>
python3.14 canonical/payload/bin/gkd-task doctor --repository github.com/KNaiFen/gkd --task-id GKD-GATE-REPAIR-R2 --task-branch task/gkd-gate-repair-r2 --task-path tasks/gkd-gate-repair-r2 --candidate-root <candidate-root> --runtime-root <runtime-root> --mode static
PYTHONDONTWRITEBYTECODE=1 python3.14 scripts/gkd-verify --base-sha 62ea7d901c746f491c8d42b2e6c11d23e2c1464d --results-dir <results-dir>
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=canonical/payload/lib:. python3.14 tests/task_core/run_contracts.py --output <output> --temporary-root <temporary-root> --protected-root <protected-root> --canonical-results <results-dir>
```

## 停止边界

本文件单独提交后，executor 仅调用 `gkd-task deliver` 绑定本文件、预提交 sidecar 和
candidate output bundle digest。delivery transition 是本分支的最后一个提交；之后不再
修改、提交、验收、合并、归档或清理，后续 fixed-head CI、独立 acceptance 与 trusted-main
处理由其他角色完成。
