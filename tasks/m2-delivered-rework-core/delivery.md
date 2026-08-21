# GKD-M2-D 交付

## 结果

- Outcome: `delivered_rework_core_ready`
- Fixed base: `5cc7f6bbc61c2a06ecdf2104a6e7cd3129f23959`
- Claim head: `f5b0c4a366880a9716c3c6fce86191edd079c418`
- Implementation commit: `c0ee720cce21500faf5ef396c5e5a985498caeff`
- Evidence commit: `c41e35e420e3bc05b7fd23149a956403a0a5732c`
- PR: [KNaiFen/gkd#9](https://github.com/KNaiFen/gkd/pull/9)，Ready
- Checks: 当前 `statusCheckRollup=[]`，不表述为 CI 成功

本交付只补齐 delivered fixed head 被 CI 或独立审查拒绝后返回授权 planning
的确定性事务。它不实现 M3 policy/monitor、资源/scanner、review Skills、finalization
或 release 功能，也没有修改 PR #8/M3-A 候选。

## 实现

- task state v2 增加不可变 `rejectedAttempts` 与 `reworked` history event；既有
  schema-v1 任务继续原样读取，只有首次成功 rework 才升级写入 v2。
- trusted `gkd-task rework` 只接受 clean synchronized main、独立 candidate
  worktree、完整 delivered head、canonical rejected review、明确 PR 与 runtime root。
  executor/candidate 调用在任何 tracked/runtime/GitHub 写前 fail-closed。
- rework 复用 fixed candidate、authorization、claim journal/receipt、automatic
  activation receipt 与 subprocess GitHub adapter 校验；两次 snapshot 必须逐字段一致，
  draft/closed/merged/head/repository/base/branch/PR 漂移均拒绝。
- 成功事务只提交 task/offer coordination files：保存旧 offer、claim、delivery、
  execution/output bundle、route decision、claim/activation receipt、review/finding、
  rejected head/PR/time 摘要；撤销旧 offer、退休旧 claim/delivery、epoch 加一、清空 active
  writer/offer/claim/delivery/acceptance 并回到已授权 planning。
- 旧 capability/envelope/claim 不可重用。fresh automatic repair 必须生成新的
  offer/envelope/activation/claim/epoch；新 delivery 后原 fixed-head acceptance 语义不变。
- transaction lock、head/revision CAS、prepared journal 与 recovery 保证并发仅一名赢家，
  pre-commit 中断恢复 exact bytes，committed 中断不会重复 history。
- 新增 `scripts/gkd-verify --base-sha <full-sha>`，确定性要求 Python 3.11+、验证 base
  ancestry，并只运行批准的 M1/M2 short contracts 与 live-negative tests。

## 摘要

- Accepted execution bundle: `05288d5b09bdd8b4703a45d8a300d9466ad59f6b414d8eb5684c4a214ecfaaad`
- Candidate output bundle: `71c4b2d3562c2e5a6a784bf3436a7d5920cd00b3ad387f320a2563d4b5b88766`
- Evidence digest: `da884bc1efe152ed983deda4c04d02bf95eafad17b2f61bd2f2067b729a2324d`
- Evidence file SHA-256: `304a76c876677660fab22afded03c9257ed023fefc2673d05235defb281fc121`
- Evidence implementation head: `c0ee720cce21500faf5ef396c5e5a985498caeff`

execution bundle 与 candidate output bundle 分离且不相等；本任务 delivery 必须继续把
前者保留在 claim/delivery，并单独传入后者。

## 验证

`scripts/gkd-verify --base-sha 5cc7f6bbc61c2a06ecdf2104a6e7cd3129f23959`
在 exact implementation head 上通过：

| Contract | Result |
| --- | ---: |
| Task core（含 11 rework L1/L2 + 3 mutation） | 118/118 |
| M2-C runtime bridge | 32/32 |
| M2-A role routing | 70/70 |
| Foundation | 53/53 |
| Watcher core | 47/47 |
| Watcher live-negative | 15/15 |

M2-D evidence 另在两个互不相交的系统临时根各运行 118 项 task-core；两份输出逐字节
一致，文件 SHA-256 均为 `304a76c876677660fab22afded03c9257ed023fefc2673d05235defb281fc121`，
两个运行根结束为空。生产保护摘要 before/after 均为
`957e7ddbb7ed95e79f0774c131421514473bbd5e50939668803b038ced31434e`
（2295 entries）；AIO before/after 均为
`27358a2dcde47816b6dd213005167645b0a86644693e446ca4da8c1c656d98c3`
（15675 entries）。未安装依赖，未运行历史 live probe、真实一小时等待或大型构建。

## 停止边界

本 session 仅提交、推送、维护 PR #9 并通过 accepted `gkd-task deliver` 写入 delivery
facts。随后固定并报告本地/upstream/PR 的同一完整 head，停止于独立验收前。不验收、
不合并、不归档、不清理、不启动 M3-A 返工，不修改 PR #8、生产 `~/.codex`、AIO、
付费 runner、Secrets、仓库设置、tag 或 Release。
