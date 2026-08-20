# GKD-M2-J 交付

## 结果

- Outcome: `delivery_document_contract_ready`
- Fixed base: `6b5d5b78a3c5f5cc98d0659167b5d3838d14f518`
- Claim head: `ea8ad0e456c2f7b226efbe6b37b5f43aec342465`
- Implementation commit: `a2beb50c511ef6651de15cb4448849db0994b4d3`
- Evidence commit: `1888d22`
- PR: `KNaiFen/gkd#15`, task branch `task/m2-delivery-document-contract`
- Candidate output bundle: `d17c5f5259591ab1dbd0b1148786fc5126dc858bdf577172c0df7c2a29f1c95b`
- Evidence digest: `1a3fa445caf6b335fda5164091b2ad5a57671d0ddca9c1ca97f188ebff171ad1`

本任务只修复 generic delivery-document sequencing 和 fixed-head acceptance 合同，
未修改 M2-I、M3-A/B/C、生产 `~/.codex`、AIO、Secrets、runner、GitHub settings、
tag 或 Release。

## 合同

- `gkd-task deliver` 要求先提交唯一的 `tasks/m2-delivery-document-contract/delivery.md`，
  再传入其 path 和 content digest。
- delivery state 绑定 `implementationHead`、`deliveryDocumentCommit`、
  `deliveryDocumentPath` 和 `deliveryDocumentDigest`。
- trusted acceptance 验证 implementation -> delivery document -> final state 的精确父链；
  delivery document commit 只能包含该文档，final state commit 只能包含 `task.json`。
- legacy v1/v2 delivery state 仍可读取，但没有 additive document binding 时明确拒绝 acceptance。
- candidate-facing CLI 不能 accept 或 merge；只有 trusted `gkd-task accept` 可执行 acceptance。

## 验证

`PATH=/opt/homebrew/bin:$PATH scripts/gkd-verify --base-sha
6b5d5b78a3c5f5cc98d0659167b5d3838d14f518` passed:

| Contract | Result |
| --- | ---: |
| Task core | 126/126 |
| Runtime bridge | 32/32 |
| Role routing | 70/70 |
| Foundation | 53/53 |
| Watchdog core | 47/47 |
| Watchdog live-negative | 15/15 |
| M2-J focused contracts | 9/9 |
| M2-J deterministic evidence | 2/2, byte-identical |

No dependencies were installed. CI monitor result remains
`CI_POLICY_UNAVAILABLE_MILESTONE_3`; this session did not query or rerun CI.

## 停止边界

This document is committed before `gkd-task deliver`. The following delivery state
commit is the only coordination commit after this document and is the fixed candidate
head. This executor stops before independent acceptance, merge, archive, cleanup, M3
start, production installation or AIO modification.
