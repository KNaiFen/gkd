# GKD-GATE-REPAIR-R3 Acceptance

## Outcome

Blocked before implementation. Candidate block head `3b48fca22b452b577eb1009f0049b19f3edc7c06`，revision 6；未创建 PR、未交付、未验收或合并。

## Evidence

- executor 在 clean candidate、claim head `0e55318ef26288d98ed10df64ad9efb4fbf2c3af` 上证明：若 sidecar 是 final implementation commit 的普通文件，且文件中声明该 commit 的 `implementationHead`，其字节参与 tree SHA，而 commit SHA 又包含 tree SHA，形成无法由普通 Git 提交构造的 SHA 自引用。
- R2 的 sidecar 后置独立提交可规避自引用，却被旧 acceptance 的 direct-parent `implementationHead` hard gate 拒绝；两条冻结条件不能同时满足。
- trusted main 使用 canonical `gkd-task block` 写入 reason `sidecar-self-referential-implementation-head`，没有手改 coordination state。

## Boundary

后续 R4 必须从 existing delivery `implementationHead` 与 fixed tree 推导 sidecar 位置，不让 sidecar 自报该 SHA。生产、AIO、GitHub settings/Secrets、runner、tag/Release 均未修改。

