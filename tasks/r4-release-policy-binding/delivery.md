# GKD-R4 交付

## 结果

- Outcome: `policy_binding_release_candidate_ready`
- Fixed base: `3133e35df8dd520e2976116e6468761eef6d84df`
- Bootstrap planning/authorized head: `59b7adee9c1219c860f45bb28895aed157c5da4e`
- Implementation/evidence commit: `987a6025d6df5a3d9df3003822a134f93b1f4a5e`
- Candidate version/bundle: `0.1.3` /
  `cc465d26f08edb2a133775e4d6a58aa517eab1bde0ec2e1ec72f6d9f2c8883bd`
- Evidence digest/file SHA-256: `306b5d979b3c202352212b6852809457df1cff3694c22a15a2279c4237af0a1b` /
  `782d743beb0494ecb033fbc9f406f7c5fb64340d0a63838e4c636ad25f3926de`

## Bootstrap Exception

当前已发布 `v0.1.2` runtime 早于 R3 的 policy-bound task state，不能被伪装成
`0.1.3` automatic claim。本任务保持 `planning`，没有 claim、activation、receipt 或
machine delivery state；没有调用 `gkd-task claim`、`gkd-task deliver`、公开 automatic
CLI 或私有 host bridge。

## 实现

- canonical version 从 `0.1.2` 升级为 `0.1.3`，并由生成器重建 manifest 与 lock。
- release L1 property 同时验证历史 `0.1.1`、`0.1.2` 与候选 `0.1.3` 的精确 tag
  propagation；新 candidate fixture/evidence 标识为 `GKD-R4`。
- R3 的 policy/origin 绑定、automatic bridge、route gates、release protocol、生产与
  AIO 都没有改变。

## 验证

已按 `gkd-local-verify` 运行：

`scripts/gkd-verify --base-sha 3133e35df8dd520e2976116e6468761eef6d84df`

终态为 `pass`，共 `424/424`。release contracts 在两个不相交临时根各运行 `15/15`，
输出逐字节一致；候选在独立临时根 install/verify 为 `0.1.3`、103 files 和上述 digest。

没有安装依赖，也没有 tag、Release、production、AIO、sandbox、GitHub settings、Secrets
或付费 runner 写入。

## 停止边界

本文件单独提交后，candidate 停在 trusted-main independent acceptance 前。只有无阻塞
review、policy-backed fixed-head CI 和 exact merge 都完成后，trusted main 才可运行既有
post-merge L3/L4、promotion 和 isolated project restage；AIO adoption 继续等待已发布且已
restage 的 exact bundle。
