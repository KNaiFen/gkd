# GKD-GATE-REPAIR-R2 Acceptance

## Outcome

Rejected. PR #41 fixed head `feada4cb6a5980a2ba901643c1e313d35056b500` 未合并。

## Evidence

- trusted main 和 candidate 均能读取 state：`status` 为 delivered/revision 6，`doctor --mode static` 为 valid；完整 verifier 438/438、`git diff --check` 和 fixed-head `GKD Verify` 均通过。
- review digest：`5dc2bc7e62d6f50d4127722fe548a3a3eae5470acf08f32edd0340e4cf10a7a4`。
- old trusted acceptance 在 `acceptance.py` 要求 delivery document commit 的父提交精确等于 lifecycle `implementationHead`。R2 state 的 implementation head 为 `4091ca53ed58c97ca27f58779d724a4ecddc0a78`，但 delivery document commit `e495bcdfd3c5f9eb25cd4427866df30748b53842` 的父提交是 sidecar commit `cdf013d...`，canonical accept/rework 前置返回 `CANDIDATE_INVALID`。
- sidecar 的 verifier result/evidence digest 没有通过服务从实际结果/证据文件重算或验证；改变两项并重算 manifest digest 仍可被候选实现接受，未满足 drift fail-closed 要求。

## Boundary

未调用 accept 或 rework；candidate、runtime、production、AIO 和 GitHub settings/Secrets 未修改。该 attempt 不得复用。

