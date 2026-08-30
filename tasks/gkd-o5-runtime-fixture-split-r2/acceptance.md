# GKD O5 Runtime Fixture Split R2 Acceptance

## 固定 Head

- PR: `#49`
- Candidate fixed head: `fcef63b4d75b39932fcb02bb83560def3c426056`
- Canonical merge: `03524c0070bb3b13b5417239cdad37b21922c278`
- Review digest: `9b94bf3c404bb2baf8be905f110cc9f8af600321cc8e56d136c2fb2a13f2ee5b`
- Reviewer digest: `8a62a3768bb48bf71653081e1761f405a63f061c64a4e6451816e702e0c136bb`

## 结果

独立验收通过。Python 3.9.6 与 Python 3.14.6 均在固定 head 运行 default/core 的 10 个 scope、405 项 verifier；相对 `.gkd/policy.json` 的 `GKD Verify` 成功，candidate tree 与 squash merge tree 均为 `5eb721ce350872723be6781e2a9ad8a9eca207a7`。

四个 finalization、release traceability、trusted-main evaluation 和 multi-repository 输入以 R100、字节不变方式迁移到 `canonical/inputs`。source declaration 与 lock 绑定 name、kind、path、mode、size 和 SHA-256；`gkd-bundle verify-input` 对显式输入执行验证，不回退到安装路径。core payload 为 107 个文件，含 metadata 的安装面为 111 个文件，且不存在 `gkd/fixtures`。candidate bundle digest 为 `b7f1d783cf01cdcecfb12f98ce426877aec99b7b4647dacc542fdae8cc053d02`。

首次 acceptor 已完成无 finding review 与本地验证，但因使用绝对 policy path 得到唯一终态 `POLICY_PATH_UNSUPPORTED`，未调用 acceptance 或 merge。该 attempt 未重试；全新 acceptor 使用相对 policy path 后完成固定 head CI、独立审查和受信 review。trusted main 随后通过 canonical `gkd-task accept --merge` 接受并合并。

## 范围边界

未进行生产安装、AIO、GitHub settings/Secrets、runner、tag、Release 或已发布资产变更。
