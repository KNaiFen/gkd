# GKD R8 验收适配器交付

## 结果

- Outcome: `github_acceptance_adapter_ready`
- Fixed base: `4c5be63aedb724de01103dd63d34bec3aea74944`
- Claim base head: `87bfda9e9ec31de1c6572c1e394f04f7f617002a`
- Claim: `2d08663c7038a7269282876e62465460119ac62d882e9703924931490bfd0601`
- Implementation commit: `44008791ae7397635a3048671f0fea156578364a`
- Accepted execution bundle: `cdaa791ace82a5e7c407b29a93a4211b852d7f364900bbcd8a549dbe918bf2a7`
- Candidate output bundle: `8a5c14bd4f4ddcc5b72190cd712bb60930f4252391619726725da32f3ae7ef8d`

本交付只实现 GitHub-only acceptance adapter、fake-gh 合同、executor delivery
CAS 指引、manifest/lock 和最小 acceptor 文档。没有修改 task lifecycle、route、claim、
bridge、历史 receipt、AIO、production、workflow/settings、tag 或 Release。

## 实现

- 新增安装态 `gkd-github-accept`。它只接受 canonical JSON request，通过 GitHub REST
  `gh api` 读取 pull request 与 check-runs，并输出 task core 所需的 canonical snapshot。
  REST `merged: true` 映射为 `state: merged`，并把原 PR head 作为 `mergedHead`。
- merge 使用单一 REST `PUT`，固定 `merge_method=squash` 与 request 的 exact head。`gh`
  exit `75` 原样传递给既有 reconciliation；非零响应和 stderr 不回显。
- `gkd-execute` 明确固定顺序：implementation commit、只含 `delivery.md` 的 document
  commit、以该 document commit full SHA 为 `gkd-task deliver --expected-head`，最后由 CLI
  创建唯一 coordination commit。`gkd-accept` 只允许安装态 adapter。

## 验证

唯一版本化 verifier：

```text
PYTHONDONTWRITEBYTECODE=1 python3.14 -B scripts/gkd-verify --base-sha 4c5be63aedb724de01103dd63d34bec3aea74944
```

终态为 `pass`，11 个 scope 共 `434` 项：release candidate `15`、finalization `9`、CI
policy `29`、resource scanner `19`、review core `11`、task core `135`、role routing `71`、
runtime bridge `39`、production migration `6`、foundation `53`、watcher `47`。未安装依赖，
未运行真实 GitHub merge、live gate、大型构建或 cache。

新增 fake-gh 合同覆盖 canonical newline、REST merged state、exact-head squash merge、
exit `75` reconciliation 和 credential-shaped stderr 不回显；foundation install/manifest
contracts 共同验证新 adapter 处于 installable candidate bundle。

## 停止边界

本文件必须单独提交。随后 executor 仅以该 document commit 的完整 SHA 调用
`gkd-task deliver`；CLI 生成 final task-state commit 后，executor 推送 PR、固定 head CI
并停止。不验收、不合并、不归档、不清理、不启动其他任务，也不修改 production、AIO、
workflow/settings、tag 或 Release。
