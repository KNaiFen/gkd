# GKD O4 Lane Manifest Compatibility R3 Acceptance

## 固定 Head

- PR: `#47`
- Epoch 0 rejected head: `6f371797d0edd4399618accecc799b0604770c5b`
- Epoch 1 accepted head: `f95b43868ca3a3d87fe4104cdee0f6da6754780f`
- Canonical merge: `aeeeb2b57fc98289e341f4b04790b7cf34d78ee3`
- Review digest: `cf763db5c1bcf91bf45e8e7bd617d21b086cd822dfff2ada5de7658411f0320d`

## 结果

Epoch 0 的独立验收把绝对 policy 路径传给 fixed-head monitor，唯一终态为 `POLICY_PATH_UNSUPPORTED`；该 attempt 未调用 accept/merge，并由 canonical rework 退役。

Epoch 1 独立验收通过。相对 `.gkd/policy.json` 的 `GKD Verify` 在精确 head 成功，系统 Python 3.9.6 与开发 Python 3.14.6 均完成 450 项完整 verifier；candidate bundle `04efd9ce5f1e0f678f9853eef5d9fb20606fff6e667aba69d9b204bddeb9b5d6` 通过 accepted execution bundle 复核。trusted main 随后以 canonical `gkd-task accept --merge` 完成合并。

验收确认 schema v2 manifest 严格绑定已知 `default/core` 与 `historical/watcher` profile 的完整、无重复 scope；delivery、acceptance 与 rework 共享 fixed-tree validator，并保留 legacy schema v1 strict path。

## 范围边界

未进行生产安装、AIO、GitHub settings/Secrets、runner、tag、Release 或已发布资产变更。
