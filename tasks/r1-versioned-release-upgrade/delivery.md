# GKD-R1 交付

## 结果

- Outcome: `release_upgrade_candidate_ready`
- Fixed base: `2d848db56aad86ece5daba281b7f857c6c1f82c6`
- Bootstrap planning/authorized head: `03726a821ad51989fde7f219d376b4e3308c7ffc`
- Implementation/evidence commit: `a73c4e7417a6d3fffabade0ddebc87ad0c49f502`
- Candidate version/bundle: `0.1.2` /
  `167be7a7c900788dbac78df0c7989310fedee6e2c97d311c068615d3127b6170`
- Evidence digest/file SHA-256: `969e1759813ddb95b475c477cc6a340eae7d1c9aa530141cf11cc7cb1f3a22b3` /
  `0e4d949c01ee67ccf7232b6a9ff4c47855a5036a51af9ac5d47b90e6fe0a678e`

## Bootstrap Exception

R1 将 current canonical source 从已发布 `0.1.1` 升级为 `0.1.2`，但 project staging
仍精确绑定旧 bundle，不能把旧执行环境伪装为本次 release 的 automatic claim。任务因此
保持 `planning`，没有 claim、activation、receipt 或 task delivery machine state；本
session 没有调用 `gkd-task claim`、`gkd-task deliver`、公开 automatic CLI 或私有 host
接口。

## 实现

- release candidate 只接受稳定的 `major.minor.patch`；拒绝缩短、前导零、pre-release、
  `v` 前缀和空版本。
- promotion 从完整性验证后的 candidate record 派生 `v<version>`，不再重用旧 `v0.1.1`
  literal。L1 property 同时证明 `0.1.1` legacy 与 `0.1.2` fresh record 的 exact tag。
- canonical `source.toml`、README、manifest/lock 与安装契约升级到 `0.1.2`，其中
  manifest/installer tests 读取 source declaration 而不再自行写死发布版本。
- 新增 positive/negative/mutation release coverage，并把 focused evidence 标识更新为
  `GKD-R1`；未修改 automatic bridge、release layers、production migration 或 AIO。

## 验证

已按 `gkd-local-verify` 运行唯一版本化 verifier：

`PYTHONDONTWRITEBYTECODE=1 PATH=/opt/homebrew/bin:$PATH scripts/gkd-verify --base-sha 2d848db56aad86ece5daba281b7f857c6c1f82c6`

终态 `pass`，共 `419/419`：release candidate 15、foundation 53、M3 CI 29、resource 14、
review 11、M4 9、P1 6、role-routing 71、runtime-bridge 35、task-core 129、watcher 47。

release evidence 在两个不相交的临时根各运行 15/15，输出逐字节一致。candidate bundle
在独立临时根 install/verify 为 `0.1.2`、103 files 和上述 digest；所有临时根已清理。
未安装依赖，没有 tag、Release、production、AIO、sandbox、GitHub 设置、Secrets 或付费
runner 写入。

## 停止边界

本文件单独提交后，candidate 停在 trusted-main independent acceptance 前。无阻塞 review、
fixed-head CI 与 exact merge 后，trusted main 才能启动单独的 post-merge L3/L4 release
gate、promotion 和 isolated project restage；AIO adoption 仍需使用发布后的 exact bundle。
