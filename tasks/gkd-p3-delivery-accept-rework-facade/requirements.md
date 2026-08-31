# P3 交付、CI、验收与返工外观需求

## Goal

让正常任务只提交实现意图、独立审查结论和明确外部动作授权；交付、固定头 CI、验收与返工所需的路径、摘要、CAS、仓库和角色事实由 trusted main 从当前 task state、project inventory、policy 与 PR 状态派生。

## Fixed baseline

- trusted main：`142429bb0d70717afc92a2740832a111a186a16b`
- accepted execution bundle：`f387dff79dd58acca465c1715e6676e38f618c71a47ae4fa07de56123efc686a`
- project inventory：`aa4244457319a3ccf4e412898145f731aa89de2781e89f6f5c2160c91756d4c0`
- repository policy：`.gkd/policy.json`，required check 为 `GKD Verify`

## Scope

1. trusted-main delivery facade 从 task state 和 fixed candidate tree 推导 delivery document、result/evidence、claim 和 bundle/output digests；Agent 不再填写 delivery claim/path/digest/result/evidence 参数。
2. CI facade 从 trusted checkout 的 origin、base branch 和相对 `.gkd/policy.json` 派生 monitor 输入；保留 exact PR/head、required checks 与 bounded terminal。
3. acceptance/rework facade 从 delivered state、project policy、PR snapshot 和 independent review 派生 roots、repository、checks、actor role 与 candidate head；只接受明确 merge/rework 意图。
4. 保留现有 fixed-head、双 snapshot、独立 review、CAS、authorization、rework epoch 和 fail-closed 语义；旧低层 CLI 继续可读并保持拒绝错误。

## Non-goals

- 不修改生产 `~/.codex`、AIO、GitHub settings/Secrets、付费 runner、tag、Release 或 deployment。
- 不实现文档 renderer、planning schema migration 或低层 CLI 删除；这些属于 P4/P5。
- 不接受模糊 PR/head、缺失 review、缺失 checks 或调用者提供的替代 digest。

## Acceptance criteria

- 正向路径可从当前 task state 生成与现有服务等价的 delivery/CI/accept/rework 输入，调用者不再手填重复机器事实。
- absolute policy path、简写 repository、错误 delivery head、PR/head drift、多 PR、review mismatch、缺 check、bundle/result/evidence drift 均在任何写入前 fail-closed。
- legacy delivery/accept/rework records 仍可读；candidate/public CLI 的越权路径保持拒绝。
- Python 3.9.6 与 3.14.6 的默认 verifier、P3 focused contracts、bundle/project verify、fixed-head CI 与独立 acceptance 通过。
