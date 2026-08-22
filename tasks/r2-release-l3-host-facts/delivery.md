# GKD-R2 交付

## 结果

- Outcome: `trusted_main_l3_candidate_ready`
- Fixed base: `d5f1eef459eb1598e48c9d61135d9ec7a6b10e48`
- Bootstrap planning/authorized head: `16be26b51d211077daeb6016f8170b48a6d532b4`
- Implementation/evidence commit: `c478d81985689920b8fe0f6c2d7c9d47afbb10be`
- Candidate version/bundle: `0.1.2` /
  `83b0063fe1f59fa6843acbaa26f70de9e02a47430c1f6bc3a72a4d0204dffc28`
- Evidence digest/file SHA-256: `c0c9fc30cf7cde103159f8d1fa07e5dc6d16658d50985b9f8ceaf2cf10ef3396` /
  `b6bcedf626c265f8d00fc57a772d3860a05aef87c079a7100eb95fe48bc25d1a`

## Bootstrap Exception

当前已安装/staged bundle 仍是已发布 `0.1.1`，不能把旧执行环境伪装为正在修复的
`0.1.2` automatic claim。本任务保持 `planning`，没有 claim、activation、receipt 或
task delivery machine state；没有调用 `gkd-task claim`、`gkd-task deliver`、公开
automatic CLI 或私有 host bridge。

## 实现

- L3 由 schema v2 的 fresh-executor 轨迹替换为 schema v3 的
  `trusted-main-post-merge-release-gate` 观察记录。
- 新记录只绑定经过验证的 release candidate 的 source SHA、candidate record digest、
  traceability digest 与固定 no-write boundary；没有 executor role、child lifecycle、
  raw agent/thread/session、prompt 或 effective runtime 字段。
- post-merge final record 使用 `l3TrustedMainEvaluation`，在 L4 和 asset provenance
  之前重新绑定同一 release candidate；source、candidate 或 traceability 替换均终止。
- L4 marker/check、semantic-version、资产格式、automatic bridge、production migration
  与 AIO 均未改动。旧 fixture 不再作为新记录的兼容入口。

## 验证

已按 `gkd-local-verify` 运行：

`scripts/gkd-verify --base-sha d5f1eef459eb1598e48c9d61135d9ec7a6b10e48`

终态为 `pass`，共 `419/419`：release candidate 15、foundation 53、M3 CI 29、resource
14、review 11、M4 9、P1 6、role-routing 71、runtime-bridge 35、task-core 129、watcher
47。release evidence 在两个不相交临时根各运行 15/15，输出逐字节一致；候选在独立临时
根 install/verify 为 `0.1.2`、103 files 和上述 digest。

没有安装依赖，也没有 tag、Release、production、AIO、sandbox、GitHub settings、Secrets
或付费 runner 写入。

## 停止边界

本文件单独提交后，candidate 停在 trusted-main independent acceptance 前。只有无阻塞
review、policy-backed fixed-head CI 和 exact merge 都完成后，trusted main 才可用新 L3
合同执行一次 post-merge L3/L4、promotion 和隔离 project restage；AIO adoption 继续等待
已发布且已 restage 的 exact bundle。
