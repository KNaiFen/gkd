# GKD-R5 Runner Resource Fact Binding 交付

## 结果

- Outcome: `runner_resource_binding_ready`
- Fixed base: `e734c1e0d5498d786e4055ac6eb05232f7e3336c`
- Claim base head: `d70195e286eab2e2cc73fc75a517b8e64906d517`
- Claim: `b94a561be8d4e7e0ef491060579e55ca505685926197dd789eebf224ce55506d`
- Implementation/evidence commit: `81c71024c3cae062fb09746b5b374919133dd36c`
- PR: [KNaiFen/gkd#29](https://github.com/KNaiFen/gkd/pull/29)

本交付只修复 recommendation 将 host、observed 或 unknown 资源数值外推为
GitHub runner 容量的缺口。没有修改 artifact class、scanner、billing schema、GitHub
workflow、role、task bridge、AIO 或生产安装。

## 实现

- 非保守 preset 只接受 `source=runner`、完整且已验证的资源事实，并且只能选用当前
  已验证 runner 声明、且确实被这些资源支持的容量。
- `speed-first` 不再从资源数值推测更高的云端 runner；`balanced` 同样只有在当前
  runner-bound 容量支持时才使用 `standard`。
- recommendation 不再声明选择未提供的高容量、标准或低价 runner。它只保留当前已验证
  runner；当前 runner 未验证时明确要求先验证。
- 新增 host、observed、unknown、runner-bound 容量不匹配和无候选 runner 的正反例，
  并添加 source gate 与容量绑定的 mutation contracts。

## 摘要与证据

- Accepted execution bundle: `cc465d26f08edb2a133775e4d6a58aa517eab1bde0ec2e1ec72f6d9f2c8883bd`
- Candidate output bundle: `7a5a00078b0624a213f3064ea13385f571b1c493c5ddc3c10250aabb33207cea`
- Resource-layer evidence digest: `7f68fcc533f74f91bc6788072529a59d58ffb36c57aa802cbc4640af5cee0e4b`
- Evidence file SHA-256: `d5d227e7f2c1bdf4b5975553bbeb6ab2994e9f52da56b9413e167680ee3ba104`
- Evidence: `evidence/r5-runner-resource-binding/resource-layer-contracts.json`

两次独立 resource-layer contract 运行均为 19 项通过，输出逐字节一致。该证据只绑定
canonical candidate bundle、测试标识和结果，不包含能力、运行时身份、prompt、transcript、
凭据或机器路径。

## 验证

唯一版本化 verifier：

```text
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 scripts/gkd-verify --base-sha e734c1e0d5498d786e4055ac6eb05232f7e3336c
```

终态为 `pass`，11 个 scope 共 429 项：release candidate 15、finalization 9、CI policy
29、resource scanner 19、review core 11、task core 130、role routing 71、runtime bridge
39、production migration 6、foundation 53、watcher 47。未安装依赖、未运行 live gate、
未修改 runner、GitHub settings、生产安装或 AIO。

## 停止边界

本文件单独提交后，executor 只调用 `gkd-task deliver` 绑定该文档与 candidate output
bundle。终态协调提交会成为唯一后续提交；executor 停在固定 head，不验收、不合并、不归档、
不清理 worktree 或分支、不启动其他任务，也不创建 tag、Release、runner、Secrets、生产或
AIO 变更。
